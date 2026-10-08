import re
from typing import Tuple, Optional

# Regular expressions for Arabic diacritics, Quranic marks, and Hadith formulas
ARABIC_CHAR_PATTERN = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]')
ARABIC_DIACRITICS_PATTERN = re.compile(r'[\u064B-\u065F\u0670\u06D6-\u06ED]')

# Common Hadith and Quranic introductory formulas
SACRED_PHRASES = [
    "بسم الله الرحمن الرحيم",
    "قال رسول الله",
    "صلى الله عليه وسلم",
    "عليه الصلاة والسلام",
    "قال الله تعالى",
    "عز وجل",
    "سبحان الله",
    "الحمد لله",
    "لا اله الا الله",
    "لا إله إلا الله",
    "الله اكبر",
    "الله أكبر",
    "استغفر الله",
    "أستغفر الله",
    "لا حول ولا قوة الا بالله",
    "لا حول ولا قوة إلا بالله",
    "اللهم صل على",
    "انا لله وانا اليه راجعون",
    "إنا لله وإنا إليه راجعون",
    "حسبنا الله ونعم الوكيل",
    "اعوذ بالله من الشيطان الرجيم",
    "أعوذ بالله من الشيطان الرجيم",
    "رضي الله عنه",
    "رضي الله عنها",
    "رحمه الله",
    "جزاك الله خيرا",
    "السلام عليكم ورحمة الله",
]

# Normalized regex patterns for matching sacred Arabic phrases
NORMALIZED_SACRED_PATTERNS = [
    re.compile(re.escape(phrase.replace(" ", r"\s*")), re.IGNORECASE)
    for phrase in SACRED_PHRASES
]


def is_sacred_arabic_content(text: str) -> Tuple[bool, Optional[str]]:
    """
    Detects if a given text segment contains or consists of a Quranic verse,
    Hadith quotation, or sacred Arabic dhikr.
    Returns (is_sacred, reason).
    """
    if not text or not text.strip():
        return False, None

    cleaned = text.strip()

    # 1. Check for specific Quranic / Hadith indicator phrases
    for phrase in SACRED_PHRASES:
        if phrase in cleaned:
            return True, f"Sacred Arabic formula detected: '{phrase}'"

    # 2. Check for heavy Arabic vocalization (Harakat / Tashkeel) characteristic of Quranic script
    total_chars = len(cleaned.replace(" ", ""))
    if total_chars > 0:
        diacritics_count = len(ARABIC_DIACRITICS_PATTERN.findall(cleaned))
        # If text has significant diacritics (>12% of chars), it's vocalized Arabic (Quran/Hadith)
        if diacritics_count / total_chars >= 0.12:
            return True, f"Quranic vocalization detected ({diacritics_count} diacritics)"

    # 3. Check for specific Quranic prefixes or surah openings
    quranic_markers = [
        "يَا أَيُّهَا الَّذِينَ آمَنُوا", "يا ايها الذين امنوا",
        "قُلْ هُوَ اللَّهُ أَحَدٌ", "قل هو الله احد",
        "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ", "الحمد لله رب العالمين",
        "إِنَّا أَعْطَيْنَاكَ الْكَوْثَرَ", "انا اعطيناك الكوثر",
        "وَالْعَصْرِ", "والعصر",
        "تَبَارَكَ الَّذِي", "تبارك الذي",
        "سُبْحَانَ الَّذِي", "سبحان الذي",
        "وَمَا أَرْسَلْنَاكَ", "وما ارسلناك",
    ]
    for marker in quranic_markers:
        if marker in cleaned:
            return True, f"Quranic verse detected: '{marker}'"

    return False, None


def should_preserve_untranslated(text: str) -> bool:
    """
    Helper returning True if this speech segment should remain in original Arabic
    without being translated into English.
    """
    is_sacred, _ = is_sacred_arabic_content(text)
    return is_sacred
