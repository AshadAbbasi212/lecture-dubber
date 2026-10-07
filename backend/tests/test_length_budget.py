import pytest
from backend.app.engines.translation.length_budget import compute_length_budget, is_over_length_budget


def test_compute_length_budget():
    duration = 5.0  # 5 seconds
    target_ur, max_ur = compute_length_budget(duration, target_lang="ur")
    # At 11.0 chars/sec: target ~ 55, max (+15%) ~ 63
    assert target_ur == 55
    assert max_ur == int(55 * 1.15)
    assert max_ur > target_ur

    target_en, max_en = compute_length_budget(duration, target_lang="en")
    # At 14.0 chars/sec: target ~ 70, max (+15%) ~ 80
    assert target_en == 70
    assert max_en == int(70 * 1.15)


def test_is_over_length_budget():
    duration = 3.0  # target: 33 chars, max: 37 chars
    short_text = "آج کا سبق بہت اہم ہے۔"  # 21 chars
    assert is_over_length_budget(short_text, duration, "ur") is False

    long_text = "آج کا سبق بہت زیادہ اہم ہے اور ہم اس میں کمپیوٹر کی تمام باتوں کو تفصیل کے ساتھ سمجھیں گے۔"  # 89 chars
    assert is_over_length_budget(long_text, duration, "ur") is True
