import subprocess
from pathlib import Path
import pytest
import soundfile as sf
import numpy as np

from backend.app.core.config import settings
from backend.app.db.models.user import User
from backend.app.db.models.job import Job
from backend.app.db.models.artifact import Artifact
from backend.app.pipeline.state_machine import JobStatus, PipelineStage
from backend.app.pipeline.runner import PipelineRunner
from backend.app.storage.local import storage
from backend.app.ingest.media_probe import probe_media_file


@pytest.fixture
def test_av_pair(tmp_path):
    vid_path = tmp_path / "source.mp4"
    ffmpeg_cmd = settings.get_ffmpeg_cmd()
    cmd = [
        ffmpeg_cmd, "-y",
        "-f", "lavfi",
        "-i", "testsrc=duration=2.5:size=320x240:rate=24",
        "-f", "lavfi",
        "-i", "sine=frequency=440:duration=2.5",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-ar", "44100",
        str(vid_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    wav_path = tmp_path / "dub_mix.wav"
    sr = 44100
    t = np.linspace(0, 2.5, int(2.5 * sr), endpoint=False)
    data = (0.2 * np.sin(2 * np.pi * 500 * t)).astype(np.float32)
    sf.write(str(wav_path), np.column_stack([data, data]), sr)

    return vid_path, wav_path


def test_phase5_video_mux_stage_and_completion(client, auth_headers, db, test_av_pair):
    user = db.query(User).filter(User.email == "testuser@example.com").first()
    vid_path, wav_path = test_av_pair

    job = Job(
        user_id=user.id,
        source_type="upload",
        source_ref="phase5_test_ref",
        source_lang="en",
        target_lang="ur",
        status=JobStatus.RUNNING.value,
        stage=PipelineStage.MUXING.value,
        options_json='{"clone_voice": true}'
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Place source video and dubbed audio mix in storage
    with open(vid_path, "rb") as f:
        storage.put(f"jobs/{job.id}/source.mp4", f.read())
    with open(wav_path, "rb") as f:
        storage.put(f"jobs/{job.id}/dub_mix.wav", f.read())

    # Run Stage 9: MUXING
    runner = PipelineRunner(db, mock_execution=False)
    progress_made = runner.run_next_stage(job.id)
    assert progress_made is True

    db.refresh(job)
    assert job.status == JobStatus.COMPLETED.value
    assert job.stage == PipelineStage.COMPLETED.value
    assert job.progress == 100

    # Verify final.mp4 exists in storage and is valid
    final_video_key = f"jobs/{job.id}/output/final.mp4"
    assert storage.exists(final_video_key)
    final_probe = probe_media_file(storage.get_path(final_video_key))
    assert final_probe.has_video is True
    assert final_probe.has_audio is True
    assert abs(final_probe.duration - 2.5) < 0.3

    # Verify dub_audio.mp3 exists
    assert storage.exists(f"jobs/{job.id}/output/dub_audio.mp3")

    # Verify Job details include honest time estimates
    job_resp = client.get(f"/api/jobs/{job.id}", headers=auth_headers)
    assert job_resp.status_code == 200
    job_data = job_resp.json()
    assert job_data["status"] == "completed"
    assert job_data["estimated_seconds_remaining"] == 0
    assert job_data["estimated_total_seconds"] > 0


def test_phase5_download_artifacts(client, auth_headers, db, test_av_pair):
    user = db.query(User).filter(User.email == "testuser@example.com").first()
    vid_path, wav_path = test_av_pair

    job = Job(
        user_id=user.id,
        source_type="upload",
        source_ref="phase5_dl_ref",
        source_lang="en",
        target_lang="ur",
        status=JobStatus.RUNNING.value,
        stage=PipelineStage.MUXING.value
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    with open(vid_path, "rb") as f:
        storage.put(f"jobs/{job.id}/source.mp4", f.read())
    with open(wav_path, "rb") as f:
        storage.put(f"jobs/{job.id}/dub_mix.wav", f.read())
    db.add(Artifact(job_id=job.id, kind="dub_mix", path=f"jobs/{job.id}/dub_mix.wav", stage=PipelineStage.MIXING.value))
    db.commit()

    runner = PipelineRunner(db, mock_execution=False)
    runner.run_next_stage(job.id)

    # 1. Download video (authenticated)
    res_vid = client.get(f"/api/jobs/{job.id}/download?kind=video", headers=auth_headers)
    assert res_vid.status_code == 200
    assert res_vid.headers["content-type"] == "video/mp4"
    assert len(res_vid.content) > 1000

    # 2. Download audio MP3
    res_mp3 = client.get(f"/api/jobs/{job.id}/download?kind=audio&format=mp3", headers=auth_headers)
    assert res_mp3.status_code == 200
    assert res_mp3.headers["content-type"] == "audio/mpeg"
    assert len(res_mp3.content) > 1000

    # 3. Download audio WAV
    res_wav = client.get(f"/api/jobs/{job.id}/download?kind=audio&format=wav", headers=auth_headers)
    assert res_wav.status_code == 200
    assert res_wav.headers["content-type"] == "audio/wav"
    assert len(res_wav.content) > 1000

    # 4. Signed download URL
    url_resp = client.get(f"/api/jobs/{job.id}/download-url?kind=video", headers=auth_headers)
    assert url_resp.status_code == 200
    signed_url = url_resp.json()["download_url"]
    assert "token=" in signed_url

    # Anonymous user downloads using signed URL
    res_signed = client.get(signed_url)
    assert res_signed.status_code == 200
    assert res_signed.headers["content-type"] == "video/mp4"

    # Invalid token rejection
    bad_token_url = f"/api/jobs/{job.id}/download?kind=video&token=INVALID_TOKEN"
    res_bad = client.get(bad_token_url)
    assert res_bad.status_code == 403
