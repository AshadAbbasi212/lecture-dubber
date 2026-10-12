import pytest
from backend.app.engines.base import TranscriptSegment
from backend.app.engines.translation.llm_translator import LocalLLMTranslator


def test_translator_context_and_glossary():
    segments = [
        TranscriptSegment(1, 0.0, 4.0, "Welcome to the lecture on computer algorithms."),
        TranscriptSegment(2, 4.5, 9.0, "Today we will analyze time and space complexity."),
    ]
    translator = LocalLLMTranslator()
    results = translator.translate(segments, src_lang="en", tgt_lang="ur")

    assert len(results) == 2
    assert results[0].idx == 1
    assert "الگورتھم" in results[0].tgt_text
    assert results[1].idx == 2
    assert "پیچیدگی" in results[1].tgt_text or "وقت" in results[1].tgt_text


def test_translator_prompt_builder():
    translator = LocalLLMTranslator()
    prompt = translator._build_prompt(
        current_text="Now observe the loop invariant.",
        prev_text="We defined the precondition.",
        next_text="This concludes the proof.",
        src_lang="en",
        tgt_lang="ur",
        target_chars=45,
        glossary={"loop": "لوپ", "proof": "ثبوت"}
    )
    assert "Precondition" in prompt or "precondition" in prompt
    assert "loop invariant" in prompt
    assert "This concludes the proof." in prompt
    assert "لوپ" in prompt
    assert "45 characters" in prompt


def test_validate_script_matches_language():
    from backend.app.engines.translation.llm_translator import validate_script_matches_language

    assert validate_script_matches_language("هذا شرح تعليمي وتوضيح", "ar") is True
    assert validate_script_matches_language("Hello this is English", "ar") is False

    assert validate_script_matches_language("这是关于该主题的讲解", "zh") is True
    assert validate_script_matches_language("Hello this is English", "zh") is False

    assert validate_script_matches_language("Это академическое объяснение", "ru") is True
    assert validate_script_matches_language("Hello this is English", "ru") is False

    assert validate_script_matches_language("यह इस विषय पर व्याख्या है", "hi") is True
    assert validate_script_matches_language("Hello this is English", "hi") is False

    assert validate_script_matches_language("یہ تعلیمی لیکچر ہے", "ur") is True
    assert validate_script_matches_language("This is English", "ur") is False

    assert validate_script_matches_language("Esta es una explicación académica", "es") is True
    assert validate_script_matches_language("هذا شرح", "es") is False


def test_script_gate_prevents_english_leakage_in_arabic():
    translator = LocalLLMTranslator()
    segments = [
        TranscriptSegment(1, 0.0, 3.0, "Some completely unknown phrase without corpus match"),
    ]
    results_ar = translator.translate(segments, src_lang="ur", tgt_lang="ar")
    assert len(results_ar) == 1
    # Arabic result MUST contain Arabic characters and never leak raw English/Latin
    assert any('\u0600' <= c <= '\u06FF' for c in results_ar[0].tgt_text)
    assert not any('a' <= c.lower() <= 'z' for c in results_ar[0].tgt_text)

    # Chinese result MUST contain Chinese characters
    results_zh = translator.translate(segments, src_lang="ur", tgt_lang="zh")
    assert any('\u4E00' <= c <= '\u9FFF' for c in results_zh[0].tgt_text)

