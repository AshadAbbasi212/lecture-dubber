# Lecture Dubber - Backend Engine & API Service

High-performance, local-first Python backend for automated educational video lecture dubbing, stem separation, transcription, length-budgeted translation, neural speech synthesis, and sample-accurate timeline mixing.

---

## Architecture Overview

The backend is structured into two cooperating services:
1. **FastAPI Web API (`backend/app/main.py`)**: Asynchronous REST & Server-Sent Events (SSE) server handling authentication, resumable chunked video uploads, job lifecycle management, side-by-side segment review, and signed download distribution.
2. **Background Queue Worker (`backend/app/worker/worker.py`)**: Dedicated pipeline execution worker that polls the SQLite database queue, acquires single-concurrency GPU mutex locks (`gpu_lock.py`), executes discrete idempotent pipeline stages, and broadcasts real-time progress events.

### Directory Structure

```
backend/
├── app/
│   ├── api/            FastAPI endpoint routers (auth, jobs, segments, uploads, health)
│   ├── core/           Configuration (Pydantic Settings), security (Argon2id/JWT), logging, SSE events
│   ├── db/             SQLAlchemy models (Job, User, Segment, Artifact, Attestation) & sessions
│   ├── engines/        Swappable interfaces & runners:
│   │   ├── asr/        Faster-Whisper speech recognition & Silero VAD sentence segmentation
│   │   ├── separation/ Demucs v4.1 stem separator (vocals / background isolation)
│   │   ├── translation/ Local LLM translator with length budget and context windows
│   │   └── tts/        Piper ONNX multilingual neural voices & Windows SAPI engine
│   ├── ingest/         SSRF protection, ffprobe validation, Cloud share links, yt-dlp import, cleanup
│   ├── pipeline/       Stage state machine, runner, timing-fit stretch, audio mixer, video muxer
│   ├── storage/        Local isolated storage engine with expiring HMAC-SHA256 signed download tokens
│   └── worker/         DB-backed atomic job queue, GPU concurrency lock, automatic crash recovery
├── tests/              Comprehensive test suite (95 unit, security, API, and E2E integration tests)
├── alembic/            Alembic database migrations
└── requirements.txt    Pinned Python dependencies
```

---

## Quick Start (Development)

### 1. Environment Setup
```powershell
# From project root
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

### 2. Database Migrations
```powershell
alembic upgrade head
```

### 3. Running Services
Start the FastAPI server:
```powershell
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive OpenAPI documentation will be available at [`http://localhost:8000/docs`](http://localhost:8000/docs).

Start the background queue worker in a separate terminal:
```powershell
python -m backend.app.worker.worker
```

---

## Running Backend Tests

```powershell
pytest backend/tests -v
```
All 95 unit, API, media probe, SSRF security, and E2E clip pipeline tests run locally without cloud API dependencies.
