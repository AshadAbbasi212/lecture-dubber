import os
import subprocess
import tempfile
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.security import hash_password, create_access_token
from backend.app.db.models.user import User
from backend.app.db.models.job import Job
from backend.app.db.models.artifact import Artifact
from backend.app.db.models.segment import Segment
from backend.app.pipeline.state_machine import JobStatus, PipelineStage
from backend.app.core.config import settings
from backend.app.storage.local import storage
from backend.app.ingest.media_probe import probe_media_file
from backend.app.pipeline.video_muxer import mux_video_and_audio, export_dub_mp3
from backend.app.pipeline.audio_mixer import mix_vocals_and_background, assemble_timeline_vocals
from backend.app.pipeline.timing_fit import calculate_timing_fit, apply_audio_time_stretch
import soundfile as sf
import numpy as np


def create_synthetic_test_video(output_path: Path, duration_sec: int = 3):
    """Generates a small valid MP4 video with AAC audio stream using FFmpeg."""
    ffmpeg_cmd = settings.get_ffmpeg_cmd()
    cmd = [
        ffmpeg_cmd, "-y",
        "-f", "lavfi", "-i", f"testsrc=size=320x240:rate=25",
        "-f", "lavfi", "-i", f"sine=frequency=440:sample_rate=44100",
        "-t", str(duration_sec),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        str(output_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert res.returncode == 0, f"FFmpeg failed to create synthetic video: {res.stderr.decode()}"


def test_e2e_short_clip_pipeline(client, db):
    """
    End-to-end integration test executing real media processing on a short clip:
    1. Probe media with ffprobe
    2. Extract audio streams
    3. Generate and align dubbed timeline
    4. Mix vocals and background audio with ducking
    5. Stream-copy mux video and dub audio into final MP4 & export MP3
    6. Verify duration match & drift tolerance
    7. Test API download and signed token endpoints
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        source_video = tmp_path / "lecture_source.mp4"
        create_synthetic_test_video(source_video, duration_sec=3)

        # 1. Probe input video
        probe_info = probe_media_file(source_video)
        assert probe_info.has_video is True
        assert probe_info.has_audio is True
        assert 2.8 <= probe_info.duration <= 3.2

        # 2. Setup user and job
        user = User(email="e2e_prof@university.edu", password_hash=hash_password("Secret123!"))
        db.add(user)
        db.commit()

        job_dir = tmp_path / "job_run"
        job_dir.mkdir(parents=True, exist_ok=True)
        job_source = job_dir / "source.mp4"
        job_source.write_bytes(source_video.read_bytes())

        job = Job(
            user_id=user.id,
            status=JobStatus.RUNNING.value,
            stage=PipelineStage.EXTRACTING.value,
            progress=10,
            source_type="upload",
            source_ref=str(job_source),
            target_lang="ur"
        )
        db.add(job)
        db.commit()

        # 3. Extract Audio Stems
        audio_dir = job_dir / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        original_wav = audio_dir / "original.wav"
        vocals_wav = audio_dir / "vocals.wav"
        bg_wav = audio_dir / "background.wav"

        # Extract 44.1kHz stereo
        cmd_extract = [
            settings.get_ffmpeg_cmd(), "-y", "-i", str(job_source),
            "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
            str(original_wav)
        ]
        assert subprocess.run(cmd_extract).returncode == 0
        assert original_wav.exists()

        # Separate simulation: split tone into vocals and quiet background
        orig_data, sr = sf.read(str(original_wav))
        sf.write(str(vocals_wav), orig_data, sr)
        sf.write(str(bg_wav), orig_data * 0.1, sr)

        # 4. Synthesize dubbed segments & assemble timeline
        tts_dir = job_dir / "tts"
        tts_dir.mkdir(parents=True, exist_ok=True)
        seg_wav = tts_dir / "seg_0001.wav"

        # Generate 2.0s dubbed speech simulation (sine wave at 300Hz)
        t = np.linspace(0, 2.0, int(sr * 2.0), endpoint=False)
        speech_synth = (0.5 * np.sin(2 * np.pi * 300 * t)).astype(np.float32)
        sf.write(str(seg_wav), speech_synth, sr)

        # Segment with start 0.5s, end 2.5s (target duration 2.0s)
        seg = Segment(
            job_id=job.id,
            idx=0,
            start=0.5,
            end=2.5,
            speaker="SPEAKER_0",
            src_text="Welcome to the lecture.",
            tgt_text="لیکچر میں خوش آمدید۔",
            tts_path=str(seg_wav),
            tts_duration=2.0,
            stretch_ratio=1.0
        )
        db.add(seg)
        db.commit()

        # Assemble timeline vocals
        total_duration = probe_info.duration
        dub_vocals_path = job_dir / "dub_vocals.wav"
        assemble_timeline_vocals([seg], total_duration, output_vocals_path=dub_vocals_path, sample_rate=sr)
        assert dub_vocals_path.exists()

        # 5. Mix with background and dynamic ducking
        dub_mix_path = job_dir / "dub_mix.wav"
        mix_vocals_and_background(
            dub_vocals_path=dub_vocals_path,
            background_path=bg_wav,
            output_mix_path=dub_mix_path
        )
        assert dub_mix_path.exists()

        # 6. Stream-copy mux final video
        output_dir = job_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        final_mp4 = output_dir / "final.mp4"
        dub_mp3 = output_dir / "dub_audio.mp3"

        mux_video_and_audio(
            video_path=job_source,
            audio_path=dub_mix_path,
            output_path=final_mp4,
            target_lang="ur"
        )
        assert final_mp4.exists()

        export_dub_mp3(
            audio_wav_path=dub_mix_path,
            output_mp3_path=dub_mp3
        )
        assert dub_mp3.exists()

        # 7. Validate output artifacts with ffprobe
        final_probe = probe_media_file(final_mp4)
        assert final_probe.has_video is True
        assert final_probe.has_audio is True
        # Drift must be under 0.5s
        assert abs(final_probe.duration - total_duration) < 0.5

        mp3_probe = probe_media_file(dub_mp3)
        assert mp3_probe.has_audio is True
        assert abs(mp3_probe.duration - total_duration) < 0.5

        # 8. Record in database and mark completed
        art_video = Artifact(job_id=job.id, kind="final_video", path=f"jobs/{job.id}/output/final.mp4", stage="muxing")
        art_mp3 = Artifact(job_id=job.id, kind="dub_audio", path=f"jobs/{job.id}/output/dub_audio.mp3", stage="muxing")
        art_mix = Artifact(job_id=job.id, kind="dub_mix", path=f"jobs/{job.id}/dub_mix.wav", stage="mixing")
        db.add_all([art_video, art_mp3, art_mix])
        job.status = JobStatus.COMPLETED.value
        job.stage = PipelineStage.COMPLETED.value
        job.progress = 100
        db.commit()

        # Store in storage for API retrieval
        storage.put(f"jobs/{job.id}/output/final.mp4", final_mp4.read_bytes())
        storage.put(f"jobs/{job.id}/output/dub_audio.mp3", dub_mp3.read_bytes())
        storage.put(f"jobs/{job.id}/dub_mix.wav", dub_mix_path.read_bytes())

        # 9. Verify API download with signed token
        auth_token = create_access_token({"sub": user.id})

        # Request signed token for video
        res_signed = client.get(
            f"/api/jobs/{job.id}/download-url?kind=video",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert res_signed.status_code == 200
        signed_data = res_signed.json()
        assert "download_url" in signed_data
        download_url = signed_data["download_url"]

        # Fetch using signed URL without auth header
        res_dl = client.get(download_url)
        assert res_dl.status_code == 200
        assert res_dl.headers["content-type"] == "video/mp4"
        assert len(res_dl.content) > 0
