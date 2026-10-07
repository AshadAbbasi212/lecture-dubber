import json
import pytest
from backend.app.db.models.user import User
from backend.app.db.models.job import Job
from backend.app.db.models.artifact import Artifact
from backend.app.db.models.segment import Segment
from backend.app.worker.worker import DubberWorker
from backend.app.worker.queue import JobQueue
from backend.app.pipeline.state_machine import JobStatus, PipelineStage
from backend.app.pipeline.runner import PipelineRunner


def test_end_to_end_worker_pipeline(db):
    # 1. Create a user
    user = User(email="prof@college.edu", password_hash="dummyhash")
    db.add(user)
    db.commit()

    # 2. Create a job with review enabled
    job = Job(
        user_id=user.id,
        status=JobStatus.QUEUED.value,
        stage=PipelineStage.INGESTING.value,
        progress=0,
        source_type="upload",
        source_ref="test_upload_123",
        target_lang="ur",
        options_json=json.dumps({"skip_review": False, "clone_voice": True})
    )
    db.add(job)
    db.commit()

    worker = DubberWorker(mock_execution=True)

    # 3. Step worker until job enters awaiting_review
    steps = 0
    while job.status != JobStatus.AWAITING_REVIEW.value and steps < 20:
        worked = worker.run_once(db=db)
        assert worked, "Worker should find work"
        db.refresh(job)
        steps += 1

    assert job.status == JobStatus.AWAITING_REVIEW.value
    assert job.stage == PipelineStage.SYNTHESIZING.value

    # Verify segments were produced for review
    segments = db.query(Segment).filter(Segment.job_id == job.id).all()
    assert len(segments) > 0
    assert segments[0].src_text != ""
    assert segments[0].tgt_text != ""

    # 4. User approves review
    job.status = JobStatus.RUNNING.value
    db.commit()

    # 5. Step worker until completed
    steps = 0
    while job.status != JobStatus.COMPLETED.value and steps < 20:
        worked = worker.run_once(db=db)
        assert worked, "Worker should continue processing"
        db.refresh(job)
        steps += 1

    assert job.status == JobStatus.COMPLETED.value
    assert job.stage == PipelineStage.COMPLETED.value
    assert job.progress == 100

    # 6. Verify final artifacts recorded
    final_artifact = db.query(Artifact).filter(
        Artifact.job_id == job.id,
        Artifact.kind == "final_video"
    ).first()
    assert final_artifact is not None


def test_crash_recovery(db):
    user = User(email="recovery@test.edu", password_hash="dummyhash")
    db.add(user)
    db.commit()

    # Job stuck in 'running' status due to simulate server restart
    job = Job(
        user_id=user.id,
        status=JobStatus.RUNNING.value,
        stage=PipelineStage.SEPARATING.value,
        progress=20,
        source_type="upload",
        source_ref="crash_test",
        target_lang="en",
        options_json=json.dumps({"skip_review": True})
    )
    db.add(job)
    db.commit()

    # Recover
    recovered = JobQueue.recover_orphaned_jobs(db)
    assert recovered == 1

    # Worker can resume it directly
    worker = DubberWorker(mock_execution=True)
    worked = worker.run_once(db=db)
    assert worked
    db.refresh(job)
    assert job.stage != PipelineStage.SEPARATING.value
