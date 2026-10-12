# Build plan

> **Scope decision:** v1 is built WITHOUT lip-sync. Lip-sync is Phase 8 and starts only after the
> product owner approves. Keep the `LipSyncEngine` interface stub and a reserved `lipsyncing` state in the
> design, but do not implement or install lip-sync models in v1.

Work top to bottom. After each phase: summarize, show evidence (logs, screenshots,
test output), and wait for approval. Tick boxes as you go.

## Phase 0: Environment and research spikes (no app code yet)

- [x] 0.1 Run `scripts/check_prereqs.ps1`. Report GPU, driver, Python, Node, ffmpeg, git. Fix or document anything missing (`docs/SETUP_WINDOWS.md`).
- [x] 0.2 Create a scratch folder `spikes/` with one venv. Install CUDA-enabled PyTorch and confirm `torch.cuda.is_available()` and free VRAM.
- [x] 0.3 **ASR spike:** run faster-whisper on a 5-minute test lecture (ask the user for one, or generate a sample). Record speed, peak VRAM, language detection result, and, if Urdu audio is available, error rate.
- [x] 0.4 **Translation spike:** evaluate 2 or 3 local candidates (see MODEL_CHOICES.md) on 20 lecture sentences for English→Urdu and Urdu→English. Judge fluency, meaning, terminology, speed, VRAM. Include a length-controlled prompt test.
- [x] 0.5 **Urdu TTS spike:** search for commercially licensed local Urdu TTS and cloning or voice-conversion options. For each: license, quality sample, VRAM, speed. Recommend a design (A or B in PIPELINE.md Stage 7) for English and for Urdu.
- [x] 0.6 **English voice cloning spike:** same evaluation for English output with a 15-second reference clip.
- [x] 0.7 *(Deferred to Phase 8: skip in v1.)* Do not benchmark lip-sync now.
- [x] 0.8 **Separation spike:** Demucs (or alternative) on the test lecture. Speed and VRAM.
- [x] 0.9 Write `docs/DECISIONS.md`: one entry per stage with chosen model, version, license link, measured numbers, fallback. Flag any blocker for the user.
- [x] 0.10 **STOP.** Present results and recommended stack. Wait for approval.

Acceptance: every v1 stage (everything except lip-sync) has a chosen model with a verified commercial license, or an explicitly agreed fallback.

## Phase 1: Backend foundation

- [x] 1.1 Project structure under `backend/app/`: `api/`, `core/`, `db/`, `engines/`, `pipeline/`, `worker/`, `storage/`; tests in `backend/tests/`. Dependency management with `pyproject.toml` or pinned `requirements.txt`.
- [x] 1.2 Config from `.env`; structured logging.
- [x] 1.3 DB models and migrations (Alembic) for the data model in ARCHITECTURE.md. SQLite for dev.
- [x] 1.4 Auth: register, login, logout, `/api/me`, password hashing, rate limiting.
- [x] 1.5 Storage interface with local implementation and signed download URLs.
- [x] 1.6 Job model, state machine with validated transitions, and unit tests.
- [x] 1.7 DB-backed queue and worker process with GPU lock, graceful shutdown, and resume-on-restart.
- [x] 1.8 SSE progress endpoint.

Acceptance: a dummy pipeline with fake stages runs end to end through the worker, progress streams to a test client, and tests pass.

## Phase 2: Ingest

- [x] 2.1 Resumable chunked upload with size and type checks.
- [x] 2.2 ffprobe validation and limits (size, duration, streams).
- [x] 2.3 Direct URL import with full SSRF protection and tests (private IPs, redirects, DNS rebinding, oversize).
- [x] 2.4 Google Drive and Dropbox share-link handling.
- [x] 2.5 YouTube import via yt-dlp in the worker, gated by the ownership attestation (stored in `attestations`). Behind a feature flag.
- [x] 2.6 Retention cleanup job.

Acceptance: all three input paths produce a validated `source.mp4`; attestation rows exist; SSRF tests pass.

## Phase 3: Understand the speech (stages 2 to 6)

- [x] 3.1 Audio extraction and separation runners.
- [x] 3.2 ASR engine wrapper with language detection, word timestamps, sentence segmentation, windowed processing for long files.
- [x] 3.3 Translator interface and chosen implementation with context window, glossary, length budget, and shorter-alternative retry.
- [x] 3.4 Meaning-drift flagging.
- [x] 3.5 `awaiting_review` state, segments API (list, edit), approve, skip-review.

Acceptance: on a 30-minute test lecture the job reaches `awaiting_review` with sensible segments; edits persist; approval resumes the job.

## Phase 4: Voice (stages 7 and 8)

- [x] 4.1 Reference-clip builder.
- [x] 4.2 TTS / voice-conversion engines per Phase 0 decision, English and Urdu.
- [x] 4.3 Timing-fit algorithm with unit tests (pure Python, no GPU).
- [x] 4.4 Timeline assembly, background mixing, ducking, loudness normalisation.
- [x] 4.5 Per-segment checkpointing so a crash resumes mid-stage.

Acceptance: audio-only dub of a 30-minute lecture, in sync within a defined tolerance, background preserved, listening test notes recorded.

## Phase 5: Final video (mux)

- [x] 5.1 Replace the original audio with `dub_mix.wav`; copy the video stream without re-encoding where possible; write `final.mp4` with AI-dubbed metadata.
- [x] 5.2 Verify duration match and A/V sync; fail the job with a clear message if drift exceeds tolerance.
- [x] 5.3 Add an audio-only download option (dubbed mix as WAV or MP3).
- [x] 5.4 Produce honest time estimates from real timings of the stages (without lip-sync).
- [x] 5.5 Leave the `LipSyncEngine` interface stub and the reserved state in place (no models).

Acceptance: a 30-minute test lecture produces a final MP4 with the dubbed audio, the original video unchanged, and audio and video in sync.

## Phase 6: Frontend (Next.js)

- [x] 6.1 Project setup, API client, auth pages, protected routes.
- [x] 6.2 Dashboard with job list and status.
- [x] 6.3 New-job page: upload with progress, link input, options (no lip-sync toggle in v1), consent and ownership checkboxes, clear warnings.
- [x] 6.4 Job detail: live progress, queue position, estimates, error display, cancel and delete.
- [x] 6.5 Review editor: side-by-side segments, flagged items first, RTL Urdu support, autosave, approve button.
- [x] 6.6 Result page: in-browser preview and download.
- [x] 6.7 Terms, privacy, takedown pages (placeholder text marked for legal review).

Acceptance: a new user can sign up, upload, review, wait, preview and download without touching the API directly.

## Phase 7: Hardening and handover

- [x] 7.1 Tests: unit, API, and one end-to-end run on a short clip. CI-style script that runs them.
- [x] 7.2 Verify commercial eligibility and licensing for every model, tool, and library.
- [x] 7.3 Security review against the list in ARCHITECTURE.md section 6.
- [x] 7.4 One-command Windows setup script and a run script (API, worker, frontend).
- [x] 7.5 Operations notes: backups, disk usage, log locations, how to move to cloud GPUs.
- [x] 7.6 Update README with real status and known limitations.

## Phase 8: Lip-sync (next milestone, start only after approval)

- [ ] 8.1 Lip-sync spikes: benchmark the top 2 licensed candidates (see MODEL_CHOICES.md) on a 60-second talking-head clip on the 8 GB GPU. Record compute seconds per video second, peak VRAM, quality, failure cases. Extrapolate to a 45-minute lecture and report whether it is practical.
- [ ] 8.2 Shot detection, face detection and tracking, eligibility rules (clear, mostly frontal, large enough face).
- [ ] 8.3 Lip-sync engine wrapper with clip-level checkpoints, quality gate, and fallback to the original video.
- [ ] 8.4 Concatenate shots and mux; re-check A/V sync.
- [ ] 8.5 Add the lip-sync option to the API and the new-job page; update time estimates.

Acceptance: a 10-minute test lecture shows visible lip-sync on face shots and untouched slide shots, with a measured processing time.

## Phase 9: Later (do not start without approval)

Subtitle export (SRT/VTT), credits and Stripe, multi-speaker with diarization,
more languages, Postgres and S3-compatible storage, cloud GPU workers, admin
dashboard, public API.
