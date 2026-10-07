import json
import pytest
from unittest.mock import patch

from backend.app.db.models.user import User
from backend.app.db.models.job import Job
from backend.app.db.models.segment import Segment
from backend.app.db.models.artifact import Artifact
from backend.app.pipeline.state_machine import JobStatus, PipelineStage
from backend.app.pipeline.runner import PipelineRunner
from backend.app.storage.local import storage
from backend.app.engines.base import ASRResult, TranscriptSegment


def test_phase3_pipeline_stages_reach_awaiting_review(client, auth_headers, db, sample_mp4_bytes):
    # 1. Create a user
    user = db.query(User).filter(User.email == "testuser@example.com").first()

    # 2. Upload sample MP4
    upload_id = "phase3_test_upload"
    storage.put(f"uploads/{upload_id}/source.mp4", sample_mp4_bytes)

    # 3. Create job with review enabled
    create_resp = client.post("/api/jobs", json={
        "source_type": "upload",
        "source_ref": upload_id,
        "target_lang": "ur",
        "clone_voice": False,
        "skip_review": False
    }, headers=auth_headers)
    assert create_resp.status_code == 200
    job_id = create_resp.json()["id"]

    runner = PipelineRunner(db, mock_execution=False)

    # Run Stage 1: INGESTING
    r1 = runner.run_next_stage(job_id)
    assert r1 is True
    job = db.query(Job).filter(Job.id == job_id).first()
    assert job.stage == PipelineStage.EXTRACTING.value

    # Run Stage 2: EXTRACTING
    r2 = runner.run_next_stage(job_id)
    assert r2 is True
    db.refresh(job)
    assert job.stage == PipelineStage.SEPARATING.value
    assert storage.exists(f"jobs/{job_id}/audio/original.wav")
    assert storage.exists(f"jobs/{job_id}/audio/asr_16k.wav")

    # Run Stage 3: SEPARATING
    r3 = runner.run_next_stage(job_id)
    assert r3 is True
    db.refresh(job)
    assert job.stage == PipelineStage.TRANSCRIBING.value
    assert storage.exists(f"jobs/{job_id}/audio/vocals.wav")
    assert storage.exists(f"jobs/{job_id}/audio/background.wav")

    # Run Stage 4: TRANSCRIBING (using mock for ASR result to avoid heavy GPU download during test)
    mock_asr_result = ASRResult(
        language="en",
        language_probability=0.99,
        duration=1.0,
        segments=[
            TranscriptSegment(1, 0.0, 1.0, "Welcome to the lecture on computer algorithms.")
        ]
    )
    with patch("backend.app.pipeline.runner.FasterWhisperASREngine.transcribe", return_value=mock_asr_result):
        r4 = runner.run_next_stage(job_id)
        assert r4 is True

    db.refresh(job)
    assert job.stage == PipelineStage.TRANSLATING.value
    assert storage.exists(f"jobs/{job_id}/transcript.json")

    # Run Stage 5: TRANSLATING
    r5 = runner.run_next_stage(job_id)
    assert r5 is True

    # Job MUST reach awaiting_review!
    db.refresh(job)
    assert job.status == JobStatus.AWAITING_REVIEW.value
    assert job.stage == PipelineStage.SYNTHESIZING.value
    assert storage.exists(f"jobs/{job_id}/translation.json")

    # 4. Fetch segments via API
    segs_resp = client.get(f"/api/jobs/{job_id}/segments", headers=auth_headers)
    assert segs_resp.status_code == 200
    segs_data = segs_resp.json()
    assert len(segs_data) == 1
    seg_item = segs_data[0]
    assert "الگورتھم" in seg_item["tgt_text"]
    assert seg_item["edited_by_user"] is False

    # 5. User edits segment
    new_urdu_text = "تمام طلباء کو کمپیوٹر الگورتھم کی کلاس میں خوش آمدید۔"
    edit_resp = client.put(f"/api/jobs/{job_id}/segments", json=[
        {"id": seg_item["id"], "tgt_text": new_urdu_text}
    ], headers=auth_headers)
    assert edit_resp.status_code == 200
    updated_seg = edit_resp.json()[0]
    assert updated_seg["edited_by_user"] is True
    assert updated_seg["tgt_text"] == new_urdu_text

    # 6. User approves job
    approve_resp = client.post(f"/api/jobs/{job_id}/approve", headers=auth_headers)
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == JobStatus.RUNNING.value
    db.refresh(job)
    assert job.status == JobStatus.RUNNING.value
    assert job.stage == PipelineStage.SYNTHESIZING.value


def test_phase3_skip_review_flow(client, auth_headers, db, sample_mp4_bytes):
    upload_id = "phase3_skip_review_upload"
    storage.put(f"uploads/{upload_id}/source.mp4", sample_mp4_bytes)

    # Job created with skip_review = True
    create_resp = client.post("/api/jobs", json={
        "source_type": "upload",
        "source_ref": upload_id,
        "target_lang": "ur",
        "skip_review": True
    }, headers=auth_headers)
    assert create_resp.status_code == 200
    job_id = create_resp.json()["id"]

    runner = PipelineRunner(db, mock_execution=False)

    # Ingest, Extract, Separate
    runner.run_next_stage(job_id)
    runner.run_next_stage(job_id)
    runner.run_next_stage(job_id)

    mock_asr_result = ASRResult(
        language="en",
        language_probability=0.99,
        duration=1.0,
        segments=[TranscriptSegment(1, 0.0, 1.0, "Welcome to the lecture.")]
    )
    with patch("backend.app.pipeline.runner.FasterWhisperASREngine.transcribe", return_value=mock_asr_result):
        runner.run_next_stage(job_id)  # Transcribing

    # Translating with skip_review=True
    runner.run_next_stage(job_id)

    job = db.query(Job).filter(Job.id == job_id).first()
    # Should NOT pause at awaiting_review; status should remain RUNNING
    assert job.status == JobStatus.RUNNING.value
    assert job.stage == PipelineStage.SYNTHESIZING.value
