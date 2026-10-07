import pytest
from pathlib import Path
from backend.app.pipeline.audio_extractor import extract_audio_tracks
from backend.app.ingest.media_probe import probe_media_file


def test_audio_extractor(sample_mp4_path, tmp_path):
    out_dir = tmp_path / "audio_out"
    orig_wav, asr_wav = extract_audio_tracks(sample_mp4_path, out_dir)

    assert orig_wav.exists()
    assert asr_wav.exists()
    assert orig_wav.stat().st_size > 0
    assert asr_wav.stat().st_size > 0

    # Probe original.wav (44.1 kHz, 2 channels)
    probe_orig = probe_media_file(orig_wav)
    assert probe_orig.has_audio is True
    assert probe_orig.sample_rate == 44100
    assert probe_orig.channels == 2

    # Probe asr_16k.wav (16 kHz, 1 channel)
    probe_asr = probe_media_file(asr_wav)
    assert probe_asr.has_audio is True
    assert probe_asr.sample_rate == 16000
    assert probe_asr.channels == 1
