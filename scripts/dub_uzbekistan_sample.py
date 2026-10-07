import os
import sys
import json
import time
import shutil
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.db.models.segment import Segment
from backend.app.ingest.media_probe import probe_media_file
from backend.app.pipeline.audio_extractor import extract_audio_tracks
from backend.app.pipeline.reference_clip import build_reference_clip
from backend.app.pipeline.timing_fit import calculate_timing_fit, apply_audio_time_stretch
from backend.app.engines.tts.voice_synthesizer import VoiceSynthesizer
from backend.app.pipeline.audio_mixer import assemble_timeline_vocals, mix_vocals_and_background
from backend.app.pipeline.video_muxer import mux_video_and_audio, export_dub_mp3

SEGMENTS = [
    {
        "idx": 1,
        "start": 0.0,
        "end": 11.8,
        "speaker": "narrator",
        "src_text": "اُزبیکستان وسطی ایشیا کی ایک ایسی سرزمین، جہاں صدیوں پرانی تاریخ آج بھی مسجدوں، مدرسوں، خانقاہوں، بازاروں، مزارات اور قدیم راستوں میں سانس لیتی ہے۔",
        "tgt_text": "Uzbekistan is a land of Central Asia where centuries-old history still breathes in mosques, madrasas, shrines, and ancient paths."
    },
    {
        "idx": 2,
        "start": 11.8,
        "end": 23.5,
        "speaker": "narrator",
        "src_text": "جی ہاں، یہ ہے اُزبیکستان، وہ خطہ جو نہ صرف اپنی تہذیبی عظمت اور فن تعمیر کے لیے، بلکہ علم، تصوف اور روحانیت کی ایک گہری اور طویل روایت کے لیے بھی پہچانا جاتا ہے۔",
        "tgt_text": "Yes, this is Uzbekistan, a region renowned not only for its cultural heritage and architecture, but also for its profound tradition of spirituality."
    },
    {
        "idx": 3,
        "start": 23.5,
        "end": 44.9,
        "speaker": "narrator",
        "src_text": "جی ہاں، یہ اُزبیکستان کی وہ سرزمین ہے جہاں محدثین، فقہا، مشائخ اور صوفیائے کرام کی عظیم شخصیات نے علم و معرفت کے چراغ روشن کیے۔ بخارا اور سمرقند کی زمین آج بھی ان بزرگوں کے مزارات، خانقاہوں اور یادگاروں کو اپنے اندر سمیٹے ہوئے ہے۔ آخر شیخ الوظائف بار بار اُزبیکستان ہی کیوں جاتے ہیں؟",
        "tgt_text": "This is Uzbekistan's sacred soil, where noble hadith scholars, jurists, and Sufis lit the lamps of knowledge. The land of Bukhara and Samarkand still preserves their sacred memorials. Why does Sheikh-ul-Wazaif visit Uzbekistan repeatedly?"
    },
    {
        "idx": 4,
        "start": 45.1,
        "end": 73.0,
        "speaker": "sheikh_ul_wazaif",
        "src_text": "ہم اپنے بڑوں کا شکریہ ادا کرنے جا رہے ہیں۔ یہاں پڑی ہے ماوراء النہر، یہاں پڑی ہے جہاں سے اولیاء صالحین آئے، یہاں پڑی ہے جہاں سے بڑی بڑی ہستیاں آئیں، جہاں سے نیک دل بادشاہ آئے، جہاں سے سچے سوداگر آئے، اور یہی وہ راستہ ہے جہاں سے وہ لوگ آئے جنہوں نے ہمیں اس رب کی، اس کے حبیب کی پہچان کروائی۔",
        "tgt_text": "We are going to express gratitude to our spiritual elders. Here lies Mawarannahr, where righteous saints, noble personalities, and honest merchants came. This is the path of those who guided us to the knowledge of God and His Beloved Prophet."
    },
    {
        "idx": 5,
        "start": 73.5,
        "end": 84.1,
        "speaker": "narrator",
        "src_text": "چار ستمبر دو ہزار چھبیس بروز جمعہ اسی سرزمین کی طرف شیخ الوظائف کے ساتھ تقریباً ایک سو اٹھائیس سے زائد مرد و خواتین پر مشتمل ایک قافلہ روانہ ہوا۔",
        "tgt_text": "On Friday, September 4th, 2026, a caravan comprising over one hundred and twenty-eight men and women departed alongside Sheikh-ul-Wazaif toward this historic land."
    },
    {
        "idx": 6,
        "start": 84.1,
        "end": 87.6,
        "speaker": "narrator",
        "src_text": "تاشقند سے بخارا اور بخارا سے سمرقند تک۔",
        "tgt_text": "From Tashkent to Bukhara, and from Bukhara to Samarkand."
    },
    {
        "idx": 7,
        "start": 87.6,
        "end": 93.2,
        "speaker": "narrator",
        "src_text": "مگر یہ سفر صرف تاریخی عمارتیں دیکھنے، قدیم شہروں کی سیر کرنے کا سفر نہیں تھا۔",
        "tgt_text": "Yet this journey was not merely to observe historical architecture or explore ancient cities."
    },
    {
        "idx": 8,
        "start": 93.2,
        "end": 102.4,
        "speaker": "narrator",
        "src_text": "یہ اولیائے کرام کے مزارات پر حاضری، محدثین کی یادگاروں سے فیضیاب، روحانیت کی تلاش اور روح کی ترقی کا سفر بھی تھا۔",
        "tgt_text": "It was a sacred pilgrimage to visit shrines of saints, draw spiritual blessing from hadith scholars, and seek the advancement of the soul."
    },
    {
        "idx": 9,
        "start": 102.4,
        "end": 114.6,
        "speaker": "narrator",
        "src_text": "سفر کے مختلف مراحل میں شیخ الوظائف نے قافلے کو ایسے اعمال، وظائف، اذکار، مراقبات اور تعویذات بھی دیے جن سے زندگی میں عزت، شہرت، رزق اور دولت ملے۔",
        "tgt_text": "Throughout the journey, Sheikh-ul-Wazaif bestowed upon the caravan sacred prayers, wazaif, litanies, and meditations that bring honour, livelihood, and blessings."
    },
    {
        "idx": 10,
        "start": 114.6,
        "end": 120.0,
        "speaker": "narrator",
        "src_text": "کامیابی، جادو، جنات اور نظر بد سے حفاظت، اور روحانیت میں عروج ہو۔",
        "tgt_text": "Bringing success, divine protection from harm and negative energies, and spiritual elevation."
    }
]

def main():
    print("=" * 70)
    print("LECTURE DUBBER - LOCAL URDU TO ENGLISH DUBBING PIPELINE")
    print("Target Video: uzbekistan_sample_2min.mp4 (120s, 1080p)")
    print("=" * 70)

    work_dir = ROOT_DIR / "storage" / "uzbekistan_demo_2min"
    work_dir.mkdir(parents=True, exist_ok=True)
    audio_dir = work_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    tts_dir = work_dir / "tts"
    tts_dir.mkdir(parents=True, exist_ok=True)

    input_video = ROOT_DIR / "uzbekistan_sample_2min.mp4"
    if not input_video.is_file():
        print(f"Error: Input video not found at {input_video}")
        return

    # Step 1: Probe video
    probe = probe_media_file(input_video)
    print(f"\n[Stage 1/6] Source Video Probed:")
    print(f"  Duration: {probe.duration:.2f}s | Resolution: {probe.width}x{probe.height} | Codec: {probe.video_codec}")

    # Step 2: Audio extraction
    print(f"\n[Stage 2/6] Extracting Audio Tracks...")
    extract_audio_tracks(input_video, audio_dir)
    orig_wav = audio_dir / "original.wav"
    asr_wav = audio_dir / "asr_16k.wav"
    print(f"  Extracted: {orig_wav.name} ({orig_wav.stat().st_size} bytes)")
    print(f"  Extracted: {asr_wav.name} ({asr_wav.stat().st_size} bytes)")

    # Step 2b: Background audio isolation (Demucs stem separation)
    bg_wav = audio_dir / "background.wav"
    vocals_wav = audio_dir / "vocals.wav"
    if not bg_wav.exists() or not vocals_wav.exists():
        print("  Running Demucs stem separation to remove original vocal track from background...")
        from backend.app.engines.separation.demucs_separator import DemucsSeparatorEngine
        sep = DemucsSeparatorEngine()
        sep.separate(str(orig_wav), str(audio_dir))
    print(f"  Isolated background track: {bg_wav.name} ({bg_wav.stat().st_size} bytes, speech removed)")

    # Pre-build segment models
    segment_objs = [
        Segment(
            id=seg["idx"],
            job_id="demo_uzbekistan_2min",
            idx=seg["idx"],
            start=seg["start"],
            end=seg["end"],
            speaker=seg["speaker"],
            src_text=seg["src_text"],
            tgt_text=seg["tgt_text"]
        )
        for seg in SEGMENTS
    ]

    # Step 3: Reference speaker clip extraction
    print(f"\n[Stage 3/6] Building Speaker Reference Timbre...")
    ref_clip_path = work_dir / "reference_clip.wav"
    build_reference_clip(orig_wav, segment_objs, ref_clip_path, target_duration=10.0)
    print(f"  Speaker reference clip created: {ref_clip_path.name}")

    # Step 4: Speech Synthesis & Timing Fit
    print(f"\n[Stage 4/6] Synthesizing English Speech for {len(SEGMENTS)} Segments...")
    synthesizer = VoiceSynthesizer()
    segment_objs = []

    for seg in SEGMENTS:
        idx = seg["idx"]
        tgt_text = seg["tgt_text"]
        target_dur = seg["end"] - seg["start"]
        raw_seg_path = tts_dir / f"seg_{idx}_raw.wav"
        fitted_seg_path = tts_dir / f"seg_{idx}_fitted.wav"

        # Synthesize English audio via Windows SAPI David
        synthesizer.synthesize_segment(
            text=tgt_text,
            language="en",
            out_path=raw_seg_path,
            reference_clip=ref_clip_path,
            clone_voice=False
        )

        raw_probe = probe_media_file(raw_seg_path)
        raw_dur = raw_probe.duration

        # Calculate timing fit
        decision = calculate_timing_fit(
            original_duration=target_dur,
            tts_duration=raw_dur,
            available_pre_silence=0.2,
            available_post_silence=0.5
        )

        # Apply time stretch if needed to perfectly fit the segment window
        if decision.effective_stretch_ratio != 1.0:
            apply_audio_time_stretch(raw_seg_path, fitted_seg_path, decision.effective_stretch_ratio)
        else:
            shutil.copy(raw_seg_path, fitted_seg_path)

        fitted_probe = probe_media_file(fitted_seg_path)
        print(f"  Segment {idx:02d} [{seg['start']:5.1f}s - {seg['end']:5.1f}s] ({target_dur:4.1f}s slot) -> TTS {raw_dur:4.1f}s (ratio {decision.effective_stretch_ratio:.2f}x) -> {fitted_probe.duration:4.1f}s")

        seg_model = Segment(
            id=idx,
            job_id="demo_uzbekistan_2min",
            idx=idx,
            start=seg["start"],
            end=seg["end"],
            speaker=seg["speaker"],
            src_text=seg["src_text"],
            tgt_text=tgt_text,
            tts_path=str(fitted_seg_path)
        )
        segment_objs.append(seg_model)

    # Step 5: Timeline Vocal Assembly & Mixing
    print(f"\n[Stage 5/6] Timeline Vocal Assembly & Audio Mastering...")
    dubbed_vocals_wav = work_dir / "dubbed_vocals.wav"
    assemble_timeline_vocals(
        segments=segment_objs,
        total_duration=probe.duration,
        output_vocals_path=dubbed_vocals_wav,
        sample_rate=44100
    )

    dub_mix_wav = work_dir / "dub_mix.wav"
    mix_vocals_and_background(
        dub_vocals_path=dubbed_vocals_wav,
        background_path=bg_wav,
        output_mix_path=dub_mix_wav,
        ducking_db=36.0,
        target_lufs=-16.0
    )
    print(f"  Mastered Audio Mix: {dub_mix_wav.name} (-16 LUFS, background silenced during speech)")

    # Step 6: Video Muxing & MP3 Export
    print(f"\n[Stage 6/6] Muxing Final Dubbed Video...")
    final_video_path = ROOT_DIR / "final_dubbed_uzbekistan_2min.mp4"
    final_mp3_path = ROOT_DIR / "dub_audio_uzbekistan_2min.mp3"

    mux_result = mux_video_and_audio(
        video_path=input_video,
        audio_path=dub_mix_wav,
        output_path=final_video_path,
        target_lang="en",
        title="Lecture Dubber - Uzbekistan Journey (English Dubbed Highlight)"
    )

    export_dub_mp3(dub_mix_wav, final_mp3_path)

    # Save bilingual transcript files
    transcript_json_path = ROOT_DIR / "uzbekistan_bilingual_transcript.json"
    transcript_txt_path = ROOT_DIR / "uzbekistan_bilingual_transcript.txt"

    with open(transcript_json_path, "w", encoding="utf-8") as f:
        json.dump(SEGMENTS, f, ensure_ascii=False, indent=2)

    with open(transcript_txt_path, "w", encoding="utf-8") as f:
        f.write("LECTURE DUBBER - BILINGUAL TRANSCRIPT (URDU -> ENGLISH)\n")
        f.write("Video: Sheikh-ul-Wazaif Ke Sath Uzbekistan Ka Rohani Safar (Highlight Clip)\n")
        f.write("=" * 80 + "\n\n")
        for s in SEGMENTS:
            f.write(f"[{s['start']:05.1f}s - {s['end']:05.1f}s] ({s['speaker']})\n")
            f.write(f"  URDU:    {s['src_text']}\n")
            f.write(f"  ENGLISH: {s['tgt_text']}\n\n")

    print("\n" + "=" * 70)
    print("SUCCESS! DUBBED ASSETS GENERATED:")
    print(f"  1. Final Dubbed Video: {final_video_path.resolve()}")
    print(f"     Size: {final_video_path.stat().st_size / (1024*1024):.2f} MB | Duration: {mux_result.duration:.2f}s")
    print(f"  2. Standalone MP3:     {final_mp3_path.resolve()}")
    print(f"     Size: {final_mp3_path.stat().st_size / 1024:.1f} KB")
    print(f"  3. Bilingual Transcript (JSON): {transcript_json_path.resolve()}")
    print(f"  4. Bilingual Transcript (TXT):  {transcript_txt_path.resolve()}")
    print("=" * 70)

if __name__ == "__main__":
    main()
