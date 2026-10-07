import subprocess
from pathlib import Path
from typing import List, Optional

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.db.models.segment import Segment
from backend.app.ingest.media_probe import probe_media_file, MediaValidationError


def build_reference_clip(
    vocals_path: Path,
    segments: List[Segment],
    output_path: Path,
    target_duration: float = 15.0
) -> Path:
    """
    Extracts a clean, normalized reference voice clip (10 to 30 seconds) from vocals.wav
    using segment timestamps. Normalizes loudness to -20 LUFS.
    """
    if not vocals_path.is_file():
        raise FileNotFoundError(f"Vocals file not found: {vocals_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg_cmd = settings.get_ffmpeg_cmd()

    # Find the best contiguous range of segments
    best_start = 0.0
    best_end = 0.0
    accumulated_duration = 0.0

    # Look for segments with duration between 2.5s and 12s (ideal speech sentences)
    candidate_segments = [s for s in segments if (s.end - s.start) >= 2.0]

    if candidate_segments:
        # Pick the segment with the cleanest duration or combine adjacent
        for i, seg in enumerate(candidate_segments):
            dur = seg.end - seg.start
            if dur >= target_duration:
                best_start = seg.start
                best_end = seg.start + target_duration
                break
            elif (i + 1 < len(candidate_segments)) and (candidate_segments[i + 1].start - seg.end < 1.0):
                # Adjacent segments close together
                comb_dur = candidate_segments[i + 1].end - seg.start
                if comb_dur >= target_duration:
                    best_start = seg.start
                    best_end = min(candidate_segments[i + 1].end, seg.start + target_duration)
                    break

        if best_end <= best_start:
            # Fall back to first available candidate segment
            best_start = candidate_segments[0].start
            best_end = candidate_segments[0].end
    else:
        # Fall back to first 15 seconds of vocals.wav
        probe = probe_media_file(vocals_path)
        best_start = 0.0
        best_end = min(probe.duration, target_duration)

    slice_duration = max(best_end - best_start, 1.0)
    logger.info(f"Extracting reference voice clip: {best_start:.2f}s to {best_end:.2f}s ({slice_duration:.2f}s) from {vocals_path.name}")

    # Extract slice with loudnorm
    cmd = [
        ffmpeg_cmd, "-y",
        "-ss", str(best_start),
        "-t", str(slice_duration),
        "-i", str(vocals_path),
        "-vn",
        "-ac", "1",
        "-ar", "24000",
        "-af", "loudnorm=I=-20:TP=-2:LRA=7",
        str(output_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    if res.returncode != 0 or not output_path.exists() or output_path.stat().st_size == 0:
        raise MediaValidationError(f"Failed to generate reference clip: {res.stderr}")

    return output_path
