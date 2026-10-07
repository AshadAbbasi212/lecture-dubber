import subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
import pytest

from backend.app.core.config import settings
from backend.app.db.models.segment import Segment
from backend.app.pipeline.audio_mixer import assemble_timeline_vocals, mix_vocals_and_background
from backend.app.ingest.media_probe import probe_media_file


@pytest.fixture
def dummy_segment_wavs(tmp_path):
    seg1_path = tmp_path / "seg_0001.wav"
    seg2_path = tmp_path / "seg_0002.wav"

    sr = 44100
    # 2 seconds of 440 Hz
    t1 = np.linspace(0, 2.0, int(2.0 * sr), endpoint=False)
    audio1 = (0.5 * np.sin(2 * np.pi * 440 * t1)).astype(np.float32)
    sf.write(str(seg1_path), np.column_stack([audio1, audio1]), sr)

    # 1.5 seconds of 880 Hz
    t2 = np.linspace(0, 1.5, int(1.5 * sr), endpoint=False)
    audio2 = (0.5 * np.sin(2 * np.pi * 880 * t2)).astype(np.float32)
    sf.write(str(seg2_path), np.column_stack([audio2, audio2]), sr)

    return seg1_path, seg2_path


def test_assemble_timeline_vocals(dummy_segment_wavs, tmp_path):
    seg1_path, seg2_path = dummy_segment_wavs
    output_vocals = tmp_path / "dub_vocals.wav"

    segments = [
        Segment(idx=1, start=1.0, end=3.0, tts_path=str(seg1_path)),
        Segment(idx=2, start=4.0, end=5.5, tts_path=str(seg2_path)),
    ]

    total_duration = 7.0
    assemble_timeline_vocals(segments, total_duration, output_vocals)

    assert output_vocals.is_file()
    probe = probe_media_file(output_vocals)
    assert abs(probe.duration - 7.0) < 0.1
    assert probe.channels == 2
    assert probe.sample_rate == 44100

    # Verify audio content is silent in the first 0.5s, active at 1.5s
    data, sr = sf.read(str(output_vocals))
    assert np.max(np.abs(data[:int(0.5 * sr)])) < 1e-4  # silence before start
    assert np.max(np.abs(data[int(1.2 * sr):int(2.8 * sr)])) > 0.1  # segment 1 active


def test_mix_vocals_and_background_with_ducking(dummy_segment_wavs, tmp_path):
    seg1_path, _ = dummy_segment_wavs
    sr = 44100

    # Create 6-second vocals timeline: silence (0-1s), speech (1-3s), silence (3-6s)
    vocals_wav = tmp_path / "vocals.wav"
    v_data = np.zeros((6 * sr, 2), dtype=np.float32)
    s_data, _ = sf.read(str(seg1_path))
    v_data[1 * sr:3 * sr] = s_data[:2 * sr]
    sf.write(str(vocals_wav), v_data, sr)

    # Create 6-second background noise / music (constant amplitude 0.4)
    bg_wav = tmp_path / "bg.wav"
    t = np.linspace(0, 6.0, 6 * sr, endpoint=False)
    b_data = (0.3 * np.sin(2 * np.pi * 100 * t)).astype(np.float32)
    sf.write(str(bg_wav), np.column_stack([b_data, b_data]), sr)

    output_mix = tmp_path / "dub_mix.wav"
    mix_vocals_and_background(
        dub_vocals_path=vocals_wav,
        background_path=bg_wav,
        output_mix_path=output_mix,
        ducking_db=12.0,
        target_lufs=-16.0
    )

    assert output_mix.is_file()
    probe = probe_media_file(output_mix)
    assert abs(probe.duration - 6.0) < 0.2
    assert probe.sample_rate == 44100
    assert probe.channels == 2
