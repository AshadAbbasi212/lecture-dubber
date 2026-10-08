import subprocess
from pathlib import Path
from typing import Optional

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.ingest.media_probe import probe_media_file, MediaProbeResult, MediaValidationError


class AVSyncDriftError(ValueError):
    """Raised when audio-video duration drift exceeds acceptable tolerance."""
    pass


def mux_video_and_audio(
    video_path: Path,
    audio_path: Path,
    output_path: Path,
    target_lang: str = "ur",
    tolerance_seconds: float = 2.0,
    title: Optional[str] = None,
    subtitle_path: Optional[Path] = None
) -> MediaProbeResult:
    """
    Replaces the original video's audio with the dubbed audio mix (dub_mix.wav).
    Copies the video stream without re-encoding where possible.
    Optionally embeds soft subtitles (SRT) into the MP4 container for closed caption toggle.
    Verifies A/V duration match and sync tolerance.
    Writes final.mp4 with AI-dubbed metadata tags.
    """
    if not video_path.is_file():
        raise FileNotFoundError(f"Source video file not found: {video_path}")
    if not audio_path.is_file():
        raise FileNotFoundError(f"Dubbed audio file not found: {audio_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg_cmd = settings.get_ffmpeg_cmd()

    # Step 1: Probe both files to verify duration match and A/V sync
    v_probe = probe_media_file(video_path)
    a_probe = probe_media_file(audio_path)

    drift = abs(v_probe.duration - a_probe.duration)
    # Dynamic tolerance: at least tolerance_seconds, or 5% of lecture duration for long lectures
    effective_tolerance = max(tolerance_seconds, 0.05 * v_probe.duration)

    if drift > effective_tolerance:
        raise AVSyncDriftError(
            f"Audio-video sync drift ({drift:.2f}s) exceeded tolerance ({effective_tolerance:.2f}s). "
            f"Original video duration: {v_probe.duration:.2f}s, Dubbed audio duration: {a_probe.duration:.2f}s."
        )

    logger.info(
        f"A/V sync verified for mux: video={v_probe.duration:.2f}s, audio={a_probe.duration:.2f}s, "
        f"drift={drift:.2f}s (tolerance={effective_tolerance:.2f}s)"
    )

    doc_title = title or f"Lecture Dubber - Dubbed ({target_lang})"
    has_sub = subtitle_path is not None and Path(subtitle_path).is_file()

    # Step 2: Try direct stream copy for video stream (-c:v copy)
    cmd_copy = [
        ffmpeg_cmd, "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
    ]
    if has_sub:
        cmd_copy.extend(["-i", str(subtitle_path)])

    cmd_copy.extend([
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
    ])
    if has_sub:
        cmd_copy.extend([
            "-c:s", "mov_text",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-map", "2:0",
            "-metadata:s:s:0", f"language={target_lang}",
            "-metadata:s:s:0", "title=Closed Captions (CC)"
        ])
    else:
        cmd_copy.extend([
            "-map", "0:v:0",
            "-map", "1:a:0",
        ])

    cmd_copy.extend([
        "-shortest",
        "-movflags", "+faststart",
        "-metadata", f"title={doc_title}",
        "-metadata", "comment=AI Dubbed with Lecture Dubber (Local AI Platform)",
        "-metadata", "service_name=Lecture Dubber",
        "-metadata:s:a:0", f"language={target_lang}",
        "-metadata:s:a:0", f"title=Dubbed Speech ({target_lang})",
        str(output_path)
    ])

    res = subprocess.run(cmd_copy, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)

    if res.returncode != 0 or not output_path.exists() or output_path.stat().st_size == 0:
        logger.warning(f"Video stream copy failed ({res.stderr[:200]}); falling back to x264 transcode.")
        # Fallback: re-encode video stream to ensure 100% compatibility
        cmd_transcode = [
            ffmpeg_cmd, "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
        ]
        if has_sub:
            cmd_transcode.extend(["-i", str(subtitle_path)])

        cmd_transcode.extend([
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "22",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "44100",
        ])
        if has_sub:
            cmd_transcode.extend([
                "-c:s", "mov_text",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-map", "2:0",
                "-metadata:s:s:0", f"language={target_lang}",
                "-metadata:s:s:0", "title=Closed Captions (CC)"
            ])
        else:
            cmd_transcode.extend([
                "-map", "0:v:0",
                "-map", "1:a:0",
            ])

        cmd_transcode.extend([
            "-shortest",
            "-movflags", "+faststart",
            "-metadata", f"title={doc_title}",
            "-metadata", "comment=AI Dubbed with Lecture Dubber (Local AI Platform)",
            "-metadata", "service_name=Lecture Dubber",
            "-metadata:s:a:0", f"language={target_lang}",
            "-metadata:s:a:0", f"title=Dubbed Speech ({target_lang})",
            str(output_path)
        ])
        res_transcode = subprocess.run(cmd_transcode, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        if res_transcode.returncode != 0 or not output_path.exists() or output_path.stat().st_size == 0:
            raise MediaValidationError(f"Failed to mux final video: {res_transcode.stderr}")

    final_probe = probe_media_file(output_path)
    if not final_probe.has_video or not final_probe.has_audio:
        raise MediaValidationError(f"Muxed video missing streams: has_video={final_probe.has_video}, has_audio={final_probe.has_audio}")

    logger.info(f"Muxed final video successfully: {output_path.name} ({final_probe.duration:.2f}s, {final_probe.size_bytes} bytes)")
    return final_probe


def export_dub_mp3(audio_wav_path: Path, output_mp3_path: Path) -> Path:
    """
    Exports the dubbed audio mix to an MP3 file (192 kbps stereo) for audio-only downloads.
    """
    if not audio_wav_path.is_file():
        raise FileNotFoundError(f"Audio mix WAV not found: {audio_wav_path}")

    output_mp3_path.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg_cmd = settings.get_ffmpeg_cmd()

    cmd = [
        ffmpeg_cmd, "-y",
        "-i", str(audio_wav_path),
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        "-ar", "44100",
        str(output_mp3_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    if res.returncode != 0 or not output_mp3_path.exists() or output_mp3_path.stat().st_size == 0:
        raise MediaValidationError(f"Failed to export dub MP3: {res.stderr}")

    return output_mp3_path
