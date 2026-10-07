import subprocess
import pytest
from pathlib import Path
from unittest.mock import patch

from backend.app.core.config import settings
from backend.app.ingest.media_probe import (
    probe_media_file,
    standardize_to_mp4,
    MediaValidationError,
    MediaProbeResult
)


def test_probe_valid_media_file(sample_mp4_path):
    result = probe_media_file(sample_mp4_path)
    assert isinstance(result, MediaProbeResult)
    assert result.has_audio is True
    assert result.has_video is True
    assert result.duration > 0.0
    assert result.width == 320
    assert result.height == 240
    assert result.audio_codec == "aac"


def test_probe_corrupted_file(tmp_path):
    corrupt_file = tmp_path / "corrupt.mp4"
    corrupt_file.write_bytes(b"NOT_A_REAL_MEDIA_FILE_HEADER_GARBAGE")

    with pytest.raises(MediaValidationError, match="Invalid or corrupted media file"):
        probe_media_file(corrupt_file)


def test_probe_empty_file(tmp_path):
    empty_file = tmp_path / "empty.mp4"
    empty_file.write_bytes(b"")

    with pytest.raises(MediaValidationError, match="File is empty"):
        probe_media_file(empty_file)


def test_probe_no_audio_stream(tmp_path):
    # Generate a video-only MP4 (no audio stream) using ffmpeg
    no_audio_file = tmp_path / "no_audio.mp4"
    ffmpeg_cmd = settings.get_ffmpeg_cmd()
    cmd = [
        ffmpeg_cmd, "-y",
        "-f", "lavfi", "-i", "color=c=red:s=160x120:d=0.5",
        "-c:v", "libx264", "-preset", "ultrafast",
        str(no_audio_file)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    with pytest.raises(MediaValidationError, match="does not contain an audio track"):
        probe_media_file(no_audio_file)


def test_probe_duration_limit_exceeded(sample_mp4_path):
    # Temporarily set max video minutes to very low value (e.g. 0.005 minutes = 0.3s)
    with patch.object(settings, "MAX_VIDEO_MINUTES", 0.005):
        with pytest.raises(MediaValidationError, match="exceeds the maximum allowed limit"):
            probe_media_file(sample_mp4_path)


def test_probe_dimension_limit_exceeded(sample_mp4_path):
    # Temporarily set MAX_DIMENSION below 320px
    with patch.object(settings, "MAX_DIMENSION", 200):
        with pytest.raises(MediaValidationError, match="exceeds the maximum allowed limit"):
            probe_media_file(sample_mp4_path)


def test_standardize_to_mp4(sample_mp4_path, tmp_path):
    output_path = tmp_path / "standardized.mp4"
    result_path = standardize_to_mp4(sample_mp4_path, output_path)

    assert result_path.exists()
    assert result_path.stat().st_size > 0

    # Probe the result to ensure it is valid faststart mp4
    probe = probe_media_file(result_path)
    assert probe.has_audio is True
    assert probe.has_video is True
    assert probe.duration > 0.0
