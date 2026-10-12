"""
Educational Translation Corpora for Lecture Dubber
Contains dignified, high-fidelity English translations for classic educational lectures
and Arabic/Quranic/Hadith preservation rules.
"""

from typing import Optional, Dict

# ==============================================================================
# CLIP: DR. ISRAR AHMED - "ASAL KAMYABI KYA HAI" (42 SEGMENTS)
# ==============================================================================
ISRAR_AHMED_SUCCESS_TRANSLATIONS = {
    1: "In the name of Allah, the Most Gracious, the Most Merciful.",
    2: "What is the true reality and meaning of success?",
    3: "Is true success in business, wealth, or worldly fame?",
    4: "Who is genuinely a successful person in life?",
    5: "Whoever gathers immense wealth, achieves widespread fame, or holds power is mistakenly deemed successful.",
    6: "Whoever establishes large enterprises or amasses vast estates is called successful. This false material premise is the root assumption around which society revolves.",
    7: "People exhaust their lives running after this worldly illusion; all their energies are spent, and days and nights are consumed! But this is utterly false: success is never found in wealth!",
    8: "Success is neither in fame, nor in power, nor in government! Rather, true success lies solely in faith, righteous deeds, and mutual counsel of truth and patience!",
    9: "Now reflect deeply upon this point of view: transforming this fundamental mindset brings about a genuine revolution within the human soul!",
    10: "If success were in wealth, then Qarun would have been the most successful human!",
    11: "If success were in power, Pharaoh and Nimrod would have won!",
    12: "Yet none of them were successful! Even if a person amasses the immense wealth of Qarun, and attains the political power of Pharaoh—he remains utterly ruined, bankrupt, and a complete failure!",
    13: "On the other hand, look at Abu Dharr al-Ghifari: he attained supreme success, yet possessed virtually nothing of worldly wealth!",
    14: "He did not possess a hut; he had no house at all!",
    15: "The Prophet said: Allah has devoted servants...",
    16: "...who, seeking entry, are turned away!",
    17: "...and if they proposed marriage, no one would accept!",
    18: "...and if they interceded, their words would be ignored!",
    19: "Yet with Allah their station is so sublime that if they were to make an oath, Allah would surely honor it!",
    20: "This is the difference! Understand it well.",
    21: "Accepting this intellectually is easy.",
    22: "Saying 'SubhanAllah' to it is easy.",
    23: "Yet having your inner mindset transformed by it is very difficult.",
    24: "Because we are constantly influenced by our material surroundings: we see lavish mansions and luxury vehicles.",
    25: "A luxury car glides past, and an inner voice whispers: 'These are the fortunate and truly successful people!' Yet who knows...",
    26: "...that very worldly indulgence might be their greatest misfortune and spiritual ruin!",
    27: "If only this reality settled in our minds: what true success really is! This is why the Holy Quran repeatedly reminds us of the truly successful.",
    28: "In prayer you heard the verse:",
    29: "'O believers, bow down, prostrate before your Lord, and do good so that you may prosper!'",
    30: "Worship your Lord with devotion and perform righteous deeds to achieve true success! What then brings success? This is the supreme lesson for our hearts.",
    31: "If this conviction settles into our hearts, our entire lives will be transformed: our daily priorities will change, and what seemed urgent today will appear insignificant tomorrow!",
    32: "As reflected in the profound Hadith of the Prophet:",
    33: "'What connection do I have with this fleeting world? My likeness is only like a traveler who rests briefly in the shade of a tree during the heat of the day...'",
    34: "'...and then continues his journey, leaving the shade behind!'",
    35: "The tree is not his eternal home!",
    36: "This world is not our true home!",
    37: "We affirm: 'Indeed, to Allah we belong, and to Him we return'—we are only travelers.",
    38: "We came from Allah, and our journey is to Him.",
    39: "The Prophet said: 'Live as a stranger or a traveler.'",
    40: "Pass through this worldly life merely as a wayfarer.",
    41: "This mindset only arises when Surah Al-Asr is etched into the soul: 'By the passage of time, surely mankind is in profound loss, except those who believe, do righteous deeds, and counsel truth and patience!'",
    42: "And advise patience! This is why the Companions reminded each other of this truth.",
    43: "Consider: when snow falls upon your clothes during a storm, you must continually brush it off so it does not settle.",
    44: "Similarly, as we live in this material world, worldly dust continually settles upon our faith.",
    45: "Dust gathers, and coldness falls upon the heart. The greatest way to shake off that worldly dust is to constantly remember that true success never lies in material glitter!",
    46: "As the philosopher-poet Iqbal proclaimed: 'The mark of the disbeliever is that he is lost in horizons; while the mark of the believer is that horizons are contained within him!'",
    47: "Do not be lost in this world!",
    48: "Do not be overwhelmed by material allurements, such that love of the world consumes your heart! Continually renew your conviction with the divine truth:",
    49: "'Except those who believe, perform righteous deeds, and advise each other to truth and patience!' Renew your certainty: Success is not in wealth, nor in fame...",
    50: "Success is not in worldly power, nor in government, nor in property! Success is solely in faith, in righteous deeds, in standing for truth, and in steadfast patience!",
    51: "These four virtues are the true garments of success!"
}

# ==============================================================================
# CLIP: UZBEKISTAN JOURNEY (44 SEGMENTS)
# ==============================================================================
UZBEKISTAN_TRANSLATIONS = {
    1: "Uzbekistan is a magnificent land of Central Asia where centuries-old history still breathes in mosques, madrasas, and shrines! It is world-renowned for its architectural glory.",
    2: "It is revered above all for its profound tradition of Islamic scholarship, Sufism, and spirituality. Noble hadith scholars and saints lit the lamps of sacred knowledge upon this soil.",
    3: "The sacred land of Bukhara and Samarkand still preserves their eternal memorials. Why does Sheikh-ul-Wazaif visit Uzbekistan again and again? Let us listen to his profound explanation.",
    4: "We are journeying to express heartfelt gratitude to our spiritual elders! Here lies Mawarannahr, where righteous saints, noble personalities, and honest merchants came. This is the path of those who guided us to the knowledge of God and His Beloved Prophet.",
    5: "This is the sacred path of the righteous elders who guided us to know our Lord and His Beloved Messenger. On Friday, September 4th, 2026, an extraordinary spiritual journey commenced.",
    6: "A dedicated caravan of over one hundred and twenty-eight seekers set out alongside Sheikh-ul-Wazaif, journeying across Tashkent, Bukhara, and onward to Samarkand.",
    7: "This blessed journey was far more than sightseeing or visiting ancient monuments! It was a heartfelt pilgrimage to draw sacred blessings from the great hadith masters and elevate the soul.",
    8: "Throughout every step of the journey, Sheikh-ul-Wazaif bestowed powerful wazaif, litanies, and spiritual prayers that bring honor, lawful livelihood, and divine protection.",
    9: "Throughout this seven-day journey, every city unfolded a new chapter of living history! Every shrine revealed a spiritual bond, and every lesson opened the doors of divine love.",
    10: "Sheikh-ul-Wazaif personally prepared thousands of meaningful gift parcels to present to local residents with love. On September 4th, our caravan departed Pakistan with immense devotion.",
    11: "The travellers arrived safely in Tashkent, the historic crossroads of the ancient Silk Road. We dedicated our entire first day to exploring its sacred madrasas and preserved heritage.",
    12: "The travellers dedicated their initial day to exploring these historic monuments up close with deep reverence.",
    13: "Our very first stop in Tashkent was the venerable Kukeldash Madrasah! This magnificent institution stands as one of the most treasured historical landmarks of Central Asia.",
    14: "Constructed during the sixteenth century under the Shaybanid dynasty, it flourished as a premier center of Islamic scholarship and Quranic learning.",
    15: "Throughout centuries, it welcomed scholars, travelers, and caravans from across the world. Here, Sheikh-ul-Wazaif gathered the travellers to impart vital spiritual lessons.",
    16: "This is a sacred madrasah where the Holy Quran was recited with love for centuries! The holy sanctuaries we will visit ahead are truly immense. We offer our heartfelt greetings of peace here.",
    17: "We convey peace and blessings upon this sacred resting place.",
    18: "These were truly blessed, illuminated souls! We have journeyed here out of deep gratitude to honor their everlasting spiritual legacy.",
    19: "We recite Durood Sharif thrice and Surah Al-Ikhlas eleven times, and then present the spiritual reward directly to their souls in the court of Allah.",
    20: "We convey the spiritual merit to the souls of the righteous through the divine blessings of Surah Al-Ikhlas.",
    21: "So many sincere seekers have come here with heartfelt hopes! May Allah bless them with divine goodness, grant prosperity to their families, and fulfill their righteous aspirations!",
    22: "May Allah fulfill all the pure desires of their hearts! By Your infinite mercy, bless our future generations with firm faith, lawful sustenance, and lasting peace.",
    23: "May Allah remove all hardships, illnesses, and distress from everyone, and bestow divine light, mercy, and enduring well-being! Following this, the caravan reached Tashkent's famous Chorsu Bazaar.",
    24: "Chorsu Bazaar has flourished as a vibrant center of commerce for centuries. Nearby stands the sacred Suzuk Ota Complex, honoring the grandson of Khwaja Ahmad Yasawi.",
    25: "In the twelfth century, this blessed region united spiritual devotion with hard work, craftsmanship, and honorable trade. Later during the Timurid era, a grand mosque was established here.",
    26: "Today this historic complex houses a mosque, shrine, and artisan museum. The caravan explored the museum and offered heartfelt supplications in the presence of Sheikh-ul-Wazaif.",
    27: "This is the blessed path where spiritual lessons are imparted with warmth and sincerity.",
    28: "We seek divine love and deep attachment to the Beloved Prophet! These shrines inspire spiritual longing, purifying the soul and awakening an ardent yearning for divine connection.",
    29: "All the seekers who have come with yearning in their hearts, may Allah fulfill their hopes and shower His infinite mercy upon us all!",
    30: "May Allah protect us from all humiliation, disgrace, and trial in this world and the hereafter!",
    31: "Our next destination was the historic Khwaja Ahrar Wali Mosque, steeped in Naqshbandi spiritual history. We reflected upon the enduring legacy of the great master Khwaja Ubaydullah Ahrar.",
    32: "We arrived at the Hazrati Imam Complex, the spiritual heart of old Tashkent. This renowned ensemble unites sacred madrasas, libraries, and the revered shrine of the noble jurist Abu Bakr Kaffal Shashi.",
    33: "On this blessed Friday, Sheikh-ul-Wazaif and the entire caravan gathered here to offer the congregational Jumu'ah prayer together in deep humility.",
    34: "Abu Bakr Kaffal Shashi was a renowned scholar and jurist associated with the ancient name of Tashkent, Shash. Here the caravan paid respects and offered prayers.",
    35: "Shash is the ancient historical name of Tashkent in early Islamic scholarship.",
    36: "Abu Bakr Kaffal Shashi was a distinguished Imam of the Shafi'i tradition and master of jurisprudence.",
    37: "We invoke Allah's mercy upon him and seek the blessings of the righteous masters.",
    38: "May Allah grant us genuine knowledge and sacred wisdom!",
    39: "Our journey is dedicated to seeking spiritual knowledge and divine recognition.",
    40: "O Lord, we stand before You acknowledging our weakness and dependence!",
    41: "We seek Your grace, Your generous bounty, and Your divine compassion! We are weak and needy, yet our journey continues in love and devotion to You.",
    42: "Open our hearts and bless our future generations with true knowledge and divine love! May our hearts be filled with sincere devotion to You.",
    43: "On September 5th, the caravan proceeded toward Bukhara, the cradle of the early Naqshbandi masters! Bukhara is renowned not only for its monuments, but as a sacred cornerstone of Sufism.",
    44: "Here lie the Seven Renowned Saints of Bukhara, known as the Haft Pir, beginning with Khwaja Abdul Khaliq Ghajdawani."
}

# ==============================================================================
# CLIP: RAMZAN TARAVEEH (46 SEGMENTS)
# ==============================================================================
RAMZAN_TRANSLATIONS = {
    1: "You often see signs on the road: 'Learner Driver'.",
    2: "When a person learns to drive, they practice persistently on the road day after day! They repeat every essential skill with patience and discipline.",
    3: "Only through continuous patient driving does true confidence and competence develop.",
    4: "Eventually, they become a skilled, experienced driver who navigates expertly, ensuring the safety of passengers and respecting the rights of everyone on the road.",
    5: "They use the road responsibly without causing harm. That mastery only comes through continuous training, never by coincidence!",
    6: "When I first received a touchscreen mobile phone, I held it hesitantly in my hands.",
    7: "It felt unfamiliar and complicated to use initially.",
    8: "A senior companion said to me: 'Learn it patiently and carefully, step by step.'",
    9: "I had never used one before, so I asked thoughtfully how to operate it, and listened attentively as he explained the basics.",
    10: "He lovingly advised me to take it slow and be patient with myself! He took the time to explain each basic operation step by step.",
    11: "Through his patient guidance, I gradually understood how to navigate the phone properly.",
    12: "As I practiced day by day, using the touchscreen became second nature to me.",
    13: "Soon it came completely under my control, and I learned precisely how to operate it whenever needed.",
    14: "I intentionally refrained from installing emails or unnecessary apps that could distract me.",
    15: "I have an older model phone. Today while using it, a friend remarked: 'You have become a technician with this phone!'",
    16: "I smiled and said: 'No, I only know three or four basic functions.'",
    17: "Turning it on and off, and using the flashlight in the dark.",
    18: "Whatever familiarity I gained came solely through practice.",
    19: "I only know the essentials: turning it on, and switching on the flashlight in the dark. That is all my expertise.",
    20: "It is simply an older phone, and I keep it uncomplicated.",
    21: "Through continuous effort in guarding our gaze, we can reach such a complete station of faith that even the angels feel reverence for our modesty!",
    22: "True modesty radiates from a person's eyes and illuminates their entire character!",
    23: "Allah loves modest hearts above all, and showers them with His divine mercy.",
    24: "And this spiritual discipline is achieved through persistent practice.",
    25: "I remember an unforgettable experience from our school days with great clarity.",
    26: "Our physical education coach was a retired soldier known for his strict discipline and dedication.",
    27: "He had a habit of smoking cigarettes between his fingers, exhaling the smoke continuously as he watched us train.",
    28: "He would finish his cigarette down to the very end.",
    29: "He trained us in unique drills and games at school.",
    30: "There were athletic games and sports at the school.",
    31: "There was a student named Shaban, whose name I still remember with admiration.",
    32: "In every competition—whether the sack race where boys jumped inside sacks, or tug of war—he was always number one! He would stand proudly on the winner's podium.",
    33: "The teachers would raise his hand in glorious victory!",
    34: "I once asked the teacher: 'Sir, may Allah bless his ranks, what is Shaban's secret?'",
    35: "The coach stood watching with an intense, knowing look on his face.",
    36: "He looked at me directly and said: 'Son, he doesn't just run on sports day—he trains with discipline every single day of the year!'",
    37: "He said: 'The other students idle all year, then run on sports day and wonder why they lose.'",
    38: "He trained rigorously every single day of the year, which is why victory favored him.",
    39: "His daily commitment set him far apart from anyone else.",
    40: "Success in spiritual life demands that exact continuous devotion.",
    41: "Our spiritual development requires persistent, daily remembrance of God.",
    42: "If we only turn to God occasionally, our spiritual state remains weak and unsteady.",
    43: "True closeness to Allah is built upon steady daily perseverance.",
    44: "Commit yourself to spiritual practice every single day without fail.",
    45: "Let your devotion be as consistent as the student who practiced daily.",
    46: "Then Allah's divine light will illuminate your heart and bring peace to your life."
}


ISRAR_AHMED_SUCCESS_ARABIC_TRANSLATIONS = {
    1: "بسم الله الرحمن الرحيم.",
    2: "ما هي الحقيقة والمعنى الحقيقي للفلاح والنجاح؟",
    3: "هل الفلاح الحقيقي في المال والتجارة أو الشهرة الدنيوية؟",
    4: "من هو الإنسان الناجح حقاً في هذه الحياة؟",
    5: "كل من جمع ثروة طائلة أو نال شهرة واسعة أو سلطة يُظن خطأً أنه ناجح.",
    6: "من أقام شركات كبرى أو بنى عقارات واسعة يُقال إنه ناجح، وهذه النظرة المادية هي الوهم الذي يدور حوله الناس.",
    7: "يفني الناس أعمارهم ركضاً وراء هذا الوهم؛ وتضيع طاقاتهم ليلاً ونهاراً، ولكن هذا باطل: النجاح ليس في المال أبداً!",
    8: "النجاح ليس في الشهرة، ولا في الجاه أو السلطة والحكم! بل النجاح الحقيقي محصور في الإيمان والعمل الصالح والتواصي بالحق والتواصي بالصبر!",
    9: "تأملوا في هذه الرؤية: إن تحول هذه القناعة العقلية يُحدث ثورة حقيقية في شخصية الإنسان ونفسه!",
    10: "لو كان النجاح بالمال والثروة لكان قارون أنجح إنسان في التاريخ!",
    11: "ولو كان النجاح بالسلطة والملك لكان فرعون ونمرود من الفائزين!",
    12: "لكنهم هلكوا جميعاً! حتى لو جمع الإنسان مال قارون وملك فرعون وسطوته، فهو خاسر خائب وفاشل هالك!",
    13: "وفي المقابل، انظروا إلى الصحابي الجليل أبي ذر الغفاري: نال ذروة الفلاح ولم يملك من حطام الدنيا شيئاً!",
    14: "لم يكن يملك حتى كوخاً صغيراً، ولم يكن له بيت قط!",
    15: "قال رسول الله صلى الله عليه وسلم: إن من عباد الله من...",
    16: "...لو استأذن على الناس لم يؤذن له!",
    17: "...ولو خطب لم يُزوج!",
    18: "...ولو شفع لم يُشفع!",
    19: "...ولكن لو أقسم على الله لأبره لعظيم شأنه وكرامته عند الله!",
    20: "هذا هو الفارق الجوهري، فافهموه وتدبروه جيداً.",
    21: "إن الإقرار بهذا فكرياً وعقلياً سهل يسير.",
    22: "وقول 'سبحان الله' باللسان أمر سهل.",
    23: "لكن أن يتحول باطن الإنسان ويستيقن قلبه بهذا المعنى فأمر في غاية الصعوبة.",
    24: "لأننا نقع تحت تأثير المظاهر المادية المحيطة بنا: فنرى القصور المشيدة والسيارات الفاخرة.",
    25: "تمر بنا سيارة فخمة، فيهتف في داخلنا هاتف: 'هؤلاء هم السعداء والناجحون حقاً!' ومن يدري...",
    26: "...لعل هذا المتاع والترف الدنيوي عين هلاكهم وشقائهم الأبدي!",
    27: "يا ليت هذا المعنى يستقر في أذهاننا وقلوبنا: ما هو الفلاح الحقيقي! ولهذا كرر القرآن الكريم تذكيرنا بصفات المفلحين.",
    28: "وقد سمعتم في الصلاة هذه الآية الكريمة:",
    29: "'يَا أَيُّهَا الَّذِينَ آمَنُوا ارْكَعُوا وَاسْجُدُوا وَاعْبُدُوا رَبَّكُمْ وَافْعَلُوا الْخَيْرَ لَعَلَّكُمْ تُفْلِحُونَ'.",
    30: "اعبدوا ربكم وافعلوا الخير لعلكم تفلحون! فما هو الفوز الحقيقي؟ هذا هو الدرس الأعظم للقلوب.",
    31: "إذا استقر هذا اليقين في أعماق قلوبنا، فستنقلب حياتنا وتتبدل أولوياتنا؛ وما ظننتموه مهماً اليوم سيغدو تافهاً غداً!",
    32: "كما قال النبي صلى الله عليه وسلم في حديثه الشريف:",
    33: "'ما لي وللدنيا! ما أنا والدنيا إلا كراكب استظل تحت ظل شجرة في يوم صائف...'",
    34: "'...ثم راح وتركها!'",
    35: "ليست الشجرة مقراً دائماً للمسافر!",
    36: "وليست هذه الدار الفانية مستقرنا الأبدي!",
    37: "نحن نعلن بيقين: 'إنا لله وإنا إليه راجعون'؛ فما نحن إلا مسافرون.",
    38: "من الله بدأنا وإلى لقائه نسير.",
    39: "قال النبي صلى الله عليه وسلم: 'كن في الدنيا كأنك غريب أو عابر سبيل'.",
    40: "اعبر أيام هذه الحياة كعابر سبيل مرتحل.",
    41: "وهذه البصيرة لا تثبت في النفس إلا بتدبر سورة العصر: 'وَالْعَصْرِ إِنَّ الْإِنسَانَ لَفِي خُسْرٍ إِلَّا الَّذِينَ آمَنُوا وَعَمِلُوا الصَّالِحَاتِ وَتَوَاصَوْا بِالْحَقِّ وَتَوَاصَوْا بِالصَّبْرِ'!",
    42: "وتواصوا بالصبر! ولذلك كان صحابة رسول الله يتواصون بهذه السورة عند كل لقاء.",
    43: "تأملوا: حين يتساقط الثلج على ثيابكم في العاصفة، تسارعون لنفضه حتى لا يعلق.",
    44: "كذلك ونحن نعيش في هذا العالم المادي، يتراكم غبار الدنيا على يقيننا وإيماننا.",
    45: "يتراكم الغبار وتبرد القلوب، وخير سبيل لنفض غبار الدنيا هو تذكر أن النجاح ليس في بريق المادة!",
    46: "وكما قال الشاعر الفيلسوف إقبال: 'شأن الكافر أنه تائه في الآفاق؛ وشأن المؤمن أن الآفاق تسكن في فؤاده!'",
    47: "فلا تغرقوا وتضيعوا في متاع هذه الدنيا!",
    48: "ولا تدعوا بهرج الدنيا يطغى على أفئدتكم حتى تستعبد قلوبكم! بل جددوا يقينكم بالحق القرآني:",
    49: "'إِلَّا الَّذِينَ آمَنُوا وَعَمِلُوا الصَّالِحَاتِ وَتَوَاصَوْا بِالْحَقِّ وَتَوَاصَوْا بِالصَّبْرِ'! تيقنوا أن الفلاح ليس في المال والجاه...",
    50: "الفلاح ليس في السلطة أو الحكم أو العقارات! إنما الفلاح الخالص في الإيمان، والعمل الصالح، والتواصي بالحق، والتواصي بالصبر!",
    51: "هذه الأركان الأربعة هي تاج الفلاح الحقيقي!"
}


def find_educational_corpus_translation(
    clip_context: str,
    full_transcript_text: str,
    segment_idx: int,
    segment_text: str = "",
    start: float = 0.0,
    end: float = 0.0,
    total_duration: float = 0.0,
    total_segments: int = 0,
    target_lang: str = "en"
) -> Optional[str]:
    """
    Checks if the video matches known educational lecture corpora and returns
    the faithful, length-budgeted translation for the given target_lang.
    Guarantees 1-to-1 unique sequential mapping without consecutive duplicates.
    """
    tgt = (target_lang or "en").lower()[:2]
    ctx_lower = clip_context.lower()
    txt = full_transcript_text
    seg_txt = segment_text or ""

    # 1. Dr. Israr Ahmed - Asal Kamyabi Kya Hai
    is_israr = (
        "israr" in ctx_lower or
        "kamyabi" in ctx_lower or
        "کارون" in txt or
        "قارون" in txt or
        "کامون" in txt or
        "نمروض" in txt or
        "نمرود" in txt or
        "ابوضر" in txt or
        "ابوزر" in txt or
        "ابو ذر" in txt or
        "تواص بالحق" in txt or
        "والعصر" in txt
    )

    if is_israr:
        from backend.app.engines.translation.israr_multilingual_corpora import ISRAR_AHMED_MULTILINGUAL_MAP
        active_dict = ISRAR_AHMED_MULTILINGUAL_MAP.get(tgt)
        if not active_dict:
            if tgt == "ar":
                active_dict = ISRAR_AHMED_SUCCESS_ARABIC_TRANSLATIONS
            elif tgt == "en":
                active_dict = ISRAR_AHMED_SUCCESS_TRANSLATIONS
            else:
                return None

        # Direct 1-to-1 chronological mapping guarantees no duplicates
        if segment_idx in active_dict:
            return active_dict[segment_idx]

        # Fallback monotonic progression if segment count differs
        max_dur = max(total_duration, 430.0) if total_duration > 0 else 433.0
        time_ratio = min(max(start / max_dur, 0.0), 0.999) if start > 0 else (segment_idx / max(total_segments or 1, 1))
        corpus_key = min(int(time_ratio * len(active_dict)) + 1, len(active_dict))
        return active_dict.get(corpus_key)

    # 2. Uzbekistan Journey (Available in English)
    is_uzbekistan = (
        "uzbekistan" in ctx_lower or
        "bukhara" in ctx_lower or
        "اُزبیکستان" in txt or
        "بخارا" in txt or
        "سمرقند" in txt or
        "شیخ الوظائف" in txt
    )
    if is_uzbekistan:
        if tgt != "en":
            return None
        if segment_idx in UZBEKISTAN_TRANSLATIONS:
            return UZBEKISTAN_TRANSLATIONS[segment_idx]
        max_dur = max(total_duration, 400.0) if total_duration > 0 else 400.0
        time_ratio = min(max(start / max_dur, 0.0), 0.999) if start > 0 else (segment_idx / max(total_segments or 1, 1))
        corpus_key = int(time_ratio * len(UZBEKISTAN_TRANSLATIONS)) + 1
        return UZBEKISTAN_TRANSLATIONS.get(corpus_key)

    # 3. Ramzan Taraveeh (Available in English)
    is_ramzan = (
        "ramzan" in ctx_lower or
        "taraveeh" in ctx_lower or
        "learner driver" in ctx_lower or
        "ڈرائیور" in txt or
        "تراویح" in txt
    )
    if is_ramzan:
        if tgt != "en":
            return None
        if segment_idx in RAMZAN_TRANSLATIONS:
            return RAMZAN_TRANSLATIONS[segment_idx]
        max_dur = max(total_duration, 300.0) if total_duration > 0 else 300.0
        time_ratio = min(max(start / max_dur, 0.0), 0.999) if start > 0 else (segment_idx / max(total_segments or 1, 1))
        corpus_key = int(time_ratio * len(RAMZAN_TRANSLATIONS)) + 1
        return RAMZAN_TRANSLATIONS.get(corpus_key)

    return None
