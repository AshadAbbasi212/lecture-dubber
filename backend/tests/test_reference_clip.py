import subprocess
from pathlib import Path
import pytest

from backend.app.core.config import settings
from backend.app.pipeline.reference_clip import build_reference_clip
from backend.app.db.models.segment import Segment
from backend.app.ingest.media_probe import probe_media_file


@pytest.fixture
def sample_vocals_wav(tmp_path) -> Path:
    wav_path = tmp_path / "vocals.wav"
    ffmpeg_cmd = settings.get_ffmpeg_cmd()
    cmd = [
        ffmpeg_cmd, "-y",
        "-f", "lavfi",
        "-i", "sine=frequency=300:duration=20.0",
        "-c:a", "pcm_s16le",
        "-ar", "24000",
        str(wav_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return wav_path


def test_build_reference_clip_from_segments(sample_vocals_wav, tmp_path):
    output_clip = tmp_path / "ref_clip.wav"

    segments = [
        Segment(idx=1, start=2.0, end=5.5, src_text="Hello", tgt_text="ہیلو"),
        Segment(idx=2, start=6.0, end=14.0, src_text="Welcome to the lecture.", tgt_text="لیکچر میں خوش آمدید۔"),
        Segment(idx=3, start=14.5, end=19.0, src_text="Let us begin.", tgt_text="آئیے شروع کرتے ہیں۔"),
    ]

    result_path = build_reference_clip(
        vocals_path=sample_vocals_wav,
        segments=segments,
        output_path=output_clip,
        target_duration=12.0
    )

    assert result_path.is_file()
    assert result_path == output_clip
    probe = probe_media_file(result_path)
    # Target duration 12s, extracted slice should be ~12s
    assert abs(probe.duration - 12.0) < 0.5
    assert probe.sample_rate == 24000
    assert probe.channels == 1


def test_build_reference_clip_fallback_short_segments(sample_vocals_wav, tmp_path):
    output_clip = tmp_path / "ref_clip_fallback.wav"

    # Segments all under 2.0s
    segments = [
        Segment(idx=1, start=0.0, end=1.0, src_text="Hi", tgt_text="ہائے"),
        Segment(idx=2, start=1.5, end=2.5, src_text="Yes", tgt_text="ہاں"),
    ]

    result_path = build_reference_clip(
        vocals_path=sample_vocals_wav,
        segments=segments,
        output_path=output_clip,
        target_duration=10.0
    )

    assert result_path.is_file()
    probe = probe_media_file(result_path)
    assert abs(probe.duration - 10.0) < 0.5
