import json
import shutil
import pytest
from unittest.mock import patch, MagicMock

from backend.app.db.models.user import User
from backend.app.db.models.job import Job
from backend.app.db.models.artifact import Artifact
from backend.app.db.models.attestation import Attestation
from backend.app.pipeline.state_machine import JobStatus, PipelineStage
from backend.app.pipeline.runner import PipelineRunner
from backend.app.storage.local import storage
from backend.app.ingest.media_probe import probe_media_file


def test_ingest_stage_from_upload(db, sample_mp4_bytes):
    # 1. Create User
    user = User(email="uploader@school.edu", password_hash="dummy")
    db.add(user)
    db.commit()

    # 2. Store upload file
    upload_id = "test_ingest_upload_1"
    storage.put(f"uploads/{upload_id}/source.mp4", sample_mp4_bytes)

    # 3. Create job
    job = Job(
        user_id=user.id,
        status=JobStatus.QUEUED.value,
        stage=PipelineStage.INGESTING.value,
        source_type="upload",
        source_ref=upload_id,
        target_lang="ur"
    )
    db.add(job)
    db.commit()

    # 4. Run ingest stage (real execution)
    runner = PipelineRunner(db, mock_execution=False)
    success = runner.run_next_stage(job.id)
    assert success is True

    db.refresh(job)
    assert job.stage == PipelineStage.EXTRACTING.value
    assert job.status == JobStatus.RUNNING.value

    # Verify source_video artifact
    artifact = db.query(Artifact).filter(
        Artifact.job_id == job.id,
        Artifact.kind == "source_video"
    ).first()
    assert artifact is not None
    assert storage.exists(artifact.path) is True

    # Verify ffprobe validity
    probe = probe_media_file(storage.get_path(artifact.path))
    assert probe.has_audio is True
    assert probe.has_video is True
    assert probe.duration > 0.0


def test_ingest_stage_from_url(db, sample_mp4_path):
    user = User(email="url_user@school.edu", password_hash="dummy")
    db.add(user)
    db.commit()

    job = Job(
        user_id=user.id,
        status=JobStatus.QUEUED.value,
        stage=PipelineStage.INGESTING.value,
        source_type="url",
        source_ref="https://example.com/lecture.mp4",
        target_lang="ur"
    )
    db.add(job)
    db.commit()

    # Mock download_safe_url to simulate downloading sample_mp4
    def fake_download_safe_url(url, dest):
        shutil.copy(sample_mp4_path, dest)

    with patch("backend.app.pipeline.runner.download_safe_url", side_effect=fake_download_safe_url):
        runner = PipelineRunner(db, mock_execution=False)
        success = runner.run_next_stage(job.id)
        assert success is True

    db.refresh(job)
    assert job.stage == PipelineStage.EXTRACTING.value

    artifact = db.query(Artifact).filter(
        Artifact.job_id == job.id,
        Artifact.kind == "source_video"
    ).first()
    assert artifact is not None
    assert storage.exists(artifact.path) is True


def test_ingest_stage_from_youtube_without_attestation_fails(db):
    user = User(email="yt_user@school.edu", password_hash="dummy")
    db.add(user)
    db.commit()

    job = Job(
        user_id=user.id,
        status=JobStatus.QUEUED.value,
        stage=PipelineStage.INGESTING.value,
        source_type="youtube",
        source_ref="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        target_lang="ur"
    )
    db.add(job)
    db.commit()

    # Run without attestation -> should fail
    runner = PipelineRunner(db, mock_execution=False)
    success = runner.run_next_stage(job.id)
    assert success is False

    db.refresh(job)
    assert job.status == JobStatus.FAILED.value
    assert "attestation" in job.error.lower()


def test_ingest_stage_from_youtube_with_attestation_succeeds(db, sample_mp4_path):
    user = User(email="yt_attested@school.edu", password_hash="dummy")
    db.add(user)
    db.commit()

    job = Job(
        user_id=user.id,
        status=JobStatus.QUEUED.value,
        stage=PipelineStage.INGESTING.value,
        source_type="youtube",
        source_ref="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        target_lang="ur"
    )
    db.add(job)
    db.commit()

    # Add required ownership attestation row
    att = Attestation(
        user_id=user.id,
        job_id=job.id,
        kind="ownership",
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        text="I own this content."
    )
    db.add(att)
    db.commit()

    # Mock youtube download to copy sample_mp4
    def fake_download_yt(url, out_path):
        shutil.copy(sample_mp4_path, out_path)
        return {"id": "dQw4w9WgXcQ", "title": "Test YT Video", "duration": 1.0}

    with patch("backend.app.pipeline.runner.download_youtube_video", side_effect=fake_download_yt):
        runner = PipelineRunner(db, mock_execution=False)
        success = runner.run_next_stage(job.id)
        assert success is True

    db.refresh(job)
    assert job.stage == PipelineStage.EXTRACTING.value

    artifact = db.query(Artifact).filter(
        Artifact.job_id == job.id,
        Artifact.kind == "source_video"
    ).first()
    assert artifact is not None
    assert storage.exists(artifact.path) is True
