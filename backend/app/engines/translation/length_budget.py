from typing import Tuple

# Average speaking rates in educational speech (characters per second including spaces)
# Chinese characters: ~6-7 chars/sec (ideograms)
# Romance languages (Spanish, Italian, Portuguese): ~15-16 chars/sec
# Germanic & Slavic (German, Russian): ~13-14 chars/sec
# Indic & Semitic (Arabic, Hindi, Urdu): ~11-12.5 chars/sec
CHARS_PER_SECOND = {
    "en": 14.0,
    "es": 15.5,
    "ar": 12.0,
    "zh": 6.5,
    "ru": 13.5,
    "ur": 11.0,
    "fr": 14.5,
    "de": 13.0,
    "hi": 12.5,
    "pt": 15.0,
    "it": 15.5,
    "tr": 13.5,
}


def compute_length_budget(duration: float, target_lang: str = "ur") -> Tuple[int, int]:
    """
    Computes (target_chars, max_tolerated_chars) for a segment given its duration in seconds.
    The upper tolerance is +15% per PIPELINE.md Stage 5 specification.
    """
    rate = CHARS_PER_SECOND.get(target_lang, 12.0)
    target_chars = max(int(duration * rate), 8)
    max_tolerated_chars = int(target_chars * 1.15)
    return target_chars, max_tolerated_chars


def is_over_length_budget(text: str, duration: float, target_lang: str = "ur") -> bool:
    """Checks if the translation exceeds the +15% length tolerance limit."""
    _, max_allowed = compute_length_budget(duration, target_lang)
    return len(text.strip()) > max_allowed
