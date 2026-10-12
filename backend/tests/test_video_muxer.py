import subprocess
from pathlib import Path
import pytest
import soundfile as sf
import numpy as np

from backend.app.core.config import settings
from backend.app.pipeline.video_muxer import (
    mux_video_and_audio,
    export_dub_mp3,
    AVSyncDriftError
)
from backend.app.ingest.media_probe import probe_media_file


@pytest.fixture
def sample_video_mp4(tmp_path) -> Path:
    vid_path = tmp_path / "source.mp4"
    ffmpeg_cmd = settings.get_ffmpeg_cmd()
    cmd = [
        ffmpeg_cmd, "-y",
        "-f", "lavfi",
        "-i", "testsrc=duration=3.0:size=320x240:rate=24",
        "-f", "lavfi",
        "-i", "sine=frequency=440:duration=3.0",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-ar", "44100",
        str(vid_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return vid_path


@pytest.fixture
def sample_dub_wav(tmp_path) -> Path:
    wav_path = tmp_path / "dub_mix.wav"
    sr = 44100
    t = np.linspace(0, 3.0, int(3.0 * sr), endpoint=False)
    data = (0.2 * np.sin(2 * np.pi * 500 * t)).astype(np.float32)
    sf.write(str(wav_path), np.column_stack([data, data]), sr)
    return wav_path


def test_mux_video_and_audio_success(sample_video_mp4, sample_dub_wav, tmp_path):
    output_mp4 = tmp_path / "final.mp4"

    res = mux_video_and_audio(
        video_path=sample_video_mp4,
        audio_path=sample_dub_wav,
        output_path=output_mp4,
        target_lang="ur",
        tolerance_seconds=1.0,
        title="Physics 101 - Dubbed Urdu"
    )

    assert output_mp4.is_file()
    assert res.has_video is True
    assert res.has_audio is True
    assert abs(res.duration - 3.0) < 0.3
    assert res.width == 320
    assert res.height == 240
    audio_streams = [s for s in res.streams if s.get("codec_type") == "audio"]
    assert len(audio_streams) == 2


def test_mux_video_and_audio_drift_tolerance_failure(sample_video_mp4, tmp_path):
    output_mp4 = tmp_path / "drift_fail.mp4"

    # Create audio that is 8 seconds long when video is only 3 seconds long (drift = 5s)
    long_wav = tmp_path / "long_dub.wav"
    sr = 44100
    t = np.linspace(0, 8.0, int(8.0 * sr), endpoint=False)
    data = (0.2 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    sf.write(str(long_wav), np.column_stack([data, data]), sr)

    with pytest.raises(AVSyncDriftError) as exc_info:
        mux_video_and_audio(
            video_path=sample_video_mp4,
            audio_path=long_wav,
            output_path=output_mp4,
            target_lang="ur",
            tolerance_seconds=1.0
        )

    assert "Audio-video sync drift" in str(exc_info.value)
    assert "exceeded tolerance" in str(exc_info.value)


def test_export_dub_mp3(sample_dub_wav, tmp_path):
    output_mp3 = tmp_path / "dub_audio.mp3"
    res_path = export_dub_mp3(sample_dub_wav, output_mp3)

    assert res_path.is_file()
    assert res_path == output_mp3
    probe = probe_media_file(res_path)
    assert probe.has_audio is True
    assert abs(probe.duration - 3.0) < 0.3
