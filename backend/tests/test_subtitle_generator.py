import pytest
from pathlib import Path
from backend.app.pipeline.subtitle_generator import generate_srt, generate_vtt, format_timestamp_srt, format_timestamp_vtt

def test_timestamp_formatting():
    assert format_timestamp_srt(0.0) == "00:00:00,000"
    assert format_timestamp_srt(65.5) == "00:01:05,500"
    assert format_timestamp_vtt(3661.123) == "01:01:01.123"

def test_generate_srt_and_vtt(tmp_path):
    segments = [
        {"idx": 1, "start": 1.0, "end": 4.5, "speaker": "narrator", "tgt_text": "Welcome to Uzbekistan."},
        {"idx": 2, "start": 5.0, "end": 9.0, "speaker": "sheikh_ul_wazaif", "tgt_text": "In the name of Allah."}
    ]

    srt_file = tmp_path / "test.srt"
    vtt_file = tmp_path / "test.vtt"

    generate_srt(segments, srt_file)
    generate_vtt(segments, vtt_file)

    assert srt_file.exists()
    assert vtt_file.exists()

    srt_content = srt_file.read_text(encoding="utf-8")
    assert "00:00:01,000 --> 00:00:04,500" in srt_content
    assert "[Narrator] Welcome to Uzbekistan." in srt_content
    assert "[Sheikh-ul-Wazaif] In the name of Allah." in srt_content

    vtt_content = vtt_file.read_text(encoding="utf-8")
    assert "WEBVTT" in vtt_content
    assert "00:00:01.000 --> 00:00:04.500" in vtt_content
    assert "<v Narrator>Welcome to Uzbekistan." in vtt_content
