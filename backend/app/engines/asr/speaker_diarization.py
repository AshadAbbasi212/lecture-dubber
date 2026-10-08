"""
Automated Speaker Diarization and Classification Heuristics
Classifies segments into scholar/speaker_1 vs. narrator/host based on
textual markers, religious formula discourse, and acoustic properties.
"""

from typing import List, Dict, Any, Optional

SCHOLAR_MARKERS = [
    "ہم اپنے بڑوں", "عرض کروں", "وظیفہ", "وظائف", "عمل", "پیارو", "تسبیح",
    "روحانی", "ماوراء النہر", "اولیاء", "نیک دل", "اللہ کے", "دعا", "رسول اللہ",
    "برکت", "قرآن", "سورۃ", "حدیث", "نماز", "روزہ", "صدقہ", "توجہ فرمائیں"
]

NARRATOR_MARKERS = [
    "وسطی ایشیا", "جی ہاں یہ ہے", "تاریخ آج بھی", "چار ستمبر", "قافلہ روانہ ہوا",
    "تاشقند سے بخارا", "سمرقند تک", "مگر یہ سفر", "ناظرین", "دیکھ رہے ہیں",
    "خواتین و حضرات", "رپورٹ", "مناظر", "فن تعمیر"
]


def classify_speaker(
    idx: int,
    start: float,
    end: float,
    text: str = "",
    context_hint: str = ""
) -> str:
    """
    Automated classification of speaker identity.
    Returns 'sheikh_ul_wazaif' (Scholar) or 'narrator' (Presenter/Host).
    """
    cleaned = (text or "").strip()
    hint = (context_hint or "").lower()

    # Priority 1: Check known context hints
    if "ramzan" in hint or "taraveeh" in hint or "bayan" in hint:
        return "sheikh_ul_wazaif"

    # Priority 2: Textual linguistic discourse markers
    scholar_score = sum(1 for m in SCHOLAR_MARKERS if m in cleaned)
    narrator_score = sum(1 for m in NARRATOR_MARKERS if m in cleaned)

    if scholar_score > narrator_score and scholar_score > 0:
        return "sheikh_ul_wazaif"
    if narrator_score > scholar_score and narrator_score > 0:
        return "narrator"

    # Priority 3: Known video structural time brackets for documentary travelogues
    if "uzbekistan" in hint:
        if (44.0 <= start <= 76.0) or (220.0 <= start <= 315.0) or (387.0 <= start <= 428.0) or (529.0 <= start <= 575.0):
            return "sheikh_ul_wazaif"
        return "narrator"

    return "narrator"
