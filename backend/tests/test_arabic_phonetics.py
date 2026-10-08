import pytest
from backend.app.engines.tts.arabic_phonetics import normalize_phonetics_for_tts

def test_surah_names_normalization():
    input_text = "In Surah Al-Baqarah and Surah Al-Ikhlas, there are great lessons."
    output = normalize_phonetics_for_tts(input_text)
    assert "Soorah Al Bakarah" in output
    assert "Soorah Al Ikhlaas" in output

def test_islamic_lexicon_normalization():
    input_text = "Sheikh-ul-Wazaif presented Tasbeeh and Wazaif for Ubqari."
    output = normalize_phonetics_for_tts(input_text)
    assert "Shaykh ul Wazaayif" in output
    assert "Tas-beeh" in output
    assert "Wazaayif" in output
    assert "Ub-qaree" in output

def test_hyphenated_articles():
    input_text = "Al-Kahf and An-Nas"
    output = normalize_phonetics_for_tts(input_text)
    assert "Al Kahf" in output
    assert "An Naas" in output
