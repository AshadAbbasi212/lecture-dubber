# Architecture

## 1. Overview

```
Browser (Next.js)
   │  REST + Server-Sent Events
   ▼
FastAPI app ───────────► SQLite (dev) / Postgres (later)
   │  creates job rows        users, jobs, segments, artifacts,
   │                          attestations, audit_log, usage_records
   ▼
Local storage (storage/)  ◄──── CPU/GPU worker process (one GPU job at a time)
   uploads, artifacts,           polls the DB for the next runnable job,
   outputs                       runs stages, writes artifacts + progress
                                     │
                                     ▼
                         Model runners (subprocess per model, own venv)
                         ASR · separation · translation · TTS · voice
                         conversion · face tracking · lip-sync
```

**Why a DB-backed queue instead of Redis/Celery:** the target is a single Windows
PC with one GPU. Redis is awkward on Windows, and a polling worker plus a `jobs`
table is simple, debuggable and survives restarts. Put the queue behind a small
interface so Celery/Temporal can replace it when moving to cloud GPUs.

## 2. Components

**Frontend (Next.js, TypeScript, Tailwind)**
Pages: register, login, dashboard (job list), new job (upload or link, options,
consent checkboxes), job detail (progress, review editor, preview, download),
terms, privacy, takedown. The review editor shows original and translated
segments side by side; Urdu text uses `dir="rtl"` and an Urdu-capable font
(for example Noto Nastaliq Urdu or Noto Naskh Arabic).

**API (FastAPI)**
Auth, uploads, job CRUD, segments editing, approval, download, SSE progress.
Never loads models. Never holds a whole video in memory.

**Worker**
A separate Python process. Picks the oldest runnable job, executes the next
stage, updates progress, and repeats. Holds a GPU lock: only one GPU stage runs
at a time.

**Model runners**
Each heavy model is wrapped by a small CLI or module in `backend/app/engines/`
and executed as a **subprocess** inside its own venv under `models/<name>/`.
Reasons: lip-sync and TTS repos pin conflicting torch / numpy versions, and a
subprocess exit reliably frees VRAM.

**Storage**
Local filesystem behind a `Storage` interface (`put`, `get`, `exists`, `signed_url`,
`delete`). Layout:

```
storage/
  uploads/<upload_id>/            chunks, then the assembled source file
  jobs/<job_id>/
    source.mp4
    audio/original.wav, vocals.wav, background.wav
    transcript.json
    translation.json
    tts/seg_0001.wav ...
    dub_vocals.wav, dub_mix.wav
    video/shots/..., lipsynced/...
    output/final.mp4
```

## 3. Data model (core)

- `users(id, email, password_hash, created_at)`
- `jobs(id, user_id, status, stage, progress, source_type, source_ref, source_lang, target_lang, options_json, error, created_at, updated_at, expires_at)`
- `segments(id, job_id, idx, start, end, speaker, src_text, tgt_text, edited_by_user, tts_path, tts_duration, stretch_ratio)`
- `artifacts(id, job_id, kind, path, stage, created_at)`
- `attestations(id, user_id, job_id, kind, url, text, created_at)`  (ownership + voice consent)
- `usage_records(id, user_id, job_id, media_seconds, created_at)`
- `audit_log(id, user_id, action, detail, created_at)`

## 4. Job state machine

```
queued → ingesting → extracting → separating → transcribing → translating
       → awaiting_review → synthesizing → mixing → muxing → completed
       (reserved for the later lip-sync milestone: mixing → lipsyncing → muxing)
any state → failed | canceled
```

Rules: transitions are validated in code; each stage checks for existing
artifacts and skips if present; `awaiting_review` waits for `POST .../approve`
(or is skipped when the user chose "skip review"); retry resumes at the failed stage.

## 5. API sketch

```
POST   /api/auth/register | /api/auth/login | /api/auth/logout      GET /api/me
POST   /api/uploads                 start resumable upload (returns upload_id)
PATCH  /api/uploads/{id}            send a chunk (offset in header)
POST   /api/uploads/{id}/complete
POST   /api/jobs                    {upload_id | url, target_lang, source_lang?,
                                     clone_voice, skip_review,
                                     ownership_confirmed?, voice_consent?}
GET    /api/jobs                    list mine
GET    /api/jobs/{id}               status, stage, progress, options
GET    /api/jobs/{id}/events        SSE progress stream
GET    /api/jobs/{id}/segments      PUT /api/jobs/{id}/segments  (edit translations)
POST   /api/jobs/{id}/approve       resume after review
POST   /api/jobs/{id}/cancel        DELETE /api/jobs/{id}
GET    /api/jobs/{id}/download?kind=video|audio    signed, short-lived
GET    /api/health
```

(The agent may choose the tus protocol or a custom chunk protocol for uploads.)

## 6. Security

- URL import: allow only http/https; resolve DNS and **reject private, loopback and link-local addresses**; re-check after every redirect; cap redirects, size and time; run YouTube downloads in the worker, not the API.
- Validate media with ffprobe; reject unexpected streams or absurd dimensions.
- Passwords hashed; JWT or session cookies with CSRF protection; rate-limit auth and job creation.
- Authorization check on every job, segment and download request.
- Signed, expiring download URLs; no directory listing; no user-controlled paths.
- Secrets only in `.env`.

## 7. Future-proofing (do not build in v1, but do not block)

Credits and Stripe via `usage_records`; Postgres; S3-compatible storage; remote
GPU workers using the same job interface; additional target languages through
the engine interfaces.
