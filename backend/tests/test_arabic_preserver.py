import pytest
from backend.app.engines.translation.arabic_preserver import is_sacred_arabic_content, should_preserve_untranslated

def test_quranic_verse_detection():
    verse = "بسم الله الرحمن الرحيم الحمد لله رب العالمين"
    is_sacred, reason = is_sacred_arabic_content(verse)
    assert is_sacred is True
    assert should_preserve_untranslated(verse) is True

def test_hadith_formula_detection():
    hadith = "قال رسول الله صلى الله عليه وسلم: خيركم من تعلم القرآن وعلمه"
    is_sacred, reason = is_sacred_arabic_content(hadith)
    assert is_sacred is True
    assert should_preserve_untranslated(hadith) is True

def test_vocalized_arabic():
    vocalized = "إِنَّا فَتَحْنَا لَكَ فَتْحًا مُبِينًا"
    is_sacred, reason = is_sacred_arabic_content(vocalized)
    assert is_sacred is True

def test_ordinary_urdu_not_flagged():
    urdu_text = "آج کے اس سبق میں ہم ازبکستان کے تاریخی شہروں کا سفر کریں گے۔"
    is_sacred, reason = is_sacred_arabic_content(urdu_text)
    assert is_sacred is False
    assert should_preserve_untranslated(urdu_text) is False
