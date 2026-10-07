import pytest
from backend.app.engines.base import WordTimestamp, TranscriptSegment
from backend.app.engines.asr.segmenter import merge_words_into_sentence_segments


def test_segmenter_punctuation_split():
    words = [
        WordTimestamp("Hello", 0.0, 0.4),
        WordTimestamp("students.", 0.5, 1.2),  # terminal punct
        WordTimestamp("Welcome", 1.5, 2.0),
        WordTimestamp("to", 2.1, 2.3),
        WordTimestamp("the", 2.4, 2.6),
        WordTimestamp("lecture.", 2.7, 3.5),   # terminal punct
    ]
    # min_duration=1.0 so both sentences qualify
    segments = merge_words_into_sentence_segments(words, min_duration=1.0, max_duration=10.0)
    assert len(segments) == 2
    assert segments[0].text == "Hello students."
    assert segments[0].start == 0.0
    assert segments[0].end == 1.2
    assert segments[1].text == "Welcome to the lecture."
    assert segments[1].start == 1.5
    assert segments[1].end == 3.5


def test_segmenter_urdu_punctuation_split():
    words = [
        WordTimestamp("سبق", 0.0, 0.6),
        WordTimestamp("نمبر", 0.7, 1.1),
        WordTimestamp("ایک۔", 1.2, 1.8),  # Urdu full stop '۔'
        WordTimestamp("کیا", 2.0, 2.4),
        WordTimestamp("آپ", 2.5, 2.8),
        WordTimestamp("تیار", 2.9, 3.3),
        WordTimestamp("ہیں؟", 3.4, 3.9),  # Urdu question mark '؟'
    ]
    segments = merge_words_into_sentence_segments(words, min_duration=1.0)
    assert len(segments) == 2
    assert "ایک۔" in segments[0].text
    assert "ہیں؟" in segments[1].text


def test_segmenter_silence_pause_split():
    words = [
        WordTimestamp("Word1", 0.0, 1.0),
        WordTimestamp("Word2", 1.1, 2.2),
        # Big silence pause of 1.3 seconds (> pause_threshold 0.6s)
        WordTimestamp("Word3", 3.5, 4.5),
        WordTimestamp("Word4", 4.6, 5.8),
    ]
    segments = merge_words_into_sentence_segments(words, min_duration=2.0, pause_threshold=0.6)
    assert len(segments) == 2
    assert segments[0].text == "Word1 Word2"
    assert segments[0].end == 2.2
    assert segments[1].text == "Word3 Word4"
    assert segments[1].start == 3.5


def test_segmenter_max_duration_guard():
    # Stream of words without punctuation or pause spanning 20 seconds
    words = [WordTimestamp(f"w_{i}", float(i), float(i) + 0.8) for i in range(20)]
    segments = merge_words_into_sentence_segments(words, min_duration=2.0, max_duration=10.0)
    assert len(segments) >= 2
    for seg in segments:
        duration = seg.end - seg.start
        assert duration <= 11.0, f"Segment exceeded max duration: {duration}"


def test_segmenter_empty_input():
    segments = merge_words_into_sentence_segments([])
    assert segments == []
