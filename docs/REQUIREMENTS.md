# Requirements

## 1. Product summary

Users upload a lecture video, or paste a link to one, choose a target language,
and receive a dubbed video in which the speaker's voice is preserved, the speech
is translated into clear and natural spoken sentences suited to explaining
complex ideas, and the original video is re-published with the new audio.

**Scope decision:** lip-sync of the speaker's mouth is a planned later milestone and is **not part of v1**.

Reference experience: YouTube auto dubbing.

## 2. Hard constraints (from the product owner)

| # | Constraint |
|---|---|
| C1 | Commercial product: every model, library and dataset must allow commercial use |
| C2 | All AI inference runs locally. No hosted LLM, TTS, ASR or lip-sync APIs |
| C3 | Hardware: Windows PC, one NVIDIA GPU, 4 GB+ VRAM |
| C4 | Source language: any (auto-detected) |
| C5 | Target languages in v1: English and Urdu |
| C6 | Typical input: 30 to 60 minute lectures |
| C7 | Stack: Python (FastAPI) backend, Next.js (React) frontend |

## 3. Functional requirements (v1)

**Accounts**
- FR-1 Sign up, log in, log out. Passwords hashed (argon2 or bcrypt).
- FR-2 Each user sees only their own jobs and files.
- FR-3 Usage is recorded per user (minutes processed per job) to allow credits and payments later.

**Input**
- FR-4 Upload a video file (mp4, mov, mkv, webm) with chunked, resumable upload and a progress bar.
- FR-5 Paste a direct file URL (public .mp4 and similar, Google Drive or Dropbox share links) and have the server fetch it.
- FR-6 Paste a YouTube URL and have the server fetch it (yt-dlp), but only after the user ticks a checkbox confirming they own the video or have permission to dub it. The confirmation is stored with timestamp, user id and URL.
- FR-7 Validate every input with ffprobe. Enforce limits for size and duration (configurable).

**Job options**
- FR-8 Choose target language: English or Urdu. Source language is auto-detected and shown to the user, who may override it.
- FR-9 Toggle "keep the speaker's voice" (voice cloning). Requires a consent checkbox: the user confirms they have the speaker's permission.
- FR-10 *(deferred)* Lip-sync toggle: not in v1. Leave room in the options model, but do not build it.

**Processing**
- FR-11 Transcribe with word-level timestamps, detect language.
- FR-12 Translate into natural spoken sentences, consistent terminology, length-aware.
- FR-13 **Review step:** after translation the job pauses in `awaiting_review`. The user can read and edit translated segments side by side with the original, then approve. Voice generation starts only after approval. (The user may also choose "skip review".)
- FR-14 Generate target-language speech in the speaker's voice, fit to the original timing.
- FR-15 Keep background sound (music, room tone) by separating and re-mixing it.
- FR-16 *(deferred)* Lip-sync on face-visible shots. Not in v1.
- FR-17 Replace the original audio track with the dubbed mix and write a final MP4 (video stream copied without re-encoding where possible).

**Output**
- FR-18 Live job progress (stage name and percentage).
- FR-19 Preview the result in the browser and download the MP4.
- FR-20 Jobs can be cancelled and deleted. Files are deleted after the retention period.

**Compliance**
- FR-21 Output is labeled as AI-dubbed (metadata and an on-page notice).
- FR-22 Terms page, privacy page, and a takedown / contact page.

## 4. Non-functional requirements

- NFR-1 Resumable: a crash or restart resumes at the failed stage.
- NFR-2 One GPU job at a time on the 8 GB card; the queue handles waiting jobs fairly.
- NFR-3 Large files never pass through the API process in memory.
- NFR-4 Urdu text displays correctly (right-to-left, proper Urdu font) everywhere in the UI.
- NFR-5 Clear error messages for users; detailed logs for the developer.
- NFR-6 Everything installable on Windows with documented steps.

## 5. Out of scope for v1 (planned later)

**Lip-sync (next milestone)**, subtitle export (SRT/VTT), payments and credits, multi-speaker dubbing with
diarization, more target languages, cloud GPU workers, Postgres and S3-compatible
storage, team workspaces, API for third parties.

## 6. Assumptions & Architectural Baseline

- A1 v1 assumes **one main speaker** per video. Multi-speaker is a later phase.
- A2 Default limits: 4 GB per file, 90 minutes per video, 14-day retention.
- A3 Processing is **asynchronous and slow** on 8 GB. The UI must set that expectation (queue position, estimated time once benchmarked).
- A4 v1 keeps the original video unchanged and replaces only the audio. When lip-sync is added later it will run only on face-visible shots.
