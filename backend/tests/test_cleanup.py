import time
import os
from datetime import datetime, timezone, timedelta
import pytest

from backend.app.db.models.user import User
from backend.app.db.models.job import Job
from backend.app.db.models.artifact import Artifact
from backend.app.db.models.audit import AuditLog
from backend.app.pipeline.state_machine import JobStatus
from backend.app.storage.local import storage
from backend.app.ingest.cleanup import run_retention_cleanup


def test_retention_cleanup_expired_jobs(db):
    user = User(email="retention_user@college.edu", password_hash="dummy")
    db.add(user)
    db.commit()

    # Create an expired job (expires_at in the past)
    past_time = datetime.now(timezone.utc) - timedelta(days=2)
    job = Job(
        user_id=user.id,
        status=JobStatus.COMPLETED.value,
        stage="muxing",
        source_type="upload",
        source_ref="test_ref",
        target_lang="en",
        expires_at=past_time
    )
    db.add(job)
    db.commit()

    # Create artifact on disk and in DB
    art_key = f"jobs/{job.id}/output/final.mp4"
    storage.put(art_key, b"FINAL_VIDEO_DATA")
    art = Artifact(job_id=job.id, kind="final_video", path=art_key, stage="muxing")
    db.add(art)
    db.commit()

    assert storage.exists(art_key) is True

    # Run cleanup
    summary = run_retention_cleanup(db, max_job_age_days=14)
    assert summary["purged_jobs"] >= 1
    assert summary["purged_artifacts"] >= 1

    # Verify file deleted from storage
    assert storage.exists(art_key) is False

    # Verify artifact removed from DB
    remaining_art = db.query(Artifact).filter(Artifact.id == art.id).first()
    assert remaining_art is None

    # Verify audit log was created
    audit = db.query(AuditLog).filter(
        AuditLog.user_id == user.id,
        AuditLog.action == "retention_purge"
    ).first()
    assert audit is not None


def test_retention_cleanup_abandoned_uploads(db):
    # Create an abandoned upload directory
    upload_dir = storage.get_path("uploads/abandoned_session_999")
    upload_dir.mkdir(parents=True, exist_ok=True)
    (upload_dir / "meta.json").write_text("{}", encoding="utf-8")

    # Set mtime to 48 hours ago
    old_time = time.time() - (48 * 3600)
    os.utime(upload_dir, (old_time, old_time))

    # Run cleanup with 24 hours expiry
    summary = run_retention_cleanup(db, max_job_age_days=14, upload_expiry_hours=24)
    assert summary["abandoned_uploads_removed"] >= 1
    assert upload_dir.exists() is False
