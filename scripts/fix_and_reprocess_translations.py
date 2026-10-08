"""
Production Translation Fix & Reprocessing Script for Lecture Dubber
Replaces flawed Whisper direct-audio translations with accurate, dignified,
and length-budgeted English educational translations for both 10-minute clips.
"""

import json
import shutil
import subprocess
import time
from pathlib import Path
import soundfile as sf
import numpy as np

ROOT_DIR = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(ROOT_DIR))

from backend.app.core.config import settings
from backend.app.db.models.segment import Segment
from backend.app.ingest.media_probe import probe_media_file
from backend.app.pipeline.timing_fit import calculate_timing_fit, apply_audio_time_stretch
from backend.app.engines.tts.voice_synthesizer import VoiceSynthesizer
from backend.app.engines.translation.arabic_preserver import is_sacred_arabic_content
from backend.app.pipeline.audio_mixer import assemble_timeline_vocals, mix_vocals_and_background
from backend.app.pipeline.video_muxer import mux_video_and_audio, export_dub_mp3

# ==============================================================================
# CLIP 1: UZBEKISTAN JOURNEY (44 SEGMENTS) - FAITHFUL ENGLISH TRANSLATION
# ==============================================================================
UZBEKISTAN_TRANSLATIONS = {
    1: "Uzbekistan is a land of Central Asia where centuries-old history still breathes in mosques, madrasas, shrines, and ancient paths. This is Uzbekistan, a region renowned not only for its cultural heritage and architecture,",
    2: "but also for its profound tradition of Islamic scholarship, Sufism, and spirituality. This is Uzbekistan's sacred soil where noble hadith scholars, jurists, and Sufis lit the lamps of knowledge.",
    3: "The land of Bukhara and Samarkand still preserves their sacred memorials. Why does Sheikh-ul-Wazaif visit Uzbekistan repeatedly? He explains:",
    4: "We are going to express gratitude to our spiritual elders. Here lies Mawarannahr, where righteous saints, noble personalities, and honest merchants came. This is the path of those who guided us to the knowledge of God and His Beloved Prophet.",
    5: "This is the sacred path of those who guided us to know our Lord and His Beloved Messenger. On Friday, September 4th, 2026,",
    6: "a caravan comprising over one hundred and twenty-eight men and women departed alongside Sheikh-ul-Wazaif toward this historic land, travelling from Tashkent to Bukhara, and from Bukhara to Samarkand. Yet this journey was not merely to observe historical architecture or explore ancient cities.",
    7: "It was a sacred pilgrimage to visit shrines of saints, draw spiritual blessing from hadith scholars, and seek the advancement of the soul. Throughout the journey, Sheikh-ul-Wazaif bestowed upon the caravan",
    8: "sacred prayers, wazaif, litanies, and meditations that bring honour, livelihood, divine protection from harm, and spiritual elevation.",
    9: "Throughout this seven-day journey, every city unfolded a new chapter of history. Every shrine revealed a spiritual bond, and every lesson unveiled secrets of success in this world and the hereafter, opening the doors of spirituality.",
    10: "Sheikh-ul-Wazaif also carried thousands of gift parcels with him to present to the local residents. On September 4th, departing Pakistan,",
    11: "the caravan arrived in Tashkent. While Tashkent is the modern political capital of Uzbekistan, its historic old city still preserves landmarks of the Silk Road, ancient madrasas, and centuries-old bazaars. The first day was devoted to exploring this city.",
    12: "The travellers dedicated their initial day to exploring the historic monuments up close.",
    13: "The Kukeldash Madrasah was our first major stop in Tashkent. Kukeldash Madrasah,",
    14: "established in the sixteenth century during the Shaybanid dynasty, is regarded among the oldest preserved educational monuments in Tashkent. Constructed around 1570 CE, this institution served as a premier center of Islamic learning,",
    15: "while also functioning across different historical eras as a caravanserai and for other community purposes. Here at the onset of the journey, Sheikh-ul-Wazaif imparted essential spiritual guidance to the travellers:",
    16: "This is a madrasah where the Holy Quran was recited for centuries. The institutions we will visit ahead are also immense. We offer our greetings of peace here.",
    17: "We convey peace and blessings upon this sacred place.",
    18: "These were truly blessed souls. We have journeyed here out of deep gratitude to honor their spiritual legacy.",
    19: "We recite Durood Sharif thrice and Surah Al-Ikhlas eleven times, and then offer the spiritual reward to their souls in the court of Allah.",
    20: "We convey the spiritual merit to the souls of the righteous through the blessings of Surah Al-Ikhlas.",
    21: "So many seekers have come here with heartfelt hopes. May Allah bless them with divine goodness, grant prosperity to their families, and fulfill their righteous aspirations!",
    22: "May Allah fulfill all the pure desires of their hearts! By Your divine mercy, bless our future generations with faith, lawful sustenance, and lasting peace and prosperity.",
    23: "May Allah remove all hardships, illnesses, and distress from everyone, and bestow divine light, mercy, and enduring well-being! Following this, the caravan reached Tashkent's famous Chorsu Bazaar.",
    24: "Chorsu Bazaar in Tashkent has been a bustling commercial hub for centuries. Nearby is the Suzuk Ota Complex. Suzuk Ota, whose real name was Sheikh Mustafa Qul Khwaja, was the grandson of Khwaja Ahmad Yasawi. In the twelfth century,",
    25: "this region fostered religious education alongside hard work, craftsmanship, and honest livelihood. Later during the Timurid era, a grand mosque was established here.",
    26: "Today this historic complex houses a mosque, shrine, and artisan museum. The caravan explored the museum and offered heartfelt supplications in the presence of Sheikh-ul-Wazaif.",
    27: "This is the blessed path where spiritual lessons are imparted.",
    28: "We seek divine love and attachment to the Beloved Prophet. These shrines inspire spiritual longing, purifying the soul and yearning for divine connection.",
    29: "All the seekers who have come with longing in their hearts, may Allah fulfill their hopes and shower His infinite mercy upon us.",
    30: "May Allah protect us from all humiliation, disgrace, and trial in this world and the next.",
    31: "Following Chorsu Bazaar, our next destination was the Khwaja Ahrar Wali Mosque, whose history dates back to the fifteenth century. Founded through the legacy of the prominent Naqshbandi master Khwaja Ubaydullah Ahrar,",
    32: "the Hazrati Imam Complex in old Tashkent is an ensemble of several historic religious monuments. It comprises the Barak-Khan Madrasah, Muyi Mubarak Madrasah, Tillya Sheikh Mosque, Hazrati Imam Mosque, and the shrine of Sheikh Abu Bakr",
    33: "Kaffal Shashi. The caravan arrived here on Friday, where Sheikh-ul-Wazaif and the travelers offered the Jumu'ah congregational prayer together.",
    34: "Abu Bakr Kaffal Shashi was a renowned scholar and jurist associated with the ancient name of Tashkent, Shash. Here the caravan paid respects and offered prayers.",
    35: "Shash is the ancient historical name of Tashkent in early Islamic scholarship.",
    36: "Abu Bakr Kaffal Shashi was a distinguished Imam of the Shafi'i tradition and master of jurisprudence.",
    37: "We invoke Allah's mercy upon him and seek the blessings of the righteous masters.",
    38: "May Allah grant us genuine knowledge and sacred wisdom.",
    39: "Our journey is dedicated to seeking spiritual knowledge and divine recognition.",
    40: "O Lord, we stand before You acknowledging our weakness and dependence.",
    41: "We seek Your grace, Your generous bounty, and Your divine compassion. We are weak and needy, yet our journey continues in love and devotion to You.",
    42: "Open our hearts and bless our future generations with true knowledge and divine love. May our hearts be filled with sincere devotion to You.",
    43: "On September 5th, the caravan proceeded toward Bukhara, the cradle of the early Naqshbandi masters. Bukhara is renowned not only for its monuments but as a sacred cornerstone in the history of Sufism.",
    44: "Here lie the Seven Renowned Saints of Bukhara, known as the Haft Pir, beginning with Khwaja Abdul Khaliq Ghajdawani."
}

# ==============================================================================
# CLIP 2: RAMZAN TARAVEEH (64 SEGMENTS) - FAITHFUL ENGLISH TRANSLATION
# ==============================================================================
RAMZAN_TRANSLATIONS = {
    1: "You often see signs on the road: 'Learner Driver'.",
    2: "When someone is learning to drive a car, they practice continuously on the road. They repeat the drills day after day,",
    3: "driving and practicing patiently over time.",
    4: "Eventually, they become a skilled, experienced driver who navigates expertly, ensuring the safety of passengers and respecting the rights of everyone on the road.",
    5: "They use the road responsibly without causing harm. That only comes to someone through continuous training, not by coincidence.",
    6: "When I first received a touchscreen mobile phone, I held it hesitantly in my hands.",
    7: "It felt unfamiliar and complicated to use initially.",
    8: "A senior companion said to me: 'Learn it patiently and carefully, step by step.'",
    9: "I had never used one before, so I asked thoughtfully how to operate it, and listened attentively as he explained the basics.",
    10: "He advised me to take it slow and be patient,",
    11: "and he explained the basic operations to me.",
    12: "Gradually, as I practiced using the touchscreen,",
    13: "it came under my control. I learned the necessary experience of turning it on and off when needed.",
    14: "I intentionally refrained from installing emails or unnecessary apps that could distract me.",
    15: "I have an older model phone. Today while using it, a friend remarked: 'You have become a technician with this phone!'",
    16: "I said: 'No, I only know three or four basic functions.'",
    17: "Turning it on and off, and using the flashlight in the dark.",
    18: "Whatever familiarity I gained came solely through practice.",
    19: "I only know the essentials: turning it on, and switching on the flashlight in the dark. That is all my expertise.",
    20: "It is simply an older phone, and I keep it uncomplicated.",
    21: "Through continuous effort in guarding our gaze, we can reach such a complete station of faith that even the angels feel reverence for our modesty!",
    22: "Because modesty shines in the eyes,",
    23: "and Allah loves modesty.",
    24: "And this spiritual discipline is achieved through persistent practice.",
    25: "During our school days,",
    26: "we had a physical education teacher who was a retired soldier.",
    27: "He had a habit of smoking cigarettes between his fingers, exhaling the smoke continuously as he watched us train.",
    28: "He would finish his cigarette down to the end.",
    29: "He trained us in unique drills and games at school.",
    30: "There were athletic games and sports at the school.",
    31: "There was a student named Shaban, whose name I still remember.",
    32: "In every competition—whether the sack race where boys jumped inside sacks, or tug of war—he was always number one. He would stand proudly on the winner's podium.",
    33: "The teachers would raise his hand in victory.",
    34: "I once asked the teacher: 'Sir, may Allah bless his ranks, what is Shaban's secret?'",
    35: "The teacher, exhaling cigarette smoke,",
    36: "looked at me and said: 'Son, he doesn't just run once a year on sports day—he trains all year round!'",
    37: "He said: 'The other students idle all year, then run on sports day and wonder why they lose.'",
    38: "In Ramadan, we must lay the foundation of our worship. Scholars and righteous saints have written in their books that whatever good deed you establish in Ramadan,",
    39: "Allah grants the divine ability to maintain it throughout the entire year!",
    40: "He grants the ability to continue it all year long!",
    41: "We must establish the foundation of guarding our gaze starting right within our prayer.",
    42: "A righteous elder once observed someone in prayer. Look at where your gaze falls during Salah!",
    43: "Too often people stand in prayer outwardly, yet their eyes and thoughts wander,",
    44: "as if they are not truly standing in the divine presence of Allah.",
    45: "We struggle because our gaze has become accustomed to wandering.",
    46: "We must be mindful of our surroundings,",
    47: "and protect the spiritual environment of our homes and families. A pious elder once remarked that we must bring our wandering eyes back to Allah.",
    48: "Our eyes have long strayed, and now is the time to bring them back! In every standing posture, in every bowing, in every prostration,",
    49: "in every posture of prayer, we must discipline our gaze: 'O Lord, wherever my power reaches, I will guard my eyes!'",
    50: "In the markets and streets, the environment erodes faith. O Allah, temptations surround us everywhere.",
    51: "O Lord, I am helpless, but You are all-powerful! I strive within prayer, and I pray to You:",
    52: "When my shroud is prepared for the grave, let my eyes be free from any sin or blemish before You! The beginning of this effort starts today in this Ramadan Taraveeh.",
    53: "I begin this discipline tonight in this Ramadan Taraveeh prayer.",
    54: "In this Ramadan prayer, from the moment I said 'Allahu Akbar' in the first rak'ah, I directed my gaze only where You commanded.",
    55: "I kept my gaze away from where You forbade.",
    56: "In the first rak'ah of prayer, where should the eyes look?",
    57: "At the place of prostration, not wandering aimlessly.",
    58: "In prayer, I made Your will my desire.",
    59: "In prayer, whose will? Allah's will I made my desire! O Allah, bless me so that outside prayer too, my eyes seek only what pleases You,",
    60: "looking only at that which is beloved to You.",
    61: "This spiritual discipline is the work of a lifetime. As I prayed the first rak'ah, Allah placed this conviction firmly in my heart: to guard my gaze in every posture of prayer.",
    62: "To work on purifying my eyes in every rak'ah and every posture.",
    63: "A spiritual scholar recorded that a person was unable to recite the Shahadah on his deathbed, because in life a forbidden gaze had poisoned his heart,",
    64: "and due to that unrepented sin, he was hindered from uttering the Kalimah in his final breath."
}

def reprocess_clip(job_slug: str, video_path: Path, translations: dict, default_speaker: str, clean_tts: bool = True):
    print("=" * 80)
    print(f"REPROCESSING JOB: {job_slug} (Crystal-Clear English Accent & Natural Pacing)")
    print("=" * 80)

    work_dir = ROOT_DIR / "storage" / f"job_{job_slug}"
    audio_dir = work_dir / "audio"
    tts_dir = work_dir / "tts"
    if clean_tts and tts_dir.exists():
        shutil.rmtree(tts_dir)
    tts_dir.mkdir(parents=True, exist_ok=True)

    vocals_wav = audio_dir / "vocals.wav"
    bg_wav = audio_dir / "background.wav"
    transcript_file = work_dir / "transcript_ur.json"

    with open(transcript_file, "r", encoding="utf-8") as f:
        ur_segments = json.load(f)

    # 1. Build Aligned Bilingual Transcript with Correct Translations
    aligned_segments = []
    voc_data, voc_sr = sf.read(str(vocals_wav), dtype="float32")
    if voc_data.ndim == 1:
        voc_data = np.column_stack([voc_data, voc_data])

    synthesizer = VoiceSynthesizer()
    segment_models = []

    for s in ur_segments:
        idx = s["idx"]
        start = s["start"]
        end = s["end"]
        target_dur = end - start
        ur_text = s["text"].strip()
        en_text = translations.get(idx, "We continue our lecture in English.")

        # Classify speaker persona
        if job_slug == "uzbekistan_journey_10m":
            if (start >= 45.0 and end <= 75.0) or (start >= 220.0 and end <= 315.0) or (start >= 387.0 and end <= 428.0) or (start >= 529.0 and end <= 575.0):
                speaker = "sheikh_ul_wazaif"
            else:
                speaker = "narrator"
        else:
            speaker = "sheikh_ul_wazaif"

        # Check sacred Arabic
        is_sacred, sacred_reason = is_sacred_arabic_content(ur_text)

        aligned_segments.append({
            "idx": idx,
            "start": round(start, 2),
            "end": round(end, 2),
            "duration": round(target_dur, 2),
            "speaker": speaker,
            "is_sacred_arabic": is_sacred,
            "sacred_reason": sacred_reason,
            "ur_text": ur_text,
            "en_text": en_text
        })

        fitted_seg_path = tts_dir / f"seg_{idx:03d}_fitted.wav"

        # If already synthesized and recent
        if fitted_seg_path.exists() and fitted_seg_path.stat().st_size > 1000:
            seg_obj = Segment(
                id=idx,
                job_id=job_slug,
                idx=idx,
                start=start,
                end=end,
                speaker=speaker,
                src_text=ur_text,
                tgt_text=en_text,
                tts_path=str(fitted_seg_path)
            )
            segment_models.append(seg_obj)
            continue

        if is_sacred:
            start_samp = int(round(start * voc_sr))
            end_samp = min(int(round(end * voc_sr)), len(voc_data))
            recitation_audio = voc_data[start_samp:end_samp]
            sf.write(str(fitted_seg_path), recitation_audio, voc_sr)
            print(f"  Segment {idx:03d} [{start:6.2f}s - {end:6.2f}s] -> Sacred Arabic Recitation Preserved")
        else:
            raw_seg_path = tts_dir / f"seg_{idx:03d}_raw.wav"
            synthesizer.synthesize_segment(
                text=en_text,
                language="en",
                out_path=raw_seg_path,
                clone_voice=False,
                speaker=speaker,
                target_duration=target_dur
            )

            raw_probe = probe_media_file(raw_seg_path)
            raw_dur = raw_probe.duration

            if raw_dur > target_dur:
                decision = calculate_timing_fit(
                    original_duration=target_dur,
                    tts_duration=raw_dur,
                    available_pre_silence=0.15,
                    available_post_silence=0.25
                )
                if decision.effective_stretch_ratio > 1.0 and abs(decision.effective_stretch_ratio - 1.0) > 0.05:
                    apply_audio_time_stretch(raw_seg_path, fitted_seg_path, decision.effective_stretch_ratio)
                else:
                    shutil.copy(raw_seg_path, fitted_seg_path)
            else:
                shutil.copy(raw_seg_path, fitted_seg_path)

            if raw_seg_path.exists():
                try:
                    raw_seg_path.unlink()
                except Exception:
                    pass

            fitted_probe = probe_media_file(fitted_seg_path)
            voice_label = "Kusal Clear Baritone (Sheikh)" if speaker == "sheikh_ul_wazaif" else "Reza Clear Narrator (Narrator)"
            print(f"  Segment {idx:03d} [{start:6.2f}s - {end:6.2f}s] ({target_dur:4.1f}s slot) -> [{voice_label}] {fitted_probe.duration:4.1f}s")

        seg_obj = Segment(
            id=idx,
            job_id=job_slug,
            idx=idx,
            start=start,
            end=end,
            speaker=speaker,
            src_text=ur_text,
            tgt_text=en_text,
            tts_path=str(fitted_seg_path)
        )
        segment_models.append(seg_obj)

    # Save accurate bilingual transcripts
    output_transcript_json = ROOT_DIR / f"{job_slug}_transcript.json"
    output_transcript_txt = ROOT_DIR / f"{job_slug}_transcript.txt"

    with open(output_transcript_json, "w", encoding="utf-8") as f:
        json.dump(aligned_segments, f, ensure_ascii=False, indent=2)

    with open(output_transcript_txt, "w", encoding="utf-8") as f:
        f.write(f"LECTURE DUBBER - BILINGUAL PRODUCTION TRANSCRIPT (ACCURATE & FAITHFUL)\nJob: {job_slug}\n" + "=" * 80 + "\n\n")
        for s in aligned_segments:
            sacred_tag = f" [SACRED ARABIC PRESERVED: {s['sacred_reason']}]" if s['is_sacred_arabic'] else ""
            f.write(f"[{s['start']:06.2f}s - {s['end']:06.2f}s] ({s['speaker']}){sacred_tag}\n")
            f.write(f"  URDU:    {s['ur_text']}\n")
            f.write(f"  ENGLISH: {s['en_text']}\n\n")

    # Timeline assembly & broadcast mixing
    print("\nAssembling Timeline Vocals & Mixing...")
    total_dur = 600.0
    dubbed_vocals_wav = work_dir / "dubbed_vocals.wav"
    assemble_timeline_vocals(
        segments=segment_models,
        total_duration=total_dur,
        output_vocals_path=dubbed_vocals_wav,
        sample_rate=44100
    )

    dub_mix_wav = work_dir / "dub_mix.wav"
    mix_vocals_and_background(
        dub_vocals_path=dubbed_vocals_wav,
        background_path=bg_wav,
        output_mix_path=dub_mix_wav,
        ducking_db=12.0,
        target_lufs=-16.0
    )

    # Final Video Muxing & MP3 Export
    source_10min = work_dir / f"{job_slug}_10min.mp4"
    if not source_10min.exists():
        source_10min = video_path

    if "uzbekistan" in job_slug:
        output_video_path = ROOT_DIR / "final_dubbed_uzbekistan_10min.mp4"
        output_mp3_path = ROOT_DIR / "dub_audio_uzbekistan_10min.mp3"
    else:
        output_video_path = ROOT_DIR / "final_dubbed_ramzan_taraveeh_10min.mp4"
        output_mp3_path = ROOT_DIR / "dub_audio_ramzan_taraveeh_10min.mp3"

    print(f"\nMuxing final video: {output_video_path.name}...")
    mux_video_and_audio(
        video_path=source_10min,
        audio_path=dub_mix_wav,
        output_path=output_video_path,
        target_lang="en",
        tolerance_seconds=3.0,
        title=f"Lecture Dubber - {job_slug}"
    )

    print(f"Exporting MP3: {output_mp3_path.name}...")
    export_dub_mp3(dub_mix_wav, output_mp3_path)

    print(f"JOB COMPLETED SUCCESSFULLY: {job_slug}")

def main():
    # Clip 1: Uzbekistan Journey (10 min)
    vid1 = ROOT_DIR / "Sheikh-ul-Wazaif Ke Sath Uzbekistan Ka Rohani Safar  Bukhara o Samarkand Ke Anokhay Raaz  2026 - Ubqari (1080p, h264).mp4"
    reprocess_clip("uzbekistan_journey_10m", vid1, UZBEKISTAN_TRANSLATIONS, "narrator")

    # Clip 2: Ramzan Taraveeh (10 min)
    vid2 = ROOT_DIR / "01 Ramzan Ul Mubarak After Taraveeh  Ubqari Tasbeeh Khana Lahore  06-05-2019 - Ubqari (1080p, h264).mp4"
    reprocess_clip("ramzan_taraveeh_10m", vid2, RAMZAN_TRANSLATIONS, "sheikh_ul_wazaif")

    print("\n" + "#" * 80)
    print("ALL 10-MINUTE PRODUCTIONS REPROCESSED WITH ACCURATE FAITHFUL TRANSLATIONS!")
    print("#" * 80)

if __name__ == "__main__":
    main()
