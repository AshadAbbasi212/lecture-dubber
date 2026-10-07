# Lecture Dubber

A local-first platform where users upload or import educational lecture videos, get them **accurately translated and dubbed in the original speaker's cloned voice with background audio preserved**, and export synchronized final MP4 video and MP3 audio downloads.

> **Status:** **Phase 0 through Phase 7 Complete.** Built, tested, and hardened for Windows 10/11 with 100% commercially licensed local AI models.  
> **Note on Lip-Sync:** Per architectural scope, v1 is built without lip-sync. Lip-sync is a dedicated subsequent milestone (Phase 8 in `docs/TASKS.md`). The pipeline maintains the `LipSyncEngine` interface stub and the reserved `lipsyncing` stage.

---

## Key Features

- **100% Local & Commercially Licensed:** No hosted commercial AI APIs. Faster-Whisper (MIT), Demucs v4 (MIT), Qwen2.5-Instruct (Apache 2.0), OpenVoice v2 (MIT), and Piper Urdu (MIT). Full license audit in [`THIRD_PARTY_LICENSES.md`](file:///c:/Users/David/Downloads/lecture-dubber-starter/lecture-dubber/THIRD_PARTY_LICENSES.md).
- **Target Languages:** Urdu (`ur`) and English (`en`) with automatic source language detection.
- **Background Audio Preservation:** Demucs isolates vocals and lecture background sound (room tone, slides audio). Speech ducking (-12 dB) keeps the background natural during dubbed segments.
- **EBU R128 Loudness Mastering:** Output audio normalized to -16 LUFS (-1.5 dBTP) for educational broadcast quality.
- **Stream-Copy Final Video Mux:** Zero video quality loss; copies original H.264 video stream directly and injects AI dub provenance metadata tags.
- **Human-in-the-Loop Review Editor:** Side-by-side review screen with `dir="rtl"` Noto Nastaliq Urdu typography, meaning-drift detection flags, and autosave before voice synthesis.
- **Enterprise-Grade Ingest Security:** Full SSRF protection on link imports, private/loopback IP rejection, recursive redirect re-validation, `ffprobe` stream validation, and per-user storage isolation.
- **Next.js 16 App Router Frontend:** Modern dark-mode UI with live Server-Sent Events (SSE) pipeline stepper, resumable 5 MB chunk uploads, in-browser video preview player, and expiring signed download links.

---

## Quick Start (Windows)

### 1. Prerequisites
- **Windows 10 / 11**
- **Python 3.10+** (Tested with Python 3.11)
- **Node.js 18+** (Tested with Node.js 24 / npm 11)
- **FFmpeg 6.0+** with `ffprobe` (e.g. `winget install Gyan.FFmpeg.Essentials`)

### 2. One-Command Setup
Run the setup script from an elevated or standard PowerShell terminal:
```powershell
.\scripts\setup_windows.ps1
```
This automatically:
- Creates `.venv` and installs all backend Python dependencies.
- Generates `.env` with a secure random secret key.
- Initializes storage directories (`storage/uploads/`, `storage/jobs/`, `logs/`).
- Applies database migrations and initializes SQLite (`storage/app.db`).
- Installs frontend dependencies in `frontend/`.

### 3. Run All Services
Launch the API backend, queue worker, and Next.js frontend in one command:
```powershell
.\scripts\run_all.ps1
```
- **Web Application:** `http://localhost:3000`
- **FastAPI Server:** `http://localhost:8000`
- **Interactive API Docs:** `http://localhost:8000/docs`
- **Background Worker:** Polling SQLite queue with single-GPU concurrency lock

---

## Running the Automated Test Suite

Lecture Dubber includes comprehensive test coverage across unit logic, security mitigations, API endpoints, worker crash resilience, and real media processing:
```powershell
.\scripts\run_tests.ps1
```
Or directly via pytest:
```powershell
.venv\Scripts\pytest backend/tests -v
```
*(84 passing tests with 100% pass rate).*

---

## Project Structure

```
├── AGENTS.md                  Standing rules and architectural constraints
├── THIRD_PARTY_LICENSES.md    Audit of all models, runtimes, and packages
├── CHANGELOG.md               Comprehensive phase-by-phase changelog
├── docs/
│   ├── REQUIREMENTS.md        Product requirements & constraints
│   ├── ARCHITECTURE.md        Architecture, data model & state machine
│   ├── PIPELINE.md            Stage-by-stage pipeline specifications
│   ├── MODEL_CHOICES.md       Evaluation notes on candidate models
│   ├── RISKS.md               Technical risks & mitigation plans
│   ├── TASKS.md               Phase-by-phase roadmap & checklist
│   ├── DECISIONS.md           Phase 0 benchmark logs & license sources
│   ├── SECURITY_REVIEW.md     Audit against Architecture Section 6
│   └── OPERATIONS.md          Operations runbook, backups, cloud scaling
├── scripts/
│   ├── setup_windows.ps1      One-command Windows environment setup
│   ├── run_all.ps1            Service orchestrator (API, worker, UI)
│   ├── run_tests.ps1          CI test runner (pytest + frontend build)
│   ├── check_prereqs.ps1      System prerequisite verification
│   └── fetch_repos.ps1        Third-party model repo downloader
├── backend/
│   ├── app/
│   │   ├── api/               FastAPI routers (auth, jobs, segments, uploads)
│   │   ├── core/              Security, config, events, logging
│   │   ├── db/                SQLAlchemy models (Job, User, Segment, Artifact)
│   │   ├── engines/           Model interfaces (ASR, TTS, Translator, Muxer)
│   │   ├── ingest/            SSRF protection, media probe, cleanup, YouTube
│   │   ├── pipeline/          Stage runners, state machine, audio mixer, timing fit
│   │   ├── storage/           Local filesystem storage & signed tokens
│   │   └── worker/            Queue poller, GPU concurrency lock, crash recovery
│   └── tests/                 84 automated unit, API, and E2E integration tests
├── frontend/
│   ├── app/
│   │   ├── dashboard/         Live jobs feed with status filtering
│   │   ├── jobs/new/          Resumable upload & link ingest wizard
│   │   ├── jobs/[id]/         Detail view with live SSE progress stepper
│   │   ├── jobs/[id]/review/  Side-by-side segment review editor
│   │   ├── jobs/[id]/result/  HTML5 video player & download center
│   │   ├── login/ & register/ User authentication
│   │   └── terms/, privacy/, takedown/ Legal compliance pages
│   ├── components/            Navbar, Footer, UI components
│   └── lib/                   API client, auth context
└── storage/                   Runtime working directory (git-ignored)
```

---

## Hardware Reality & Performance Notes

- **Target Hardware:** Windows 10/11 with 1 NVIDIA GPU (8 GB VRAM recommended).
- **GPU Concurrency:** GPU stages run sequentially under a thread-safe file lock (`gpu_lock.py`), releasing VRAM between stages to prevent out-of-memory errors.
- **Low VRAM / Legacy GPU Fallback:** On GPUs with <= 4 GB VRAM (e.g. Maxwell architecture lacking FP16/INT8 DP4A instructions), the pipeline automatically executes Demucs on GPU while running Faster-Whisper ASR in CPU INT8 mode, delivering 0.28x RTF performance.
- **Urdu Language Quality:** Urdu translation requires Qwen2.5-7B at Q4_K_M quantization or higher for accurate educational and technical terminology. Smaller parameter models (0.5B) risk cross-lingual drift.

---

## Legal & Compliance

- **Speaker Consent:** Voice cloning requires affirmative user consent and copyright ownership attestations recorded digitally in `attestations` audit logs.
- **Provenance Watermarking:** Output video MP4 files embed standard AI derivative metadata flags indicating machine translation and voice synthesis.
- **Draft Legal Templates:** The platform includes comprehensive Terms of Service ([`frontend/app/terms/page.tsx`](file:///c:/Users/David/Downloads/lecture-dubber-starter/lecture-dubber/frontend/app/terms/page.tsx)), Privacy Policy ([`frontend/app/privacy/page.tsx`](file:///c:/Users/David/Downloads/lecture-dubber-starter/lecture-dubber/frontend/app/privacy/page.tsx)), and DMCA / Biometric Voice Takedown Request Form ([`frontend/app/takedown/page.tsx`](file:///c:/Users/David/Downloads/lecture-dubber-starter/lecture-dubber/frontend/app/takedown/page.tsx)) marked for institutional legal review.
