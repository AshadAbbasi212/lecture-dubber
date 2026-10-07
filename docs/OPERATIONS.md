# Lecture Dubber — Operations Runbook & Maintenance Guide

This operations manual details production management, disk cleanup, backup strategies, monitoring, and cloud GPU scaling for **Lecture Dubber**.

---

## 1. Process Architecture & Topology

```
[Browser / Client]
         │
         ▼ (Port 3000)
┌─────────────────────────────────┐
│ Next.js 16 Web Frontend         │
└─────────────────────────────────┘
         │  REST (8000) / SSE events
         ▼
┌─────────────────────────────────┐       ┌───────────────────────────────┐
│ FastAPI Application Server      │◄─────►│ SQLite Database               │
│ (backend.app.main:app)          │       │ (storage/app.db)              │
└─────────────────────────────────┘       └───────────────────────────────┘
                                                          ▲
                                                          │ Polls runnable jobs
                                                          │
┌─────────────────────────────────┐       ┌───────────────┴───────────────┐
│ Local Storage Filesystem        │◄─────►│ Background Queue Worker       │
│ storage/uploads/                │       │ (backend.app.worker.worker)   │
│ storage/jobs/<job_id>/          │       └───────────────────────────────┘
│   source.mp4                    │                       │
│   audio/original.wav, vocals... │                       ▼
│   output/final.mp4, dub_mix.wav │        ┌──────────────────────────────┐
└─────────────────────────────────┘        │ Model Engines (Subprocesses) │
                                           │ Demucs, Whisper, TTS, Muxer  │
                                           └──────────────────────────────┘
```

---

## 2. Directory Layout & Log Files

| Directory / File | Description | Retention / Management |
|---|---|---|
| `storage/app.db` | Primary SQLite database (WAL mode) containing users, jobs, segments, artifacts, attestations, and audit logs. | Critical. Back up daily. |
| `storage/uploads/<upload_id>/` | Resumable chunk upload staging area. Once complete, assembled into source video. | Auto-purged after 24h if abandoned. |
| `storage/jobs/<job_id>/` | Per-job working directory containing separated audio stems, Whisper transcripts, TTS clips, and final MP4/MP3 muxes. | Purged after `RETENTION_DAYS` (default 14 days) or on user delete. |
| `logs/api.log` | FastAPI access and error log stream. | Rotated at 50 MB, keep 5 backups. |
| `logs/worker.log` | Background worker stage transitions, model subprocess output, and VRAM stats. | Rotated at 50 MB, keep 5 backups. |

---

## 3. Routine Maintenance & Disk Usage Management

### Storage Consumption Estimates
- A standard **45-minute 1080p lecture** generates approximately **1.2 GB to 2.0 GB** of total disk data:
  - Source MP4: ~500 MB
  - Separated audio stems (vocals, accompaniment WAVs): ~450 MB
  - Segment TTS clips (100–300 small WAVs): ~250 MB
  - Final muxed MP4 + MP3 audio export: ~520 MB

### Automated Retention Cleanup
Lecture Dubber includes an automatic retention cleaner in [`backend/app/ingest/cleanup.py`](file:///c:/Users/David/Downloads/lecture-dubber-starter/lecture-dubber/backend/app/ingest/cleanup.py):
1. **Expired Jobs:** Deletes jobs and all associated disk directories whose `created_at` exceeds `RETENTION_DAYS` (default 14).
2. **Abandoned Uploads:** Removes incomplete uploads in `storage/uploads/` inactive for more than 24 hours.

#### Running Cleanup via Scheduled Task (Windows PowerShell)
To execute nightly cleanup at 3:00 AM, register a Windows Scheduled Task:
```powershell
$Action = New-ScheduledTaskAction -Execute "$PWD\.venv\Scripts\python.exe" -Argument "-c `"from backend.app.db.session import SessionLocal; from backend.app.ingest.cleanup import run_retention_cleanup; db = SessionLocal(); run_retention_cleanup(db); db.close()`"" -WorkingDirectory $PWD
$Trigger = New-ScheduledTaskTrigger -Daily -At 3am
Register-ScheduledTask -TaskName "LectureDubber-RetentionCleanup" -Action $Action -Trigger $Trigger -Description "Purges expired lecture dub storage files"
```

#### Immediate User Deletion
When a user deletes a job via the Dashboard or `DELETE /api/jobs/{id}`, the storage layer atomically unlinks the directory `storage/jobs/<job_id>` from disk and deletes the database cascade.

---

## 4. Database Backup & Disaster Recovery

SQLite supports online atomic backups while the database is actively being written:

### Creating an Online Hot Backup
```powershell
# Online backup using sqlite3 CLI
New-Item -ItemType Directory -Path "storage\backups" -Force | Out-Null
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
sqlite3 storage\app.db ".backup 'storage\backups\app_backup_$Timestamp.db'"
```

### Automated Backup Script
A backup script can be scheduled daily to retain the last 7 daily snapshots.

### Restoring from Backup
1. Stop running services: `Stop-Process -Name "python", "uvicorn", "node" -Force`
2. Rename current database: `Move-Item storage\app.db storage\app.db.corrupt`
3. Restore snapshot: `Copy-Item storage\backups\app_backup_20261007.db storage\app.db`
4. Restart services: `.\scripts\run_all.ps1`

---

## 5. Scaling to Cloud GPUs

Lecture Dubber is engineered with pluggable interfaces to facilitate straightforward migration from a single local Windows machine to cloud GPU infrastructure (RunPod, Lambda Labs, AWS EC2 G5, Modal):

```
                                 [Cloud Architecture]
                                          │
                                          ▼
                         ┌─────────────────────────────────┐
                         │ Managed PostgreSQL (RDS/Supabase│
                         └─────────────────────────────────┘
                                          ▲
                     ┌────────────────────┴────────────────────┐
                     │                                         │
                     ▼                                         ▼
        ┌─────────────────────────┐               ┌─────────────────────────┐
        │ FastAPI API Service     │               │ GPU Worker Pods (RunPod)│
        │ (Docker / ECS / K8s)    │               │ Autoscale on queue depth│
        └─────────────────────────┘               └─────────────────────────┘
                     │                                         │
                     └────────────────────┬────────────────────┘
                                          ▼
                         ┌─────────────────────────────────┐
                         │ S3-Compatible Storage           │
                         │ (AWS S3 / Cloudflare R2)        │
                         └─────────────────────────────────┘
```

### Steps to Migrate to Cloud:
1. **Database:**
   - Update `.env`: `DATABASE_URL=postgresql+psycopg://user:pass@db.host:5432/lecturedubber`
   - Run migrations: `alembic upgrade head`
2. **Storage Layer:**
   - Implement `S3Storage` against `backend/app/storage/interface.py` using `boto3`.
   - Replace local filesystem writes with presigned S3 upload/download URLs.
3. **Queue & Workers:**
   - The current DB-backed queue (`JobQueue`) works identically on Postgres with row-level locks (`SELECT ... FOR UPDATE SKIP LOCKED`).
   - Multiple GPU worker pods can run in parallel without race conditions.
4. **Model Performance Upgrades in Cloud:**
   - **ASR:** Faster-Whisper `large-v3` running on NVIDIA L4 / A10G with CUDA float16.
   - **Translation:** Run Qwen2.5-7B-Instruct via vLLM with PagedAttention for 10x higher batch throughput.
   - **Voice Synthesis:** Parallelize per-segment synthesis across worker threads.

---

## 6. Troubleshooting & Diagnostics

### Problem 1: Out of Memory (VRAM Exhaustion)
- **Symptom:** Worker logs `torch.cuda.OutOfMemoryError` during stem separation or synthesis.
- **Remedy:**
  1. The pipeline automatically frees VRAM between stages (`torch.cuda.empty_cache()` and process exit).
  2. For GPUs with <= 4 GB VRAM, ensure `.env` specifies `WHISPER_COMPUTE_TYPE=int8` (CPU execution) and Demucs uses `--segment 10`.

### Problem 2: Orphaned / Stuck Jobs After Server Reboot
- **Symptom:** Jobs remain in `running` status after machine restart.
- **Remedy:**
  - Upon worker startup, `JobQueue.recover_orphaned_jobs()` automatically identifies all jobs in `status='running'` and resets them to `queued`, resuming exactly at their checkpointed stage without re-running finished work.

### Problem 3: Audio/Video Sync Drift Error (`AVSyncDriftError`)
- **Symptom:** Job fails at Stage 9 with `Audio/video sync drift exceeds tolerance`.
- **Remedy:**
  - Check `ffprobe` on original video for variable framerate (VFR). If original video has corrupted timestamps, re-encode source video to constant framerate (`-vsync cfr`) or adjust `tolerance_seconds` in `backend/app/pipeline/video_muxer.py`.
