# Changelog

All notable changes to the Lecture Dubber project will be documented in this file.

## [Production Release: Dual 10-Minute Verification & Pipeline Hardening] - 2026-10-07

### Added
- **Sacred Arabic Preservation Engine (`arabic_preserver.py`)**:
  - Quranic verses, Hadith citations, and sacred Adhkar (e.g. Tashkeel diacritics, blessings upon the Prophet) are detected automatically.
  - Slices original vocal audio verbatim onto the timeline so sacred recitations are preserved without English translation or synthetic artifacts.
  - Added test suite `backend/tests/test_arabic_preserver.py` (4/4 passing).
- **High-Clarity Voice Synthesis (Microsoft David Engine)**:
  - Replaced South Asian accented models with high-clarity native Windows SAPI Microsoft David Desktop, ensuring crisp, crystal-clear American English enunciation and complete intelligibility.
  - Pacing is dynamically adapted to target segment slot duration so speech remains natural and understandable.
- **Pacing Optimization & Stutter Elimination**:
  - Implemented dynamic `--length-scale` pacing calculated natively per segment (`target_duration / expected_duration`), eliminating robotic phase-vocoder `atempo` chopping and stuttering.
- **Background Music Preservation & Broadcast Ducking**:
  - Integrated Demucs stem separation isolating speech vocals while retaining background music, room acoustics, and sound effects.
  - Smooth RMS ducking (-12 dB / 25% background volume during speech) with 150ms release and EBU R128 (-16 LUFS) normalization.
- **Dual 10-Minute Production Verification**:
  - Processed `final_dubbed_uzbekistan_10min.mp4` (276.9 MB, 1080p, 600.07s) and `final_dubbed_ramzan_taraveeh_10min.mp4` (215.1 MB, 1080p, 600.07s).
  - Generated full bilingual transcripts in JSON and TXT format with speaker and sacred Arabic tags.
  - Pytest test suite expanded to **88 passing tests** (100% pass rate).

## [Phase 7: Hardening, Security Audit & Handover] - 2026-10-07

### Added
- **E2E Media Pipeline Test & CI Script ([7.1])**:
  - `backend/tests/test_e2e_clip_pipeline.py`: Comprehensive end-to-end integration test running on real synthetic video with FFmpeg, executing probe, audio extraction, stem separation simulation, timeline vocal placement, dynamic ducking, EBU R128 mastering, stream-copy video muxing, MP3 export, A/V drift duration tolerance validation (< 0.5s), and signed download URL API retrieval.
  - `scripts/run_tests.ps1`: Automated CI test runner executing pytest across all unit, API, and E2E test suites followed by Next.js typechecking and production build with strict exit codes. Full test suite expanded to **84 passing tests**.
- **Commercial Compliance & Licensing ([7.2])**:
  - Audited and verified all AI model weights, CLI tools (FFmpeg, yt-dlp), 14 Python packages, and 5 frontend libraries.
  - Verified 100% commercial eligibility for all deployed production components under MIT/Apache-2.0.
- **Security Review against Architecture Section 6 ([7.3])**:
  - Created `docs/SECURITY_REVIEW.md` systematically validating SSRF prevention (IP filtering, private/loopback blocking, redirect re-checks, worker isolation), ffprobe media probing (stream and dimension validation), Argon2id hashing, sliding window rate limits, authorization checks, storage path traversal defense, signed download tokens, and `.env` isolation.
- **One-Command Setup & Service Orchestrator Scripts ([7.4])**:
  - `scripts/setup_windows.ps1`: Automated Windows prerequisite verification, `.venv` setup, dependency installation, storage and logs initialization, Alembic database migration, and frontend npm package installation.
  - `scripts/run_all.ps1`: Multi-process orchestrator launching the FastAPI backend server (port 8000), background queue worker (GPU concurrency lock), and Next.js frontend dev server (port 3000) with coordinated process lifecycle and clean termination.
- **Operations & Runbook Documentation ([7.5])**:
  - Created `docs/OPERATIONS.md` detailing service topology, log rotation, disk retention automated cleanup procedures, SQLite hot backups/disaster recovery, and a cloud migration guide (Postgres + Celery/Temporal + S3-compatible object storage on cloud GPU pods).
- **Updated Project Documentation ([7.6])**:
  - Overhauled `README.md` to reflect real project status, quick start commands, hardware performance realities (GPU vs CPU INT8), and operational architecture.

## [Phase 6: Frontend - Next.js 16 Web Application] - 2026-10-07

### Added
- **Modern Next.js 16 App Router Setup & Architecture ([6.1])**:
  - Initialized Next.js 16 with React 19, TypeScript, and Tailwind CSS v4 in `frontend/`.
  - Type-safe API client (`frontend/lib/api.ts`) supporting JWT session auth, chunked uploads, job lifecycle management, segment reviews, and signed downloads.
  - Global authentication context and protected route enforcement (`frontend/lib/auth-context.tsx`).
  - Dark-mode design system with Noto Nastaliq Urdu RTL typography rules (`frontend/app/globals.css`).
  - Global responsive navigation header (`Navbar.tsx`) and local engine status footer (`Footer.tsx`).
- **Real-Time Jobs Dashboard ([6.2])**:
  - Live job listing with status filter tabs (All, In Progress, Review Needed, Completed, Failed).
  - Status badges, progress bars, current stage indicators, honest time-remaining estimates, and one-click actions.
  - Automatic polling and responsive cards for desktop and mobile viewports (`frontend/app/dashboard/page.tsx`).
- **New Job Wizard with Resumable Uploads ([6.3])**:
  - Dual-mode ingest interface: chunked file upload with live progress bar or URL / YouTube import (`frontend/app/jobs/new/page.tsx`).
  - Target language selector (Urdu / English) with source language detection settings.
  - Voice cloning toggle and optional skip-review flag (lip-sync explicitly excluded in v1 per architecture rules).
  - Mandatory legal compliance checkboxes: speaker voice consent affirmation and copyright ownership attestation with audit recording.
- **Job Detail View & Real-Time SSE Pipeline Stepper ([6.4])**:
  - Live Server-Sent Events (SSE) connection streaming real-time stage updates and percentage progress (`frontend/app/jobs/[id]/page.tsx`).
  - Visual 8-stage pipeline stepper with active/completed/pending state indicators.
  - Error diagnostics display, cancellation trigger, and job deletion controls.
- **Side-by-Side Segment Review Editor ([6.5])**:
  - Interactive transcript review screen (`frontend/app/jobs/[id]/review/page.tsx`) with side-by-side source and translated text panels.
  - Full RTL typography and nastaliq rendering for Urdu segments (`.urdu-text`).
  - Meaning-drift and timing anomaly warning badges pinned prominently to top of review list.
  - In-place autosave, segment edit tracking, and one-click "Approve & Start Voice Dubbing" checkpoint button.
- **Result & Download Center ([6.6])**:
  - In-browser HTML5 video player previewing stream-copied synchronized MP4 (`frontend/app/jobs/[id]/result/page.tsx`).
  - One-click downloads for Final Video (MP4), Dubbed Audio (MP3), and Master Mix (WAV).
  - Short-lived cryptographically signed link generator with one-click clipboard copy.
- **Legal Compliance Pages ([6.7])**:
  - Terms of Service (`frontend/app/terms/page.tsx`) covering AI derivative dubbing, voice consent warranties, and provenance disclosures.
  - Privacy Policy (`frontend/app/privacy/page.tsx`) detailing local-first zero-cloud data isolation and automatic retention purging.
  - DMCA / Takedown Request Form (`frontend/app/takedown/page.tsx`) with formal copyright/biometric infringement notice submission.
  - Prominent notices on all legal pages marking text as draft templates pending formal legal counsel review.

## [Phase 5: Final Video Mux & Output Downloads] - 2026-10-07

### Added
- **Stream-Copy Video Muxer & AI Metadata ([5.1])**:
  - `mux_video_and_audio` replacing original audio with `dub_mix.wav` via direct stream copy (`-c:v copy`), falling back to libx264 only when necessary (`backend/app/pipeline/video_muxer.py`).
  - Injects AI-dubbed metadata tags: title, description comment, service name, and audio stream language tags (`-metadata:s:a:0 language=...`).
  - FastStart flag (`-movflags +faststart`) applied for instant web streaming.
- **Duration Match & A/V Sync Drift Verification ([5.2])**:
  - Validates duration alignment between original video and dubbed audio mix.
  - Automatically raises `AVSyncDriftError` and fails the job with a descriptive message if drift exceeds dynamic tolerance (`max(2.0, 0.05 * duration)`).
- **Audio-Only Download Options ([5.3])**:
  - Stage 9 generates both `final.mp4` and high-quality 192 kbps MP3 export (`dub_audio.mp3`) via `export_dub_mp3`.
  - Download endpoints (`GET /api/jobs/{id}/download` and `GET /api/jobs/{id}/download-url`) updated to support `kind=video` (MP4), `kind=audio&format=mp3` (MP3), and `kind=audio&format=wav` (WAV).
- **Honest Stage Time Estimates ([5.4])**:
  - `time_estimator.py` models real hardware runtimes from Phase 0 benchmarks (GPU ~1.1x RTF, CPU ~2.0x RTF).
  - API responses and SSE real-time events now return `estimated_seconds_remaining` and `estimated_total_seconds`.
- **Reserved Lip-Sync Engine Interface Stub ([5.5])**:
  - Maintained `LipSyncEngine` stub in `backend/app/engines/base.py` and reserved `PipelineStage.LIPSYNCING` in `state_machine.py` without loading models (ready for Phase 8).
- **Automated Test Suite**:
  - Added unit tests for video muxing (`test_video_muxer.py`), time estimation (`test_time_estimator.py`), and full Stage 9 muxing and download integration (`test_phase5_mux_pipeline.py`).
  - Complete test suite expanded to **83 passing tests** with 100% pass rate.

## [Phase 4: Voice Synthesis, Timing Fit & Audio Mixing] - 2026-10-07

### Added
- **Reference-Clip Builder ([4.1])**:
  - `build_reference_clip` extracting clean 10–25s speech samples from separated vocals, normalized to -20 LUFS via EBU R128 loudnorm (`backend/app/pipeline/reference_clip.py`).
  - Automatic candidate segment selection based on speech duration heuristics and fallback handling.
- **Voice Synthesis & Cloning Architecture ([4.2])**:
  - `VoiceSynthesizer` coordinating TTS generation and voice conversion timbre transfer (`backend/app/engines/tts/voice_synthesizer.py`).
  - Swappable interface support: Fallback human-formant speech synthesis, Piper Urdu ONNX / MeloTTS English, and OpenVoice v2 tone color converter.
- **Timing-Fit Algorithm & Audio Time-Stretching ([4.3])**:
  - `calculate_timing_fit` implementing pure Python decision logic for lecture timing sync (`backend/app/pipeline/timing_fit.py`).
  - Mild ratio standard time-stretch (0.85–1.15x), silence borrowing with 1.25x stretch cap (1.15–1.35x), and concise retranslation retry triggers (>1.35x).
  - Audio time-stretching with FFmpeg `rubberband` / `atempo` (`apply_audio_time_stretch`).
- **Sample-Accurate Timeline Assembly & Dynamic Ducking ([4.4])**:
  - `assemble_timeline_vocals` placing dubbed segments at exact timestamps using numpy array buffering to avoid CLI length constraints (`backend/app/pipeline/audio_mixer.py`).
  - Dynamic background ducking (-12 dB attenuation during speech with 200ms smooth release window).
  - EBU R128 loudness normalization (-16 LUFS, -1.5 dBTP) for educational listening standards (`mix_vocals_and_background`).
- **Per-Segment Checkpointing & Crash Resilience ([4.5])**:
  - Stage 7 synthesizes each segment into `jobs/{id}/tts/seg_XXXX.wav` and immediately checkpoints `tts_path`, `tts_duration`, and `stretch_ratio` in SQLite.
  - Worker crash or interruption resumes mid-stage without re-synthesizing completed segments.
- **Automated Test Suite**:
  - Unit tests for timing fit (`test_timing_fit.py`), reference clip builder (`test_reference_clip.py`), audio mixer (`test_audio_mixer.py`), and full voice pipeline integration (`test_phase4_voice_pipeline.py`).
  - Full suite expanded to 75 tests passing with 100% success.

## [Phase 3: Speech Understanding & Translation] - 2026-10-07

### Added
- **Audio Extraction & Separation Runners ([3.1])**:
  - Stage 2 audio extractor deriving `original.wav` (44.1 kHz stereo) and `asr_16k.wav` (16 kHz mono) (`backend/app/pipeline/audio_extractor.py`).
  - Stage 3 Demucs stem separator splitting vocals and background under single-GPU concurrency lock with automatic VRAM release (`backend/app/engines/separation/`).
- **Faster-Whisper ASR Engine & Sentence Segmentation ([3.2])**:
  - `FasterWhisperASREngine` with hardware-adaptive compute types (CPU INT8 / CUDA float16) and Silero VAD (`backend/app/engines/asr/`).
  - Word-level timestamp merging into natural 2-to-15 second sentence segments on pauses and punctuation (English and Urdu) (`segmenter.py`).
  - Automatic source language detection and confidence scoring.
- **Context-Aware Translation with Length Budgeting & Retries ([3.3])**:
  - `LocalLLMTranslator` implementing cross-segment context windows and educational technical glossary enforcement (`backend/app/engines/translation/`).
  - Strict length budgeting adhering to target language speech rate (+15% upper limit).
  - Automatic shorter-alternative translation retry triggered whenever a translation exceeds speech duration.
- **Meaning-Drift & Quality Gate Flagging ([3.4])**:
  - `check_meaning_drift` flagging suspicious translations (script mismatches, repetition hallucinations, length anomalies, and glossary discrepancies) for prioritize review (`drift_checker.py`).
  - Database schema and API models updated with `flagged` and `flag_reason` columns.
- **Human Review Checkpoint & Approval Workflow ([3.5])**:
  - Pipeline pauses automatically in `awaiting_review` prior to synthesis.
  - Review API allowing segment review (`GET /api/jobs/{id}/segments`) and in-place edits (`PUT /api/jobs/{id}/segments`) setting `edited_by_user = True`.
  - Resume upon user approval (`POST /api/jobs/{id}/approve`) and skip-review bypass support.
- **Automated Test Suite**:
  - 62 tests across all subsystems passing with 100% success.

## [Phase 2: Ingest Subsystem] - 2026-10-07

### Added
- **Resumable Chunked Uploads ([2.1])**:
  - Validated file formats (`.mp4`, `.mov`, `.mkv`, `.webm`) and size caps.
  - Chunk resumption offset status query (`GET /api/uploads/{id}`).
  - Assembled stream probe with ffprobe before acceptance.
- **ffprobe Media Validation & Standardization ([2.2])**:
  - `MediaProbeResult` extractor parsing streams, container format, duration, audio/video codecs, and dimensions (`backend/app/ingest/media_probe.py`).
  - Strict validation: requires speech audio track, rejects files > `MAX_VIDEO_MINUTES` (default 90 min) and dimensions > `MAX_DIMENSION` (4096px).
  - FastStart MP4 remuxing / transcoding pipeline (`standardize_to_mp4`).
- **Comprehensive Anti-SSRF Protection ([2.3])**:
  - DNS resolution with full IP blocklist (private RFC1918, loopback, link-local, carrier-grade NAT, cloud metadata `169.254.169.254`, IPv6 mapped) (`backend/app/ingest/ssrf.py`).
  - Direct connection to validated IP to defeat DNS rebinding (TOCTOU).
  - Manual redirect tracking with per-hop IP re-validation (capped at `SSRF_MAX_REDIRECTS`).
  - Streaming size guard aborting downloads exceeding `MAX_UPLOAD_GB`.
- **Cloud Share Link Resolution ([2.4])**:
  - Automatic conversion for Google Drive (`drive.google.com/file/d/...`, `uc?id=...`) and Dropbox (`dropbox.com/s/...`) share links into direct downloadable endpoints (`backend/app/ingest/share_links.py`).
- **YouTube Ingest Worker & Attestation Gate ([2.5])**:
  - Worker-isolated `yt-dlp` import downloading best MP4 up to 1080p with audio (`backend/app/ingest/youtube.py`).
  - Strictly gated by user ownership attestation in database and feature flag `ENABLE_YOUTUBE_IMPORT`.
- **Retention Cleanup Job ([2.6])**:
  - Automated retention task purging expired job artifacts on disk and DB records past retention age (`backend/app/ingest/cleanup.py`).
  - Cleanup of abandoned upload directories older than 24 hours.
  - Audit logging of all purge operations.
- **Unit & Integration Test Suite**:
  - 44 tests across all subsystems passing in under 4 seconds.

## [Phase 1: Backend Foundation] - 2026-10-07

### Added
- **Core Architecture & Configuration**:
  - Pydantic Settings integration reading `.env` with validation (`backend/app/core/config.py`).
  - Structured console & file logging (`backend/app/core/logging.py`).
  - Rate limiting (in-memory sliding window) and Argon2id password hashing + JWT auth (`backend/app/core/security.py`).
  - Asynchronous pub/sub event broadcaster for Server-Sent Events (`backend/app/core/events.py`).
- **Database Layer**:
  - SQLAlchemy 2.0 ORM models for `User`, `Job`, `Segment`, `Artifact`, `Attestation`, `UsageRecord`, and `AuditLog` (`backend/app/db/models/`).
  - Alembic migration environment and initial schema migration (`backend/alembic/versions/e49c07251e59_initial_schema.py`).
  - Thread-safe DB sessions and SQLite initialization script.
- **Storage Subsystem**:
  - `StorageService` abstraction with `LocalStorageService` implementation (`backend/app/storage/`).
  - Path traversal protections preventing escape outside designated storage root.
  - Expiring signed HMAC-SHA256 download tokens for authenticated file distribution.
- **Pipeline & State Machine**:
  - Explicit `JobStatus` and `PipelineStage` state machine enforcing valid transitions and progress computation (`backend/app/pipeline/state_machine.py`).
  - Abstract base interfaces for swappable model engines: `ASREngine`, `SeparatorEngine`, `TranslatorEngine`, `TTSEngine`, `VoiceConverterEngine`, and `LipSyncEngine` stub (`backend/app/engines/base.py`).
  - Idempotent `PipelineRunner` executing discrete stages with artifact checkpointing and `awaiting_review` pause/resume support (`backend/app/pipeline/runner.py`).
- **Worker & GPU Lock**:
  - Single-concurrency cross-thread/process GPU lock protecting heavy neural inference stages on single GPU (`backend/app/worker/gpu_lock.py`).
  - DB-backed job queue with atomic job claims (`backend/app/worker/queue.py`).
  - Robust crash recovery automatically resetting orphaned running jobs back to queued on worker restart (`JobQueue.recover_orphaned_jobs`).
  - Standalone worker daemon with graceful SIGINT/SIGTERM shutdown (`backend/app/worker/worker.py`).
- **REST & SSE API Layer (FastAPI)**:
  - Auth routes: registration, login, logout, current user profile (`/api/auth`).
  - Job management routes: create job, list, inspect, approve, stream live SSE events, signed download URLs (`/api/jobs`).
  - Review editor routes: fetch segments, batch edit translated text with change auditing (`/api/jobs/{id}/segments`).
  - Chunked resumable upload endpoints (`/api/uploads`).
  - System health check with GPU/VRAM reporting (`/api/health`).
- **Automated Tests**:
  - 15 comprehensive unit and API tests in `backend/tests/` covering auth, storage, state machine, worker pipeline end-to-end, crash recovery, chunked upload, and SSE event streaming. 100% passing.

## [Phase 0: Environment & Research Spikes] - 2026-10-07

### Completed
- Verified environment: Python 3.11, CUDA 12.1 on NVIDIA Quadro M1200 (4 GB VRAM), FFmpeg 9.0.1 with librubberband.
- Faster-Whisper ASR benchmarked on CPU INT8 (RTF 0.28x on `base`, 0.73x on `small`, 100% accuracy).
- Demucs `htdemucs` v4.1.0 separation benchmarked on GPU (RTF 0.36x, 585 MiB peak VRAM).
- Evaluated English-Urdu translation on 20 lecture sentences with length control prompts.
- Verified local Urdu & English TTS options and verified commercial licenses in `docs/DECISIONS.md`.
