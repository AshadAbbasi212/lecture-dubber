import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.ingest.media_probe import probe_media_file, MediaValidationError


@dataclass
class TimingFitDecision:
    raw_ratio: float
    effective_stretch_ratio: float
    borrowed_silence_before: float
    borrowed_silence_after: float
    needs_retranslation: bool
    retranslation_reason: Optional[str]
    status: str  # "exact", "stretched", "borrowed_silence", "overshoot_retry", "undershoot_pad"


def calculate_timing_fit(
    original_duration: float,
    tts_duration: float,
    available_pre_silence: float = 0.0,
    available_post_silence: float = 0.0
) -> TimingFitDecision:
    """
    Computes time-stretching and silence borrowing decisions to fit TTS audio
    into original speech segments per PIPELINE.md Stage 7 rules:
    - ratio = tts_duration / original_duration
    - Mild ratio (0.85 to 1.15): standard time-stretch.
    - Moderate ratio (1.15 to 1.35): borrow adjacent silence with capped stretch (<= 1.25).
    - Extreme ratio (> 1.35): flag for shorter retranslation retry.
    """
    if original_duration <= 0.0 or tts_duration <= 0.0:
        return TimingFitDecision(
            raw_ratio=1.0,
            effective_stretch_ratio=1.0,
            borrowed_silence_before=0.0,
            borrowed_silence_after=0.0,
            needs_retranslation=False,
            retranslation_reason=None,
            status="exact"
        )

    raw_ratio = tts_duration / original_duration

    # Case 1: Almost exact duration match (+/- 3%)
    if 0.97 <= raw_ratio <= 1.03:
        return TimingFitDecision(
            raw_ratio=round(raw_ratio, 3),
            effective_stretch_ratio=1.0,
            borrowed_silence_before=0.0,
            borrowed_silence_after=0.0,
            needs_retranslation=False,
            retranslation_reason=None,
            status="exact"
        )

    # Case 2: Standard stretch range (0.85 <= ratio <= 1.15)
    if 0.85 <= raw_ratio <= 1.15:
        return TimingFitDecision(
            raw_ratio=round(raw_ratio, 3),
            effective_stretch_ratio=round(raw_ratio, 3),
            borrowed_silence_before=0.0,
            borrowed_silence_after=0.0,
            needs_retranslation=False,
            retranslation_reason=None,
            status="stretched"
        )

    # Case 3: Overshoot requiring silence borrowing (1.15 < ratio <= 1.35)
    if 1.15 < raw_ratio <= 1.35:
        max_stretch_cap = 1.25  # Never stretch audio beyond 1.25x to avoid robotic voices
        stretched_duration = tts_duration / max_stretch_cap
        extra_time_needed = max(0.0, stretched_duration - original_duration)

        total_available_silence = available_pre_silence + available_post_silence

        if extra_time_needed <= total_available_silence:
            # Borrow from post-silence first, then pre-silence
            borrow_post = min(available_post_silence, extra_time_needed)
            remaining = extra_time_needed - borrow_post
            borrow_pre = min(available_pre_silence, remaining)

            return TimingFitDecision(
                raw_ratio=round(raw_ratio, 3),
                effective_stretch_ratio=max_stretch_cap,
                borrowed_silence_before=round(borrow_pre, 3),
                borrowed_silence_after=round(borrow_post, 3),
                needs_retranslation=False,
                retranslation_reason=None,
                status="borrowed_silence"
            )

    # Case 4: Severe overshoot (> 1.35 or not enough silence)
    if raw_ratio > 1.15:
        return TimingFitDecision(
            raw_ratio=round(raw_ratio, 3),
            effective_stretch_ratio=1.25,
            borrowed_silence_before=0.0,
            borrowed_silence_after=0.0,
            needs_retranslation=True,
            retranslation_reason=f"TTS duration ({tts_duration:.1f}s) overshoots slot ({original_duration:.1f}s) by {int((raw_ratio - 1)*100)}%",
            status="overshoot_retry"
        )

    # Case 5: Undershoot (audio shorter than slot, ratio < 0.85)
    return TimingFitDecision(
        raw_ratio=round(raw_ratio, 3),
        effective_stretch_ratio=1.0,
        borrowed_silence_before=0.0,
        borrowed_silence_after=round(original_duration - tts_duration, 3),
        needs_retranslation=False,
        retranslation_reason=None,
        status="undershoot_pad"
    )


def apply_audio_time_stretch(input_wav: Path, output_wav: Path, stretch_ratio: float) -> Path:
    """
    Stretches audio timing using FFmpeg rubberband or atempo filter.
    Note: stretch_ratio > 1.0 means original speech is sped up (higher tempo),
    so duration becomes shorter.
    """
    if not input_wav.is_file():
        raise FileNotFoundError(f"Input audio for time stretching not found: {input_wav}")

    output_wav.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg_cmd = settings.get_ffmpeg_cmd()

    if abs(stretch_ratio - 1.0) < 0.01:
        # No stretch needed, copy file
        import shutil
        shutil.copy(input_wav, output_wav)
        return output_wav

    # In ffmpeg atempo: atempo = tempo_factor (>1 means faster/shorter)
    # Clamp stretch ratio between 0.5 and 2.0
    tempo = max(0.5, min(2.0, stretch_ratio))

    # Try rubberband first, fallback to atempo
    filter_str = f"rubberband=tempo={tempo}"

    cmd = [
        ffmpeg_cmd, "-y",
        "-i", str(input_wav),
        "-filter:a", filter_str,
        str(output_wav)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)

    if res.returncode != 0 or not output_wav.exists() or output_wav.stat().st_size == 0:
        # Fallback to standard atempo filter
        cmd_atempo = [
            ffmpeg_cmd, "-y",
            "-i", str(input_wav),
            "-filter:a", f"atempo={tempo}",
            str(output_wav)
        ]
        res2 = subprocess.run(cmd_atempo, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        if res2.returncode != 0 or not output_wav.exists():
            raise MediaValidationError(f"Failed to time-stretch audio: {res2.stderr}")

    return output_wav
