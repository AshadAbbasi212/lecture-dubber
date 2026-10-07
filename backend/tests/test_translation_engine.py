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
