import shutil
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from pathlib import Path
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.db.models.job import Job
from backend.app.db.models.artifact import Artifact
from backend.app.db.models.audit import AuditLog
from backend.app.storage.local import storage


def run_retention_cleanup(db: Session, max_job_age_days: int = None, upload_expiry_hours: int = 24) -> Dict[str, Any]:
    """
    Cleans up expired job artifacts and abandoned chunk uploads.
    - Purges storage for jobs past their retention date or explicitly marked expires_at.
    - Deletes abandoned chunk upload directories older than upload_expiry_hours.
    - Records audit logs for compliance.
    """
    if max_job_age_days is None:
        max_job_age_days = settings.RETENTION_DAYS

    now = datetime.now(timezone.utc)
    cutoff_date = now - timedelta(days=max_job_age_days)

    purged_jobs_count = 0
    purged_artifacts_count = 0
    deleted_bytes = 0

    # 1. Identify jobs eligible for retention purging
    # Eligible: (completed, failed, canceled) and older than cutoff_date, OR explicitly past expires_at
    jobs_to_purge = db.query(Job).filter(
        (Job.expires_at != None) & (Job.expires_at < now) |
        (Job.status.in_(["completed", "failed", "canceled"])) & (Job.created_at < cutoff_date)
    ).all()

    for job in jobs_to_purge:
        job_artifacts = db.query(Artifact).filter(Artifact.job_id == job.id).all()
        for art in job_artifacts:
            art_path = storage.get_path(art.path)
            if art_path.exists():
                try:
                    deleted_bytes += art_path.stat().st_size
                    art_path.unlink()
                except OSError as e:
                    logger.warning(f"Failed to delete artifact file {art_path}: {e}")
            db.delete(art)
            purged_artifacts_count += 1

        # Also purge job directory if anything remains
        job_dir = storage.get_path(f"jobs/{job.id}")
        if job_dir.exists():
            try:
                shutil.rmtree(job_dir, ignore_errors=True)
            except Exception as e:
                logger.warning(f"Failed to remove directory {job_dir}: {e}")

        # Record audit log
        audit = AuditLog(
            user_id=job.user_id,
            action="retention_purge",
            detail=f"Purged storage artifacts for job {job.id} due to retention expiration."
        )
        db.add(audit)
        purged_jobs_count += 1

    # 2. Clean abandoned upload sessions
    abandoned_uploads_count = 0
    uploads_dir = storage.get_path("uploads")
    if uploads_dir.exists():
        now_ts = time.time()
        expiry_seconds = upload_expiry_hours * 3600
        for entry in uploads_dir.iterdir():
            if entry.is_dir():
                try:
                    mtime = entry.stat().st_mtime
                    if now_ts - mtime > expiry_seconds:
                        logger.info(f"Removing abandoned upload session: {entry.name}")
                        shutil.rmtree(entry, ignore_errors=True)
                        abandoned_uploads_count += 1
                except Exception as e:
                    logger.warning(f"Error inspecting upload dir {entry}: {e}")

    db.commit()

    logger.info(
        f"Retention cleanup finished: {purged_jobs_count} jobs purged, "
        f"{purged_artifacts_count} artifacts removed, {deleted_bytes / (1024*1024):.2f} MB freed, "
        f"{abandoned_uploads_count} abandoned upload sessions removed."
    )

    return {
        "purged_jobs": purged_jobs_count,
        "purged_artifacts": purged_artifacts_count,
        "deleted_mb": round(deleted_bytes / (1024 * 1024), 2),
        "abandoned_uploads_removed": abandoned_uploads_count
    }
