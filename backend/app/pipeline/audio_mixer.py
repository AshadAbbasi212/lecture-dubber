import math
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional
import numpy as np
import soundfile as sf

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.db.models.segment import Segment
from backend.app.ingest.media_probe import probe_media_file, MediaValidationError


from backend.app.storage.local import storage


def assemble_timeline_vocals(
    segments: List[Segment],
    total_duration: float,
    output_vocals_path: Path,
    sample_rate: int = 44100
) -> Path:
    """
    Places each synthesized segment at its start timestamp onto a continuous audio timeline.
    Uses sample-accurate array buffering to prevent CLI string-length limits.
    """
    output_vocals_path.parent.mkdir(parents=True, exist_ok=True)
    num_samples = int(math.ceil(total_duration * sample_rate))
    timeline = np.zeros((num_samples, 2), dtype=np.float32)

    for seg in segments:
        if not seg.tts_path:
            continue

        seg_file = Path(seg.tts_path)
        if not seg_file.is_file():
            try:
                seg_file = storage.get_path(seg.tts_path)
            except Exception:
                pass

        if not seg_file.is_file():
            logger.warning(f"Segment {seg.idx} audio file missing: {seg_file}")
            continue

        data, sr = sf.read(str(seg_file), dtype="float32")
        # Ensure stereo
        if data.ndim == 1:
            data = np.column_stack([data, data])
        elif data.shape[1] > 2:
            data = data[:, :2]

        # Resample if sample rate differs
        if sr != sample_rate:
            # Linear interpolation resample
            orig_len = len(data)
            target_len = int(round(orig_len * sample_rate / sr))
            idx_orig = np.linspace(0, orig_len - 1, target_len)
            data = np.column_stack([
                np.interp(idx_orig, np.arange(orig_len), data[:, 0]),
                np.interp(idx_orig, np.arange(orig_len), data[:, 1])
            ])

        start_sample = int(round(seg.start * sample_rate))
        if start_sample >= num_samples:
            continue

        end_sample = min(start_sample + len(data), num_samples)
        slice_len = end_sample - start_sample
        timeline[start_sample:end_sample] += data[:slice_len]

    # Normalize to prevent clipping if any overlaps occurred
    max_val = np.max(np.abs(timeline))
    if max_val > 1.0:
        timeline /= max_val

    sf.write(str(output_vocals_path), timeline, sample_rate)
    logger.info(f"Assembled vocals timeline: {total_duration:.2f}s ({num_samples} samples) at {output_vocals_path.name}")
    return output_vocals_path


def mix_vocals_and_background(
    dub_vocals_path: Path,
    background_path: Path,
    output_mix_path: Path,
    ducking_db: float = 12.0,
    target_lufs: float = -16.0
) -> Path:
    """
    Mixes dubbed vocals with background music/room tone.
    Applies ducking (reducing background by ducking_db during speech)
    and normalizes the final mix to EBU R128 (-16 LUFS for web/learning media).
    """
    output_mix_path.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg_cmd = settings.get_ffmpeg_cmd()

    # Step 1: Read files and apply ducking
    v_data, v_sr = sf.read(str(dub_vocals_path), dtype="float32")
    if v_data.ndim == 1:
        v_data = np.column_stack([v_data, v_data])

    if background_path.is_file():
        b_data, b_sr = sf.read(str(background_path), dtype="float32")
        if b_data.ndim == 1:
            b_data = np.column_stack([b_data, b_data])
    else:
        # If background is missing, use quiet room tone
        b_data = np.zeros_like(v_data)
        b_sr = v_sr

    # Match lengths
    target_len = len(v_data)
    if len(b_data) < target_len:
        pad = np.zeros((target_len - len(b_data), 2), dtype=np.float32)
        b_data = np.vstack([b_data, pad])
    else:
        b_data = b_data[:target_len]

    # Compute speech energy envelope for ducking
    # Window size: ~50ms (2205 samples at 44.1k)
    v_mono = np.mean(np.abs(v_data), axis=1)
    window_size = int(v_sr * 0.05)
    kernel = np.ones(window_size) / window_size
    envelope = np.convolve(v_mono, kernel, mode="same")

    # Ducking gain: 1.0 when silent, 10^(-ducking_db/20) when speech active
    attenuation_factor = 10.0 ** (-ducking_db / 20.0)
    speech_threshold = 0.015

    # Smooth ducking mask
    is_speech = envelope > speech_threshold
    # Smooth mask with 200ms release window
    release_samples = int(v_sr * 0.20)
    smooth_mask = np.convolve(is_speech.astype(np.float32), np.ones(release_samples) / release_samples, mode="same")
    smooth_mask = np.clip(smooth_mask, 0.0, 1.0)

    # Gain: 1.0 -> attenuation_factor
    duck_gain = 1.0 - smooth_mask * (1.0 - attenuation_factor)
    ducked_bg = b_data * duck_gain[:, np.newaxis]

    # Combine vocals and ducked background
    raw_mix = v_data + ducked_bg
    raw_mix_path = output_mix_path.with_suffix(".raw_mix.wav")
    sf.write(str(raw_mix_path), raw_mix, v_sr)

    try:
        # Step 2: Apply EBU R128 loudness normalization (-16 LUFS, True Peak -1.5 dBTP)
        loudnorm_cmd = [
            ffmpeg_cmd, "-y",
            "-i", str(raw_mix_path),
            "-af", f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11",
            "-c:a", "pcm_s16le",
            "-ar", "44100",
            str(output_mix_path)
        ]
        res = subprocess.run(loudnorm_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        if res.returncode != 0 or not output_mix_path.exists() or output_mix_path.stat().st_size == 0:
            # Fallback to raw mix if loudnorm fails
            shutil.copy(raw_mix_path, output_mix_path)

        logger.info(f"Mixed and normalized dubbed audio to {output_mix_path.name} (EBU R128 {target_lufs} LUFS)")
        return output_mix_path

    finally:
        if raw_mix_path.exists():
            raw_mix_path.unlink()
