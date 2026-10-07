import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any

from backend.app.core.config import settings
from backend.app.core.logging import logger


class MediaValidationError(Exception):
    """Raised when an ingested media file fails validation."""
    pass


@dataclass
class MediaProbeResult:
    format_name: str
    duration: float
    size_bytes: int
    has_audio: bool
    has_video: bool
    width: Optional[int] = None
    height: Optional[int] = None
    audio_codec: Optional[str] = None
    video_codec: Optional[str] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    streams: List[Dict[str, Any]] = field(default_factory=list)


def probe_media_file(path: Path) -> MediaProbeResult:
    """
    Validates and extracts technical parameters from a media file using ffprobe.
    Enforces format, audio stream presence, duration, and dimension limits.
    """
    if not path.is_file():
        raise MediaValidationError(f"File not found: {path}")

    file_size = path.stat().st_size
    if file_size == 0:
        raise MediaValidationError("File is empty (0 bytes).")

    ffprobe_cmd = settings.get_ffprobe_cmd()
    cmd = [
        ffprobe_cmd,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(path)
    ]

    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    except FileNotFoundError:
        raise MediaValidationError("ffprobe binary is not installed or accessible on system PATH.")

    if res.returncode != 0 or not res.stdout.strip():
        logger.warning(f"ffprobe failed on {path.name}: {res.stderr}")
        raise MediaValidationError("Invalid or corrupted media file. ffprobe could not parse the container.")

    try:
        data = json.loads(res.stdout)
    except json.JSONDecodeError:
        raise MediaValidationError("Failed to parse ffprobe inspection data.")

    fmt = data.get("format", {})
    streams = data.get("streams", [])

    duration_str = fmt.get("duration")
    duration = float(duration_str) if duration_str else 0.0

    audio_stream = None
    video_stream = None

    for s in streams:
        codec_type = s.get("codec_type")
        if codec_type == "audio" and not audio_stream:
            audio_stream = s
        elif codec_type == "video" and not video_stream:
            # Skip attached pictures/thumbnails (e.g. album art in audio)
            disposition = s.get("disposition", {})
            if disposition.get("attached_pic") != 1:
                video_stream = s

    has_audio = audio_stream is not None
    has_video = video_stream is not None

    # Fall back to stream duration if container duration was missing
    if duration <= 0.0:
        if audio_stream and "duration" in audio_stream:
            duration = float(audio_stream["duration"])
        elif video_stream and "duration" in video_stream:
            duration = float(video_stream["duration"])

    # Strict Validation Checks
    if not has_audio:
        raise MediaValidationError("The uploaded file does not contain an audio track. An audio track with spoken speech is required.")

    if duration <= 0.0:
        raise MediaValidationError("Media file has indeterminate or zero duration.")

    max_duration_seconds = settings.MAX_VIDEO_MINUTES * 60
    if duration > max_duration_seconds:
        raise MediaValidationError(
            f"Video duration ({duration / 60:.1f} minutes) exceeds the maximum allowed limit of {settings.MAX_VIDEO_MINUTES} minutes."
        )

    width = int(video_stream["width"]) if (video_stream and "width" in video_stream) else None
    height = int(video_stream["height"]) if (video_stream and "height" in video_stream) else None

    if width and width > settings.MAX_DIMENSION:
        raise MediaValidationError(f"Video width ({width}px) exceeds the maximum allowed limit ({settings.MAX_DIMENSION}px).")
    if height and height > settings.MAX_DIMENSION:
        raise MediaValidationError(f"Video height ({height}px) exceeds the maximum allowed limit ({settings.MAX_DIMENSION}px).")

    return MediaProbeResult(
        format_name=fmt.get("format_name", "unknown"),
        duration=duration,
        size_bytes=file_size,
        has_audio=has_audio,
        has_video=has_video,
        width=width,
        height=height,
        audio_codec=audio_stream.get("codec_name") if audio_stream else None,
        video_codec=video_stream.get("codec_name") if video_stream else None,
        sample_rate=int(audio_stream.get("sample_rate", 0)) if audio_stream else None,
        channels=int(audio_stream.get("channels", 0)) if audio_stream else None,
        streams=streams
    )


def standardize_to_mp4(input_path: Path, output_path: Path) -> Path:
    """
    Ensures the media is packaged as a standard MP4 container with AAC audio and faststart flags.
    Copies video stream without re-encoding when possible; transcodes if necessary.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg_cmd = settings.get_ffmpeg_cmd()

    # Step 1: Probe input to check streams
    probe = probe_media_file(input_path)

    if probe.has_video:
        # Try direct remuxing with stream copy for video
        remux_cmd = [
            ffmpeg_cmd, "-y",
            "-i", str(input_path),
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            str(output_path)
        ]
        res = subprocess.run(remux_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        if res.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
            logger.info(f"Successfully remuxed {input_path.name} to {output_path.name} with video copy.")
            return output_path

        # If remux failed (e.g. incompatible video codec like VP9 in WebM), transcode video to H.264
        logger.info(f"Video stream copy failed; transcoding {input_path.name} to H.264 MP4...")
        transcode_cmd = [
            ffmpeg_cmd, "-y",
            "-i", str(input_path),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            str(output_path)
        ]
        res2 = subprocess.run(transcode_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        if res2.returncode != 0 or not output_path.exists():
            raise MediaValidationError(f"Failed to transcode video to MP4: {res2.stderr}")
        return output_path
    else:
        # Audio-only file: generate a still black background canvas with the audio track
        logger.info(f"Input {input_path.name} is audio-only; generating black video container for lecture pipeline...")
        audio_to_video_cmd = [
            ffmpeg_cmd, "-y",
            "-f", "lavfi", "-i", "color=c=black:s=1280x720:r=25",
            "-i", str(input_path),
            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            "-movflags", "+faststart",
            str(output_path)
        ]
        res = subprocess.run(audio_to_video_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        if res.returncode != 0 or not output_path.exists():
            raise MediaValidationError(f"Failed to package audio into MP4 container: {res.stderr}")
        return output_path
