import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from backend.app.core.config import settings
from backend.app.ingest.youtube import (
    is_youtube_url,
    extract_youtube_video_id,
    download_youtube_video,
    YouTubeImportError,
)


def test_is_youtube_url():
    valid_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "http://youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
        "https://www.youtube.com/shorts/dQw4w9WgXcQ",
    ]
    for url in valid_urls:
        assert is_youtube_url(url) is True, f"URL {url} should be recognized as YouTube"

    invalid_urls = [
        "https://vimeo.com/12345678",
        "https://example.com/video.mp4",
        "https://notyoutube.com/watch?v=12345",
    ]
    for url in invalid_urls:
        assert is_youtube_url(url) is False, f"URL {url} should not be recognized as YouTube"


def test_extract_youtube_video_id():
    assert extract_youtube_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_youtube_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_youtube_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_youtube_video_id("https://example.com") is None


def test_youtube_feature_flag_disabled(tmp_path):
    with patch.object(settings, "ENABLE_YOUTUBE_IMPORT", False):
        with pytest.raises(YouTubeImportError, match="disabled"):
            download_youtube_video("https://www.youtube.com/watch?v=dQw4w9WgXcQ", tmp_path / "out.mp4")


@patch("yt_dlp.YoutubeDL")
def test_youtube_duration_limit_exceeded(mock_ydl_cls, tmp_path):
    mock_ydl = MagicMock()
    mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

    # Video duration exceeds settings.MAX_VIDEO_MINUTES (e.g. 10 hours)
    mock_ydl.extract_info.return_value = {
        "id": "dQw4w9WgXcQ",
        "title": "10 Hour Lecture",
        "duration": 36000,  # 10 hours
        "uploader": "LongUploader"
    }

    with pytest.raises(YouTubeImportError, match="exceeds maximum permitted limit"):
        download_youtube_video("https://www.youtube.com/watch?v=dQw4w9WgXcQ", tmp_path / "out.mp4")


@patch("yt_dlp.YoutubeDL")
def test_youtube_download_successful(mock_ydl_cls, tmp_path, sample_mp4_path):
    mock_ydl = MagicMock()
    mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

    target_file = tmp_path / "downloaded.mp4"

    def fake_extract_info(url, download=False):
        if download:
            # Simulate file downloaded
            import shutil
            shutil.copy(sample_mp4_path, target_file)
            return {"id": "dQw4w9WgXcQ", "title": "Math 101", "duration": 1.0, "uploader": "Prof"}
        return {"id": "dQw4w9WgXcQ", "title": "Math 101", "duration": 1.0, "uploader": "Prof"}

    mock_ydl.extract_info.side_effect = fake_extract_info
    mock_ydl.prepare_filename.return_value = str(target_file)

    res = download_youtube_video("https://www.youtube.com/watch?v=dQw4w9WgXcQ", target_file)
    assert res["id"] == "dQw4w9WgXcQ"
    assert res["title"] == "Math 101"
    assert target_file.exists()
