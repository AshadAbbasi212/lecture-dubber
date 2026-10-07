import pytest
from pathlib import Path
import subprocess

from backend.app.pipeline.timing_fit import (
    calculate_timing_fit,
    apply_audio_time_stretch,
    TimingFitDecision
)
from backend.app.core.config import settings
from backend.app.ingest.media_probe import probe_media_file


def test_timing_fit_exact_match():
    # Ratio 1.0 (exact match)
    decision = calculate_timing_fit(original_duration=5.0, tts_duration=5.0)
    assert decision.status == "exact"
    assert decision.effective_stretch_ratio == 1.0
    assert decision.needs_retranslation is False
    assert decision.borrowed_silence_before == 0.0
    assert decision.borrowed_silence_after == 0.0


def test_timing_fit_mild_stretch():
    # Ratio 1.10 (within 0.85 - 1.15 range)
    decision = calculate_timing_fit(original_duration=5.0, tts_duration=5.5)
    assert decision.status == "stretched"
    assert decision.effective_stretch_ratio == 1.1
    assert decision.needs_retranslation is False
    assert decision.borrowed_silence_before == 0.0
    assert decision.borrowed_silence_after == 0.0

    # Ratio 0.90 (slight stretch/slowdown)
    decision_slow = calculate_timing_fit(original_duration=5.0, tts_duration=4.5)
    assert decision_slow.status == "stretched"
    assert decision_slow.effective_stretch_ratio == 0.9
    assert decision_slow.needs_retranslation is False


def test_timing_fit_silence_borrowing():
    # TTS duration is 6.0s for a 5.0s slot (ratio = 1.20).
    # Stretched at max cap 1.25x -> duration becomes 4.8s, which fits within 5.0s slot.
    # What if TTS duration is 6.5s for 5.0s slot (ratio = 1.30):
    # At 1.25x cap -> stretched duration is 6.5 / 1.25 = 5.2s. Extra time needed = 0.2s.
    decision = calculate_timing_fit(
        original_duration=5.0,
        tts_duration=6.5,
        available_pre_silence=0.2,
        available_post_silence=0.5
    )
    assert decision.status == "borrowed_silence"
    assert decision.effective_stretch_ratio == 1.25
    assert decision.needs_retranslation is False
    # Post-silence borrowed first: 0.2s from post-silence
    assert decision.borrowed_silence_after == 0.2
    assert decision.borrowed_silence_before == 0.0


def test_timing_fit_insufficient_silence_flags_retranslation():
    # TTS duration is 6.5s (ratio 1.30), extra needed is 0.2s, but no silence available
    decision = calculate_timing_fit(
        original_duration=5.0,
        tts_duration=6.5,
        available_pre_silence=0.05,
        available_post_silence=0.05
    )
    assert decision.status == "overshoot_retry"
    assert decision.needs_retranslation is True
    assert "overshoots slot" in decision.retranslation_reason


def test_timing_fit_extreme_overshoot_flags_retranslation():
    # TTS duration 7.5s for 5.0s slot (ratio = 1.50 > 1.35)
    decision = calculate_timing_fit(
        original_duration=5.0,
        tts_duration=7.5,
        available_pre_silence=2.0,
        available_post_silence=2.0
    )
    assert decision.status == "overshoot_retry"
    assert decision.needs_retranslation is True
    assert "overshoots slot" in decision.retranslation_reason


def test_timing_fit_undershoot():
    # TTS is much shorter (2.0s for 4.0s slot, ratio 0.50)
    decision = calculate_timing_fit(
        original_duration=4.0,
        tts_duration=2.0
    )
    assert decision.status == "undershoot_pad"
    assert decision.effective_stretch_ratio == 1.0
    assert decision.needs_retranslation is False
    assert decision.borrowed_silence_after == 2.0


def test_apply_audio_time_stretch(tmp_path):
    # Generate 2.0 second test tone
    input_wav = tmp_path / "in.wav"
    output_wav = tmp_path / "out_fast.wav"

    ffmpeg_cmd = settings.get_ffmpeg_cmd()
    cmd = [
        ffmpeg_cmd, "-y",
        "-f", "lavfi",
        "-i", "sine=frequency=440:duration=2.0",
        "-c:a", "pcm_s16le",
        str(input_wav)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    probe_in = probe_media_file(input_wav)
    assert abs(probe_in.duration - 2.0) < 0.1

    # Speed up 1.25x (duration should become ~1.6s)
    apply_audio_time_stretch(input_wav, output_wav, stretch_ratio=1.25)
    assert output_wav.exists()
    probe_out = probe_media_file(output_wav)
    assert abs(probe_out.duration - 1.6) < 0.15
