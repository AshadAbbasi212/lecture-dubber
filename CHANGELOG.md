# Changelog

All notable changes to the Lecture Dubber project will be documented in this file.

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
