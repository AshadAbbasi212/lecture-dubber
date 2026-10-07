from typing import Tuple

# Average speaking rates in educational speech (characters per second including spaces)
# English: ~13-16 chars/sec (~140 words/min)
# Urdu: ~10-13 chars/sec (~120 words/min)
CHARS_PER_SECOND = {
    "en": 14.0,
    "ur": 11.0,
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
