from typing import Dict, Optional

# Default bilingual educational glossary for English <-> Urdu technical terms
DEFAULT_EDUCATIONAL_GLOSSARY: Dict[str, str] = {
    # Computer Science & Mathematics
    "algorithm": "الگورتھم",
    "algorithms": "الگورتھمز",
    "data structure": "ڈیٹا اسٹرکچر",
    "complexity": "پیچیدگی",
    "function": "فنکشن",
    "variable": "متغیر",
    "equation": "مساوات",
    "derivative": "مشتق",
    "integral": "انٹیگرل",
    "matrix": "میٹرکس",
    "vector": "ویکٹر",
    "artificial intelligence": "مصنوعی ذہانت",
    "machine learning": "مشین لرننگ",
    "neural network": "نیورل نیٹ ورک",
    "computer": "کمپیوٹر",
    "program": "پروگرام",
    "software": "سافٹ ویئر",
    "hardware": "ہارڈ ویئر",
    "loop": "لوپ",
    "array": "ایرے",
    "memory": "میموری",
    "database": "ڈیٹا بیس",
    "network": "نیٹ ورک",
    "theory": "نظریہ",
    "proof": "ثبوت",
    "theorem": "مسئلہ",
    "hypothesis": "مفروضہ",
}


def get_combined_glossary(user_glossary: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Combines system educational glossary with any user-provided glossary."""
    combined = dict(DEFAULT_EDUCATIONAL_GLOSSARY)
    if user_glossary:
        for k, v in user_glossary.items():
            combined[k.strip().lower()] = v.strip()
    return combined
