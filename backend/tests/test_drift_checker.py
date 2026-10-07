import pytest
from backend.app.engines.translation.drift_checker import check_meaning_drift


def test_drift_checker_valid_urdu():
    src = "Welcome to the algorithm class."
    tgt = "الگورتھم کی کلاس میں خوش آمدید۔"
    flagged, reason = check_meaning_drift(src, tgt, "en", "ur")
    assert flagged is False
    assert reason is None


def test_drift_checker_missing_urdu_script():
    src = "Welcome to the algorithm class."
    # Output was left in English
    tgt = "Welcome to the class."
    flagged, reason = check_meaning_drift(src, tgt, "en", "ur")
    assert flagged is True
    assert "missing Urdu script" in reason


def test_drift_checker_empty_translation():
    flagged, reason = check_meaning_drift("Hello", "   ", "en", "ur")
    assert flagged is True
    assert "Empty" in reason


def test_drift_checker_repetition_loop():
    src = "Let us examine the loop function."
    tgt = "یہ لوپ لوپ لوپ لوپ ہے"
    flagged, reason = check_meaning_drift(src, tgt, "en", "ur")
    assert flagged is True
    assert "loop detected" in reason.lower()


def test_drift_checker_length_anomaly():
    src = "This is a very long and detailed lecture sentence covering multiple principles of computation."
    # Suspiciously truncated output (e.g. 2 chars)
    tgt = "جی"
    flagged, reason = check_meaning_drift(src, tgt, "en", "ur")
    assert flagged is True
    assert "short" in reason.lower()


def test_drift_checker_glossary_discrepancy():
    src = "We study the algorithm efficiency."
    tgt = "ہم طریقہ کار کی کارکردگی کا مطالعہ کرتے ہیں۔"  # Missing 'الگورتھم'
    glossary = {"algorithm": "الگورتھم"}
    flagged, reason = check_meaning_drift(src, tgt, "en", "ur", glossary=glossary)
    assert flagged is True
    assert "Glossary term discrepancy" in reason
