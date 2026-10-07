import re
from pathlib import Path
from typing import Dict, Any, Optional

import yt_dlp

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.ingest.media_probe import MediaValidationError


class YouTubeImportError(Exception):
    """Raised when YouTube download fails or violates constraints."""
    pass


YOUTUBE_URL_REGEX = re.compile(
    r"^(https?://)?(www\.|m\.)?(youtube\.com/(watch\?.*v=|embed/|shorts/)|youtu\.be/)([\w-]{11})",
    re.IGNORECASE
)


def is_youtube_url(url: str) -> bool:
    """Verifies if the URL is a recognized YouTube video link."""
    return bool(YOUTUBE_URL_REGEX.search(url))


def extract_youtube_video_id(url: str) -> Optional[str]:
    """Extracts 11-character video ID from YouTube URL."""
    match = YOUTUBE_URL_REGEX.search(url)
    return match.group(5) if match else None


def download_youtube_video(url: str, output_path: Path) -> Dict[str, Any]:
    """
    Downloads a YouTube video to output_path using yt-dlp.
    Enforces feature flag, max duration, format constraints, and outputs MP4.
    MUST be run in worker process, never in the synchronous web request thread.
    """
    if not settings.ENABLE_YOUTUBE_IMPORT:
        raise YouTubeImportError("YouTube import feature is currently disabled by administrator configuration.")

    if not is_youtube_url(url):
        raise YouTubeImportError(f"Provided URL is not a valid YouTube video URL: {url}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_template = str(output_path.parent / "%(id)s.%(ext)s")

    max_duration_seconds = settings.MAX_VIDEO_MINUTES * 60
    max_bytes = settings.MAX_UPLOAD_GB * 1024 * 1024 * 1024

    ydl_opts = {
        "format": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
        "merge_output_format": "mp4",
        "outtmpl": temp_template,
        "max_filesize": max_bytes,
        "quiet": True,
        "no_warnings": True,
        "no_color": True,
        "noplaylist": True,
        "socket_timeout": settings.SSRF_TIMEOUT_SECONDS,
        "prefer_ffmpeg": True,
        "ffmpeg_location": settings.get_ffmpeg_cmd(),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 1. Extract metadata first to validate duration before full download
            info = ydl.extract_info(url, download=False)
            if not info:
                raise YouTubeImportError("Could not retrieve video information from YouTube.")

            duration = info.get("duration", 0)
            if duration and duration > max_duration_seconds:
                raise YouTubeImportError(
                    f"YouTube video duration ({duration/60:.1f} min) exceeds maximum permitted limit of {settings.MAX_VIDEO_MINUTES} minutes."
                )

            # 2. Perform the download
            download_info = ydl.extract_info(url, download=True)
            downloaded_file = Path(ydl.prepare_filename(download_info))

            # If merged format was mp4, check file existence
            if not downloaded_file.exists():
                mp4_cand = downloaded_file.with_suffix(".mp4")
                if mp4_cand.exists():
                    downloaded_file = mp4_cand

            if not downloaded_file.exists():
                raise YouTubeImportError("Downloaded YouTube media file was not found on disk.")

            # Move or rename to final output_path
            if downloaded_file != output_path:
                if output_path.exists():
                    output_path.unlink()
                downloaded_file.replace(output_path)

            logger.info(f"Successfully downloaded YouTube video '{info.get('title')}' to {output_path.name}")

            return {
                "id": info.get("id"),
                "title": info.get("title"),
                "uploader": info.get("uploader"),
                "duration": duration,
                "view_count": info.get("view_count"),
                "output_path": str(output_path),
            }

    except yt_dlp.utils.DownloadError as e:
        raise YouTubeImportError(f"yt-dlp download failed: {e}")
    except Exception as e:
        if isinstance(e, YouTubeImportError):
            raise
        raise YouTubeImportError(f"Unexpected error importing YouTube video: {e}")
