import json
import asyncio
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.logging import logger
from backend.app.core.events import broadcaster
from backend.app.db.session import get_db
from backend.app.db.models.user import User
from backend.app.db.models.job import Job
from backend.app.db.models.attestation import Attestation
from backend.app.db.models.artifact import Artifact
from backend.app.pipeline.state_machine import JobStatus, PipelineStage, validate_status_transition
from backend.app.core.config import settings
from backend.app.storage.local import storage
from backend.app.api.deps import get_current_user, get_current_user_optional, check_job_create_rate_limit
from backend.app.ingest.ssrf import validate_url_security, SSRFSecurityError
from backend.app.ingest.share_links import is_share_link
from backend.app.ingest.youtube import is_youtube_url
from backend.app.ingest.cleanup import run_retention_cleanup
from backend.app.ingest.media_probe import probe_media_file
from backend.app.pipeline.time_estimator import estimate_remaining_seconds, estimate_total_pipeline_seconds

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobCreateRequest(BaseModel):
    source_type: str  # "upload", "url", "youtube"
    source_ref: str   # upload_id or URL string
    target_lang: str  # "en", "ur"
    source_lang: Optional[str] = None
    clone_voice: bool = False
    skip_review: bool = False
    enable_lipsync: bool = False  # Reserved for Phase 8 milestone
    ownership_confirmed: bool = False
    voice_consent: bool = False


class JobResponse(BaseModel):
    id: str
    status: str
    stage: str
    progress: int
    source_type: str
    source_ref: str
    source_lang: Optional[str]
    target_lang: str
    options: dict
    error: Optional[str]
    estimated_seconds_remaining: Optional[int] = None
    estimated_total_seconds: Optional[int] = None
    created_at: datetime
    updated_at: datetime


def _format_job(job: Job) -> JobResponse:
    options = json.loads(job.options_json) if job.options_json else {}
    est_rem = None
    est_total = None
    try:
        curr_stage = PipelineStage(job.stage)
        source_file = storage.get_path(f"jobs/{job.id}/source.mp4")
        v_dur = probe_media_file(source_file).duration if source_file.is_file() else 60.0
        est_total = estimate_total_pipeline_seconds(v_dur)
        if job.status == JobStatus.COMPLETED.value:
            est_rem = 0
        elif job.status in [JobStatus.FAILED.value, JobStatus.CANCELED.value]:
            est_rem = None
        else:
            est_rem = estimate_remaining_seconds(curr_stage, 0.5, v_dur)
    except Exception:
        pass

    return JobResponse(
        id=job.id,
        status=job.status,
        stage=job.stage,
        progress=job.progress,
        source_type=job.source_type,
        source_ref=job.source_ref,
        source_lang=job.source_lang,
        target_lang=job.target_lang,
        options=options,
        error=job.error,
        estimated_seconds_remaining=est_rem,
        estimated_total_seconds=est_total,
        created_at=job.created_at,
        updated_at=job.updated_at
    )



@router.post("", response_model=JobResponse, dependencies=[Depends(check_job_create_rate_limit)])
def create_job(req: JobCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if req.target_lang not in ["en", "ur"]:
        raise HTTPException(status_code=400, detail="Target language must be 'en' or 'ur'.")

    if req.source_type not in ["upload", "url", "youtube", "drive", "dropbox"]:
        raise HTTPException(status_code=400, detail=f"Unsupported source_type '{req.source_type}'.")

    # If upload, verify uploaded session exists
    if req.source_type == "upload":
        upload_path = f"uploads/{req.source_ref}/source.mp4"
        meta_path = f"uploads/{req.source_ref}/meta.json"
        if not storage.exists(upload_path) and not storage.exists(meta_path) and not storage.exists(req.source_ref):
            raise HTTPException(status_code=404, detail="Upload file not found. Complete chunk upload first.")

    # If URL, validate against SSRF
    elif req.source_type in ["url", "drive", "dropbox"]:
        if not is_share_link(req.source_ref):
            try:
                validate_url_security(req.source_ref)
            except SSRFSecurityError as e:
                raise HTTPException(status_code=400, detail=f"URL security check failed: {str(e)}")

    # If YouTube source, check feature flag, format, and ownership confirmation
    elif req.source_type == "youtube":
        if not settings.ENABLE_YOUTUBE_IMPORT:
            raise HTTPException(status_code=400, detail="YouTube import is currently disabled.")
        if not is_youtube_url(req.source_ref):
            raise HTTPException(status_code=400, detail="Invalid YouTube URL format.")
        if not req.ownership_confirmed:
            raise HTTPException(
                status_code=400,
                detail="You must confirm ownership or permission to dub YouTube videos."
            )

    # If voice cloning is requested, check consent checkbox
    if req.clone_voice and not req.voice_consent:
        raise HTTPException(
            status_code=400,
            detail="You must confirm you have the speaker's consent for voice cloning."
        )

    options_dict = {
        "clone_voice": req.clone_voice,
        "skip_review": req.skip_review,
        "enable_lipsync": req.enable_lipsync
    }

    job = Job(
        user_id=current_user.id,
        status=JobStatus.QUEUED.value,
        stage=PipelineStage.INGESTING.value,
        progress=0,
        source_type=req.source_type,
        source_ref=req.source_ref,
        source_lang=req.source_lang,
        target_lang=req.target_lang,
        options_json=json.dumps(options_dict)
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Record attestations if present
    if req.ownership_confirmed:
        att = Attestation(
            user_id=current_user.id,
            job_id=job.id,
            kind="ownership",
            url=req.source_ref if req.source_type in ["url", "youtube"] else None,
            text="User confirmed video ownership / authorization."
        )
        db.add(att)

    if req.voice_consent:
        att = Attestation(
            user_id=current_user.id,
            job_id=job.id,
            kind="voice_consent",
            text="User confirmed speaker consent for voice cloning."
        )
        db.add(att)

    db.commit()
    return _format_job(job)


@router.get("", response_model=List[JobResponse])
def list_jobs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    jobs = db.query(Job).filter(Job.user_id == current_user.id).order_by(Job.created_at.desc()).all()
    return [_format_job(j) for j in jobs]


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _format_job(job)


@router.post("/{job_id}/approve", response_model=JobResponse)
def approve_job(job_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != JobStatus.AWAITING_REVIEW.value:
        raise HTTPException(
            status_code=400,
            detail=f"Job is not awaiting review (current status: {job.status})"
        )

    validate_status_transition(job.status, JobStatus.RUNNING.value)
    job.status = JobStatus.RUNNING.value
    job.stage = PipelineStage.SYNTHESIZING.value
    db.commit()
    db.refresh(job)

    # Notify listeners via SSE
    broadcaster.broadcast_sync(job.id, {
        "job_id": job.id,
        "status": job.status,
        "stage": job.stage,
        "progress": job.progress
    })

    return _format_job(job)


@router.post("/{job_id}/cancel", response_model=JobResponse)
def cancel_job(job_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    validate_status_transition(job.status, JobStatus.CANCELED.value)
    job.status = JobStatus.CANCELED.value
    db.commit()
    db.refresh(job)

    broadcaster.broadcast_sync(job.id, {
        "job_id": job.id,
        "status": job.status,
        "stage": job.stage,
        "progress": job.progress
    })
    return _format_job(job)


@router.delete("/{job_id}")
def delete_job(job_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Clean up artifacts in storage
    artifacts = db.query(Artifact).filter(Artifact.job_id == job.id).all()
    for art in artifacts:
        storage.delete(art.path)

    db.delete(job)
    db.commit()
    return {"message": "Job deleted successfully"}


@router.get("/{job_id}/events")
async def stream_job_events(job_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Server-Sent Events (SSE) stream for real-time progress updates."""
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    queue = await broadcaster.subscribe(job_id)

    async def event_generator():
        try:
            # Yield initial status immediately
            initial_data = {
                "job_id": job.id,
                "status": job.status,
                "stage": job.stage,
                "progress": job.progress,
                "error": job.error
            }
            yield f"event: progress\ndata: {json.dumps(initial_data)}\n\n"
            if job.status in [JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELED.value]:
                return

            # Stream upcoming events
            while True:
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"event: progress\ndata: {json.dumps(data)}\n\n"
                    if data.get("status") in [JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELED.value]:
                        break
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        finally:
            await broadcaster.unsubscribe(job_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/{job_id}/download")
def download_artifact(
    job_id: str,
    kind: str = Query("video", pattern="^(video|audio|audio_mp3|audio_wav)$"),
    format: str = Query("mp3", pattern="^(mp3|wav)$"),
    token: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Downloads the output file (MP4 video, MP3 audio, or mixed WAV audio).
    Supports either authenticated user session OR a signed short-lived token.
    """
    if token:
        payload = storage.verify_signed_token(token)
        if not payload or payload.get("job_id") != job_id:
            raise HTTPException(status_code=403, detail="Invalid or expired download token")
        allowed_kinds = [kind]
        if kind in ["audio", "audio_mp3", "audio_wav"]:
            allowed_kinds.extend(["audio", "audio_mp3", "audio_wav"])
        if payload.get("kind") not in allowed_kinds:
            raise HTTPException(status_code=403, detail="Token kind mismatch")
    elif not current_user:
        raise HTTPException(status_code=401, detail="Authentication or valid token required")

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if current_user and job.user_id != current_user.id and not token:
        raise HTTPException(status_code=403, detail="Not authorized to access this job")

    if kind == "video":
        target_kind = "final_video"
        media_type = "video/mp4"
        filename = f"lecture_dub_{job.id}.mp4"
    elif kind == "audio_wav" or (kind == "audio" and format == "wav"):
        target_kind = "dub_mix"
        media_type = "audio/wav"
        filename = f"lecture_dub_{job.id}.wav"
    else:
        # Default audio is MP3, fallback to WAV if MP3 is missing
        mp3_art = db.query(Artifact).filter(Artifact.job_id == job.id, Artifact.kind == "dub_audio").first()
        if mp3_art and storage.exists(mp3_art.path):
            target_kind = "dub_audio"
            media_type = "audio/mpeg"
            filename = f"lecture_dub_{job.id}.mp3"
        else:
            target_kind = "dub_mix"
            media_type = "audio/wav"
            filename = f"lecture_dub_{job.id}.wav"

    file_path = None
    artifact = db.query(Artifact).filter(Artifact.job_id == job.id, Artifact.kind == target_kind).first()
    if artifact and storage.exists(artifact.path):
        file_path = storage.get_path(artifact.path)
    elif target_kind == "dub_mix" and storage.exists(f"jobs/{job.id}/dub_mix.wav"):
        file_path = storage.get_path(f"jobs/{job.id}/dub_mix.wav")
    elif target_kind == "dub_audio" and storage.exists(f"jobs/{job.id}/output/dub_audio.mp3"):
        file_path = storage.get_path(f"jobs/{job.id}/output/dub_audio.mp3")
    elif target_kind == "final_video" and storage.exists(f"jobs/{job.id}/output/final.mp4"):
        file_path = storage.get_path(f"jobs/{job.id}/output/final.mp4")

    if not file_path or not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"Output {kind} not ready for download")


    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename
    )


@router.get("/{job_id}/download-url")
def get_signed_download_url(
    job_id: str,
    kind: str = Query("video", pattern="^(video|audio|audio_mp3|audio_wav)$"),
    format: str = Query("mp3", pattern="^(mp3|wav)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns a short-lived signed download URL for the requested artifact."""
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    token = storage.create_signed_token(job_id=job.id, kind=kind, expires_in_seconds=3600)
    url = f"/api/jobs/{job.id}/download?kind={kind}&format={format}&token={token}"
    return {"download_url": url, "expires_in": 3600}



@router.post("/retention-cleanup")
def trigger_retention_cleanup(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Triggers retention cleanup of expired jobs and abandoned uploads."""
    results = run_retention_cleanup(db)
    return results
