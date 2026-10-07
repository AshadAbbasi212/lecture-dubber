import subprocess
from pathlib import Path
from typing import Tuple

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.ingest.media_probe import MediaValidationError


def extract_audio_tracks(source_mp4: Path, out_dir: Path) -> Tuple[Path, Path]:
    """
    Extracts audio from source.mp4:
    1. original.wav: 44.1 kHz, stereo PCM 16-bit (for background mixing and reference).
    2. asr_16k.wav: 16 kHz, mono PCM 16-bit (optimized for Whisper ASR processing).
    Returns (original_wav_path, asr_wav_path).
    """
    if not source_mp4.is_file():
        raise FileNotFoundError(f"Source video file not found: {source_mp4}")

    out_dir.mkdir(parents=True, exist_ok=True)
    original_wav = out_dir / "original.wav"
    asr_wav = out_dir / "asr_16k.wav"
    ffmpeg_cmd = settings.get_ffmpeg_cmd()

    # 1. Extract original 44.1 kHz stereo audio
    cmd_original = [
        ffmpeg_cmd, "-y",
        "-i", str(source_mp4),
        "-vn",
        "-ac", "2",
        "-ar", "44100",
        "-c:a", "pcm_s16le",
        str(original_wav)
    ]
    res_orig = subprocess.run(cmd_original, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    if res_orig.returncode != 0 or not original_wav.exists() or original_wav.stat().st_size == 0:
        raise MediaValidationError(f"Failed to extract original.wav: {res_orig.stderr}")

    # 2. Extract 16 kHz mono audio for ASR
    cmd_asr = [
        ffmpeg_cmd, "-y",
        "-i", str(source_mp4),
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-c:a", "pcm_s16le",
        str(asr_wav)
    ]
    res_asr = subprocess.run(cmd_asr, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    if res_asr.returncode != 0 or not asr_wav.exists() or asr_wav.stat().st_size == 0:
        raise MediaValidationError(f"Failed to extract asr_16k.wav: {res_asr.stderr}")

    logger.info(f"Extracted audio tracks for {source_mp4.name}: original.wav ({original_wav.stat().st_size} bytes), asr_16k.wav ({asr_wav.stat().st_size} bytes)")
    return original_wav, asr_wav
