"""
Islamic & Arabic Phonetic Normalizer for English Neural TTS
Translates theological Islamic, Quranic, Hadith, and geographical terms
into pronunciation-optimized spellings for neural English phonemizers (espeak-ng / Piper).
"""

import re
from typing import Dict

# Complete list of 114 Quranic Surahs mapped to English neural phonetic spellings
QURANIC_SURAHS: Dict[str, str] = {
    "al-fatihah": "Al Faatiha", "fatihah": "Faatiha",
    "al-baqarah": "Al Bakarah", "baqarah": "Bakarah",
    "ali 'imran": "Aal Imraan", "al-imran": "Aal Imraan", "ali imran": "Aal Imraan",
    "an-nisa": "An Nisaa", "nisa": "Nisaa",
    "al-ma'idah": "Al Maa'ida", "al-maidah": "Al Maa'ida", "maidah": "Maa'ida",
    "al-an'am": "Al An'aam", "al-anam": "Al An'aam", "anam": "An'aam",
    "al-a'raf": "Al A'raaf", "al-araf": "Al A'raaf", "araf": "A'raaf",
    "al-anfal": "Al Anfaal", "anfal": "Anfaal",
    "at-tawbah": "At Tawbah", "tawbah": "Tawbah",
    "yunus": "Yoonus",
    "hud": "Hood",
    "yusuf": "Yoosuf",
    "ar-ra'd": "Ar Ra'ad", "ar-rad": "Ar Ra'ad", "rad": "Ra'ad",
    "ibrahim": "Ibraaheem",
    "al-hijr": "Al Hijr", "hijr": "Hijr",
    "an-nahl": "An Nahl", "nahl": "Nahl",
    "al-isra": "Al Israa", "isra": "Israa",
    "al-kahf": "Al Kahf", "kahf": "Kahf",
    "maryam": "Maryam",
    "ta-ha": "Taa Haa", "taha": "Taa Haa",
    "al-anbiya": "Al Anbiyaa", "anbiya": "Anbiyaa",
    "al-hajj": "Al Hajj", "hajj": "Hajj",
    "al-mu'minun": "Al Mu'minoon", "al-muminun": "Al Mu'minoon", "muminun": "Mu'minoon",
    "an-nur": "An Noor", "nur": "Noor",
    "al-furqan": "Al Furqaan", "furqan": "Furqaan",
    "ash-shu'ara": "Ash Shu'araa", "ash-shuara": "Ash Shu'araa",
    "an-naml": "An Naml", "naml": "Naml",
    "al-qasas": "Al Qasas", "qasas": "Qasas",
    "al-ankabut": "Al Ankabout", "ankabut": "Ankabout",
    "ar-rum": "Ar Room", "rum": "Room",
    "luqman": "Luqmaan",
    "as-sajdah": "As Sajdah", "sajdah": "Sajdah",
    "al-ahzab": "Al Ahzaab", "ahzab": "Ahzaab",
    "saba": "Saba",
    "fatir": "Faatir",
    "ya-sin": "Yaa Seen", "yasin": "Yaa Seen", "yaseen": "Yaa Seen",
    "as-saffat": "As Saaffaat", "saffat": "Saaffaat",
    "sad": "Saad",
    "az-zumar": "Az Zumar", "zumar": "Zumar",
    "ghafir": "Ghaafir",
    "fussilat": "Fussilat",
    "ash-shura": "Ash Shoora", "shura": "Shoora",
    "az-zukhruf": "Az Zukhruf", "zukhruf": "Zukhruf",
    "ad-dukhan": "Ad Dukhaan", "dukhan": "Dukhaan",
    "al-jathiyah": "Al Jaathiyah", "jathiyah": "Jaathiyah",
    "al-ahqaf": "Al Ahqaaf", "ahqaf": "Ahqaaf",
    "muhammad": "Muhammad",
    "al-fath": "Al Fath", "fath": "Fath",
    "al-hujurat": "Al Hujuraat", "hujurat": "Hujuraat",
    "qaf": "Qaaf",
    "adh-dhariyat": "Adh Dhaariyaat", "dhariyat": "Dhaariyaat",
    "at-tur": "At Toor", "tur": "Toor",
    "an-najm": "An Najm", "najm": "Najm",
    "al-qamar": "Al Qamar", "qamar": "Qamar",
    "ar-rahman": "Ar Rahmaan", "rahman": "Rahmaan",
    "al-waqi'ah": "Al Waaqi'ah", "al-waqiah": "Al Waaqi'ah", "waqiah": "Waaqi'ah",
    "al-hadid": "Al Hadeed", "hadid": "Hadeed",
    "al-mujadila": "Al Mujaadila", "mujadila": "Mujaadila",
    "al-hashr": "Al Hashr", "hashr": "Hashr",
    "al-mumtahanah": "Al Mumtahanah", "mumtahanah": "Mumtahanah",
    "as-saff": "As Saff", "saff": "Saff",
    "al-jumu'ah": "Al Jumu'ah", "al-jumuah": "Al Jumu'ah", "jumuah": "Jumu'ah",
    "al-munafiqun": "Al Munaafiqoon", "munafiqun": "Munaafiqoon",
    "at-taghabun": "At Taghaabun", "taghabun": "Taghaabun",
    "at-talaq": "At Talaaq", "talaq": "Talaaq",
    "at-tahrim": "At Tahreem", "tahrim": "Tahreem",
    "al-mulk": "Al Mulk", "mulk": "Mulk",
    "al-qalam": "Al Qalam", "qalam": "Qalam",
    "al-haqqah": "Al Haaqqah", "haqqah": "Haaqqah",
    "al-ma'arij": "Al Ma'aarij", "maarij": "Ma'aarij",
    "nuh": "Nooh",
    "al-jinn": "Al Jinn", "jinn": "Jinn",
    "al-muzzammil": "Al Muzzammil", "al-muzammil": "Al Muzzammil", "muzammil": "Muzzammil",
    "al-muddaththir": "Al Muddath-thir", "muddathir": "Muddath-thir",
    "al-qiyamah": "Al Qiyaamah", "qiyamah": "Qiyaamah",
    "al-insan": "Al Insaan", "insan": "Insaan",
    "al-mursalat": "Al Mursalaat", "mursalat": "Mursalaat",
    "an-naba": "An Naba", "naba": "Naba",
    "an-nazi'at": "An Naazi'aat", "naziat": "Naazi'aat",
    "'abasa": "Abasa", "abasa": "Abasa",
    "at-takwir": "At Takweer", "takwir": "Takweer",
    "al-infitar": "Al Infitaar", "infitar": "Infitaar",
    "al-mutaffifin": "Al Mutaffifeen", "mutaffifin": "Mutaffifeen",
    "al-inshiqaq": "Al Inshiqaaq", "inshiqaq": "Inshiqaaq",
    "al-buruj": "Al Burooj", "buruj": "Burooj",
    "at-tariq": "At Taariq", "tariq": "Taariq",
    "al-a'la": "Al A'laa", "al-ala": "Al A'laa", "ala": "A'laa",
    "al-ghashiyah": "Al Ghaashiyah", "ghashiyah": "Ghaashiyah",
    "al-fajr": "Al Fajr", "fajr": "Fajr",
    "al-balad": "Al Balad", "balad": "Balad",
    "ash-shams": "Ash Shams", "shams": "Shams",
    "al-layl": "Al Layl", "layl": "Layl",
    "ad-duha": "Ad Duhaa", "duha": "Duhaa",
    "ash-sharh": "Ash Sharh", "sharh": "Sharh", "inshirah": "Inshiraah",
    "at-tin": "At Teen", "tin": "Teen",
    "al-'alaq": "Al Alaq", "al-alaq": "Al Alaq", "alaq": "Alaq",
    "al-qadr": "Al Qadr", "qadr": "Qadr",
    "al-bayyinah": "Al Bayyinah", "bayyinah": "Bayyinah",
    "az-zalzalah": "Az Zalzalah", "zalzalah": "Zalzalah",
    "al-'adiyat": "Al Aadiyaat", "al-adiyat": "Al Aadiyaat", "adiyat": "Aadiyaat",
    "al-qari'ah": "Al Qaari'ah", "al-qariah": "Al Qaari'ah", "qariah": "Qaari'ah",
    "at-takathur": "At Takaathur", "takathur": "Takaathur",
    "al-'asr": "Al Asr", "al-asr": "Al Asr", "asr": "Asr",
    "al-humazah": "Al Humazah", "humazah": "Humazah",
    "al-fil": "Al Feel", "fil": "Feel",
    "quraysh": "Quraish",
    "al-ma'un": "Al Maa'oon", "al-maun": "Al Maa'oon", "maun": "Maa'oon",
    "al-kawthar": "Al Kawthar", "kawthar": "Kawthar", "kausar": "Kawthar",
    "al-kafirun": "Al Kaafiroon", "kafirun": "Kaafiroon",
    "an-nasr": "An Nasr", "nasr": "Nasr",
    "al-masad": "Al Masad", "masad": "Masad", "lahab": "Lahab",
    "al-ikhlas": "Al Ikhlaas", "ikhlas": "Ikhlaas",
    "al-falaq": "Al Falaq", "falaq": "Falaq",
    "an-nas": "An Naas", "nas": "Naas",
}

# General Islamic & lecture terminology
ISLAMIC_LEXICON: Dict[str, str] = {
    # Surah and Ayah prefixes
    r"\bsurah\b": "Soorah",
    r"\bsurat\b": "Soorat",
    r"\bayah\b": "Aayah",
    r"\bayat\b": "Aayaat",
    r"\bayat-ul-kursi\b": "Aayat ul Kursee",
    r"\bayatul kursi\b": "Aayat ul Kursee",

    # Key figures & Honorifics
    r"\bsheikh-ul-wazaif\b": "Shaykh ul Wazaayif",
    r"\bsheikh ul wazaif\b": "Shaykh ul Wazaayif",
    r"\bsheikh\b": "Shaykh",
    r"\bhazrat\b": "Haz-rat",
    r"\bubqari\b": "Ub-qaree",
    r"\brasool\b": "Rasool",
    r"\brasulullah\b": "Rasool-ullaah",
    r"\bsallallahu alayhi wasallam\b": "Sallallaahu Alayhee Wa Sallam",
    r"\bradiallahu anhu\b": "Radi-Allaahu Anhu",

    # Spiritual practices & institutions
    r"\btasbeeh khana\b": "Tas-beeh Khaana",
    r"\btasbeeh\b": "Tas-beeh",
    r"\btasbih\b": "Tas-beeh",
    r"\bwazaif\b": "Wazaayif",
    r"\bwazifa\b": "Wazee-fa",
    r"\bwazeefa\b": "Wazee-fa",
    r"\bdhikr\b": "Zikr",
    r"\bzikr\b": "Zikr",
    r"\bdu'a\b": "Du'aa",
    r"\bdua\b": "Du'aa",
    r"\bhadith\b": "Hadeeth",
    r"\bhadeeth\b": "Hadeeth",
    r"\bsunnah\b": "Sunnah",
    r"\bmadrasa\b": "Madrasah",
    r"\bmadrasas\b": "Madrasahs",
    r"\bkhanqah\b": "Khaan-qaah",
    r"\bkhanqahs\b": "Khaan-qaahs",
    r"\btaraveeh\b": "Taraa-weeh",
    r"\btaraweeh\b": "Taraa-weeh",
    r"\bramzan\b": "Ramadaan",
    r"\bramadan\b": "Ramadaan",

    # Sacred invocations
    r"\bsubhanallah\b": "Sub-haan-Allaah",
    r"\balhamdulillah\b": "Al-hamdu-lillaah",
    r"\ballahu akbar\b": "Allaahu Akbar",
    r"\bastaghfirullah\b": "Astagh-firul-laah",
    r"\bjazakallah\b": "Jazaak-Allaah",
    r"\binshallah\b": "Inshaa-Allaah",
    r"\bmashallah\b": "Maashaa-Allaah",

    # Historical geography & Hadith scholars
    r"\bmawarannahr\b": "Maa waraa un Nahr",
    r"\bbukhara\b": "Bukhaara",
    r"\bsamarkand\b": "Samarqand",
    r"\btashkent\b": "Tashkent",
    r"\bimam bukhari\b": "Imaam Bukhaaree",
    r"\bbukhari\b": "Bukhaaree",
    r"\btirmidhi\b": "Tirmidhee",
}


def normalize_phonetics_for_tts(text: str) -> str:
    """
    Transforms English text containing Islamic terms and Quranic Surah names
    into phonetically optimized spellings for natural English neural TTS pronunciation.
    """
    if not text or not text.strip():
        return text

    normalized = text

    # Step 1: Detect and replace Surah names (e.g. "Surah Al-Baqarah", "Surat Al-Kahf")
    # Matches patterns like "Surah [Name]" or "Surat [Name]"
    def surah_replacer(match):
        prefix = match.group(1)  # "Surah" or "Surat"
        name_part = match.group(2).strip().lower()

        # Clean dashes for lookup
        clean_name = name_part.strip("-")
        phonetic_name = QURANIC_SURAHS.get(clean_name)
        if not phonetic_name:
            # Try removing or adding "al-"
            if clean_name.startswith("al-"):
                phonetic_name = QURANIC_SURAHS.get(clean_name[3:])
            else:
                phonetic_name = QURANIC_SURAHS.get(f"al-{clean_name}")

        prefix_phone = "Soorat" if prefix.lower() == "surat" else "Soorah"
        if phonetic_name:
            return f"{prefix_phone} {phonetic_name}"
        else:
            # Fallback: remove hyphens so espeak doesn't stutter
            return f"{prefix_phone} {name_part.replace('-', ' ')}"

    surah_pattern = re.compile(
        r'\b(surah|surat)\s+([a-zA-Z\'-]+)',
        re.IGNORECASE
    )
    normalized = surah_pattern.sub(surah_replacer, normalized)

    # Step 2: Normalize standalone Surah names (e.g. "An-Nas", "Al-Baqarah")
    for surah_key, phonetic_val in sorted(QURANIC_SURAHS.items(), key=lambda x: len(x[0]), reverse=True):
        if len(surah_key) >= 4 and ("-" in surah_key or " " in surah_key):
            escaped = re.escape(surah_key)
            pattern = re.compile(rf'\b{escaped}\b', re.IGNORECASE)
            normalized = pattern.sub(phonetic_val, normalized)

    # Step 3: Apply general Islamic and geographic lexicon
    for pattern, replacement in ISLAMIC_LEXICON.items():
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)

    # Step 3: Polish hyphens in Arabic definite articles ("Al-", "An-", "Ash-", "Ar-", "At-")
    # Hyphens in English TTS cause awkward pauses (e.g., "Al - Baqarah"). Replacing with space sounds natural.
    article_pattern = re.compile(r'\b(Al|An|Ash|Ar|At|Az|Ad|As|Adh)-([A-Za-z])', re.IGNORECASE)
    normalized = article_pattern.sub(r'\1 \2', normalized)

    return normalized
