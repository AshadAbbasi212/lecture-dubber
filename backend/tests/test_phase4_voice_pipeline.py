import time
from pathlib import Path
import numpy as np
import soundfile as sf
import pytest

from backend.app.core.security import hash_password
from backend.app.db.models.user import User
from backend.app.db.models.job import Job
from backend.app.db.models.segment import Segment
from backend.app.pipeline.state_machine import JobStatus, PipelineStage
from backend.app.pipeline.runner import PipelineRunner
from backend.app.storage.local import storage
from backend.app.ingest.media_probe import probe_media_file


def _create_wav_file(path: Path, duration: float = 2.0, sr: int = 44100) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    t = np.linspace(0, duration, int(duration * sr), endpoint=False)
    data = (0.2 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    sf.write(str(path), np.column_stack([data, data]), sr)
    return path


def test_phase4_voice_synthesis_and_mixing(client, auth_headers, db, sample_mp4_bytes):
    # 1. Create a job directly up to awaiting_review with 2 segments
    user = db.query(User).filter(User.email == "testuser@example.com").first()
    job = Job(
        user_id=user.id,
        source_type="upload",
        source_ref="test_phase4_ref",
        source_lang="en",
        target_lang="ur",
        status=JobStatus.AWAITING_REVIEW.value,
        stage=PipelineStage.SYNTHESIZING.value,
        options_json='{"clone_voice": true, "skip_review": false}'
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Put source video and audio tracks in storage
    storage.put(f"jobs/{job.id}/source.mp4", sample_mp4_bytes)
    _create_wav_file(storage.get_path(f"jobs/{job.id}/audio/vocals.wav"), duration=5.0)
    _create_wav_file(storage.get_path(f"jobs/{job.id}/audio/background.wav"), duration=5.0)

    # Add 2 segments
    seg1 = Segment(
        job_id=job.id,
        idx=1,
        start=0.5,
        end=4.0,
        speaker="speaker_0",
        src_text="Welcome to the lecture.",
        tgt_text="لیکچر میں خوش آمدید۔"
    )
    seg2 = Segment(
        job_id=job.id,
        idx=2,
        start=4.5,
        end=8.0,
        speaker="speaker_0",
        src_text="Today we learn algorithms.",
        tgt_text="آج ہم الگورتھم سیکھیں گے۔"
    )
    db.add_all([seg1, seg2])
    db.commit()

    # 2. User approves the job
    approve_resp = client.post(f"/api/jobs/{job.id}/approve", headers=auth_headers)
    assert approve_resp.status_code == 200
    db.refresh(job)
    assert job.status == JobStatus.RUNNING.value
    assert job.stage == PipelineStage.SYNTHESIZING.value

    # 3. Run Stage 7: SYNTHESIZING
    runner = PipelineRunner(db, mock_execution=False)
    progress_made = runner.run_next_stage(job.id)
    assert progress_made is True

    db.refresh(job)
    assert job.stage == PipelineStage.MIXING.value

    # Verify segments were updated with tts checkpoints
    db_segs = db.query(Segment).filter(Segment.job_id == job.id).order_by(Segment.idx.asc()).all()
    assert len(db_segs) == 2
    for s in db_segs:
        assert s.tts_path is not None
        assert s.tts_duration is not None and s.tts_duration > 0
        assert s.stretch_ratio is not None
        assert storage.exists(s.tts_path)

    # Verify dub_vocals.wav exists
    assert storage.exists(f"jobs/{job.id}/dub_vocals.wav")
    voc_path = storage.get_path(f"jobs/{job.id}/dub_vocals.wav")
    probe_voc = probe_media_file(voc_path)
    assert probe_voc.duration > 0

    # 4. Run Stage 8: MIXING
    progress_made = runner.run_next_stage(job.id)
    assert progress_made is True

    db.refresh(job)
    assert job.stage == PipelineStage.MUXING.value

    # Verify dub_mix.wav exists
    assert storage.exists(f"jobs/{job.id}/dub_mix.wav")
    mix_path = storage.get_path(f"jobs/{job.id}/dub_mix.wav")
    probe_mix = probe_media_file(mix_path)
    assert probe_mix.duration > 0
    assert probe_mix.channels == 2
    assert probe_mix.sample_rate == 44100


def test_phase4_per_segment_checkpoint_crash_recovery(db, sample_mp4_bytes):
    # Tests that when a job is interrupted mid-synthesis, already completed segments are preserved
    user = db.query(User).first()
    if not user:
        user = User(email="test_checkpoint@example.com", password_hash=hash_password("pass123456"))
        db.add(user)
        db.commit()
        db.refresh(user)

    job = Job(
        user_id=user.id,
        source_type="upload",
        source_ref="test_checkpoint_ref",
        source_lang="en",
        target_lang="ur",
        status=JobStatus.RUNNING.value,
        stage=PipelineStage.SYNTHESIZING.value,
        options_json='{"clone_voice": false}'
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    storage.put(f"jobs/{job.id}/source.mp4", sample_mp4_bytes)

    # Create 3 segments
    seg1 = Segment(job_id=job.id, idx=1, start=0.0, end=2.5, src_text="One", tgt_text="ایک")
    seg2 = Segment(job_id=job.id, idx=2, start=3.0, end=5.5, src_text="Two", tgt_text="دو")
    seg3 = Segment(job_id=job.id, idx=3, start=6.0, end=8.5, src_text="Three", tgt_text="تین")
    db.add_all([seg1, seg2, seg3])
    db.commit()

    # Pre-synthesize segment 1 (simulating crash after seg 1 completed)
    seg1_key = f"jobs/{job.id}/tts/seg_0001.wav"
    _create_wav_file(storage.get_path(seg1_key), duration=2.0)

    seg1_mtime_before = storage.get_path(seg1_key).stat().st_mtime
    seg1.tts_path = seg1_key
    seg1.tts_duration = 2.0
    seg1.stretch_ratio = 1.0
    db.commit()

    # Sleep slightly so mtime would change if rewritten
    time.sleep(0.05)

    runner = PipelineRunner(db, mock_execution=False)
    progress_made = runner.run_next_stage(job.id)
    assert progress_made is True

    # Segment 1 should NOT have been touched / overwritten
    seg1_mtime_after = storage.get_path(seg1_key).stat().st_mtime
    assert seg1_mtime_after == seg1_mtime_before

    # Segments 2 and 3 should now have been synthesized
    db.refresh(seg2)
    db.refresh(seg3)
    assert seg2.tts_duration is not None and seg2.tts_duration > 0
    assert seg3.tts_duration is not None and seg3.tts_duration > 0
    assert storage.exists(seg2.tts_path)
    assert storage.exists(seg3.tts_path)
