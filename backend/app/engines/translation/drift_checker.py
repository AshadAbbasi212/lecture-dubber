import re
from typing import Tuple, Optional, Dict

URDU_UNICODE_PATTERN = re.compile(r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]")


def check_meaning_drift(
    src_text: str,
    tgt_text: str,
    src_lang: str,
    tgt_lang: str,
    glossary: Optional[Dict[str, str]] = None
) -> Tuple[bool, Optional[str]]:
    """
    Evaluates translation quality and flags segments that may have drifted in meaning,
    contain hallucinations, or violate script/length guidelines.
    Returns (is_flagged, flag_reason).
    """
    s_clean = src_text.strip()
    t_clean = tgt_text.strip()

    # Check 1: Empty text
    if not t_clean:
        return True, "Empty translation."

    # Check 2: Target script correctness
    if tgt_lang == "ur":
        has_urdu_chars = bool(URDU_UNICODE_PATTERN.search(t_clean))
        if not has_urdu_chars:
            return True, "Untranslated text or missing Urdu script characters."
    elif tgt_lang == "en":
        has_urdu_chars = bool(URDU_UNICODE_PATTERN.search(t_clean))
        if has_urdu_chars:
            return True, "Target English text contains untranslated Urdu script."

    # Check 3: Repetition hallucination check (e.g., "the the the the the")
    words = t_clean.split()
    if len(words) >= 4:
        repeated_count = 0
        for i in range(len(words) - 1):
            if words[i] == words[i + 1]:
                repeated_count += 1
        if repeated_count >= 3:
            return True, "Repetitive word loop detected in translation."

    # Check 4: Length ratio anomaly
    src_len = max(len(s_clean), 1)
    tgt_len = len(t_clean)
    ratio = tgt_len / src_len

    if ratio < 0.35 and len(s_clean) > 20:
        return True, f"Suspiciously short translation ({tgt_len} vs {src_len} chars); possible content truncation."
    if ratio > 2.6 and len(s_clean) > 15:
        return True, f"Excessively long translation ({tgt_len} vs {src_len} chars); will cause severe timing stretch."

    # Check 5: Glossary check
    if glossary:
        src_lower = s_clean.lower()
        for term, expected_target in glossary.items():
            if term in src_lower and expected_target not in t_clean:
                # If term is in source but not in target, flag for review
                return True, f"Glossary term discrepancy: expected '{expected_target}' for '{term}'."

    return False, None
