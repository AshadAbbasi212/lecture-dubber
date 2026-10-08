import os
import sys
import json
import time
import shutil
import math
from pathlib import Path
import numpy as np
import soundfile as sf

# Project root
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.db.models.segment import Segment
from backend.app.ingest.media_probe import probe_media_file
from backend.app.pipeline.audio_extractor import extract_audio_tracks
from backend.app.engines.separation.demucs_separator import DemucsSeparatorEngine
from backend.app.engines.asr.faster_whisper_asr import FasterWhisperASREngine
from backend.app.engines.translation.arabic_preserver import is_sacred_arabic_content, should_preserve_untranslated
from backend.app.engines.tts.voice_synthesizer import VoiceSynthesizer
from backend.app.pipeline.timing_fit import calculate_timing_fit, apply_audio_time_stretch
from backend.app.pipeline.audio_mixer import assemble_timeline_vocals, mix_vocals_and_background
from backend.app.pipeline.video_muxer import mux_video_and_audio, export_dub_mp3


def classify_speaker(segment_idx: int, start_time: float, text: str, clip_name: str) -> str:
    """
    Identifies speaker role based on acoustic/segment context and linguistic markers.
    """
    text_lower = text.lower()
    # Uzbekistan clip structure:
    # 0s - 45s: Narrator introducing Uzbekistan
    # 45s - 73s: Sheikh-ul-Wazaif speaking about Mawarannahr and spiritual elders
    # 73s - 120s+: Narrator describing caravan departure
    if "uzbekistan" in clip_name.lower():
        if 44.0 <= start_time <= 74.0:
            return "sheikh_ul_wazaif"
        elif "ہم اپنے بڑوں کا شکریہ" in text or "میں گیا" in text:
            return "sheikh_ul_wazaif"
        return "narrator"
    elif "ramzan" in clip_name.lower() or "taraveeh" in clip_name.lower():
        # In Taraveeh lecture: Sheikh-ul-Wazaif is main speaker
        return "sheikh_ul_wazaif"
    return "speaker_0"


def process_clip(
    video_path: Path,
    job_slug: str,
    output_video_path: Path,
    output_mp3_path: Path,
    output_transcript_path: Path,
    max_duration_seconds: float = 600.0,  # 10 minutes
    force_tts: bool = False
):
    print("\n" + "=" * 75)
    print(f"PROCESSING CLIP: {video_path.name}")
    print(f"Slug: {job_slug} | Target Duration: {max_duration_seconds}s | Force TTS: {force_tts}")
    print("=" * 75)

    work_dir = ROOT_DIR / "storage" / f"job_{job_slug}"
    work_dir.mkdir(parents=True, exist_ok=True)
    audio_dir = work_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    tts_dir = work_dir / "tts"
    tts_dir.mkdir(parents=True, exist_ok=True)

    # 1. Probe input video
    v_probe = probe_media_file(video_path)
    total_dur = min(v_probe.duration, max_duration_seconds)
    print(f"\n[Stage 1/7] Source Video: {v_probe.duration:.2f}s (Processing up to {total_dur:.2f}s), {v_probe.width}x{v_probe.height} {v_probe.video_codec}")

    # Trim to 10 minutes if original is slightly longer (or create trimmed source if needed)
    source_to_use = video_path
    if v_probe.duration > max_duration_seconds + 5.0:
        clipped_video = work_dir / f"{job_slug}_10min.mp4"
        if not clipped_video.exists():
            print(f"  Trimming to exact 10 minutes ({max_duration_seconds}s) with stream copy...")
            ffmpeg_cmd = settings.get_ffmpeg_cmd()
            cmd_trim = [
                ffmpeg_cmd, "-y",
                "-ss", "0",
                "-to", str(max_duration_seconds),
                "-i", str(video_path),
                "-c", "copy",
                "-movflags", "+faststart",
                str(clipped_video)
            ]
            import subprocess
            subprocess.run(cmd_trim, check=True)
        source_to_use = clipped_video
        v_probe = probe_media_file(source_to_use)
        total_dur = v_probe.duration
        print(f"  Using 10-minute clip: {clipped_video.name} ({total_dur:.2f}s)")

    # 2. Audio Extraction
    print(f"\n[Stage 2/7] Extracting Audio...")
    extract_audio_tracks(source_to_use, audio_dir)
    orig_wav = audio_dir / "original.wav"
    asr_wav = audio_dir / "asr_16k.wav"
    print(f"  Extracted original audio: {orig_wav.stat().st_size} bytes")

    # 3. Stem Separation (Demucs)
    print(f"\n[Stage 3/7] Isolating Speech and Preserving Background Music (Demucs)...")
    bg_wav = audio_dir / "background.wav"
    vocals_wav = audio_dir / "vocals.wav"
    if not bg_wav.exists() or not vocals_wav.exists() or bg_wav.stat().st_size < 1000:
        separator = DemucsSeparatorEngine()
        separator.separate(str(orig_wav), str(audio_dir))
    print(f"  Vocals isolated: {vocals_wav.stat().st_size} bytes (speech extracted)")
    print(f"  Background isolated: {bg_wav.stat().st_size} bytes (music & ambient sound preserved)")

    # 4. ASR Transcription & Arabic Preservation & Translation
    print(f"\n[Stage 4/7] Transcribing Urdu, Detecting Sacred Arabic & Translating...")
    asr_engine = FasterWhisperASREngine()
    
    # Transcribe Urdu
    transcript_file = work_dir / "transcript_ur.json"
    translation_file = work_dir / "translation_en.json"

    if transcript_file.exists() and translation_file.exists():
        with open(transcript_file, "r", encoding="utf-8") as f:
            ur_segments = json.load(f)
        with open(translation_file, "r", encoding="utf-8") as f:
            en_segments = json.load(f)
    else:
        # Run Faster-Whisper ASR
        asr_res = asr_engine.transcribe(str(vocals_wav), language="ur", task="transcribe")
        ur_segments = [
            {"idx": s.idx, "start": s.start, "end": s.end, "text": s.text}
            for s in asr_res.segments
        ]
        with open(transcript_file, "w", encoding="utf-8") as f:
            json.dump(ur_segments, f, ensure_ascii=False, indent=2)

        # Run Faster-Whisper Translation
        trans_res = asr_engine.transcribe(str(vocals_wav), task="translate")
        en_segments = [
            {"idx": s.idx, "start": s.start, "end": s.end, "text": s.text}
            for s in trans_res.segments
        ]
        with open(translation_file, "w", encoding="utf-8") as f:
            json.dump(en_segments, f, ensure_ascii=False, indent=2)

    print(f"  Transcribed {len(ur_segments)} Urdu segments and {len(en_segments)} English segments.")

    # Align Urdu and English segments and apply Arabic / Quranic / Hadith preservation
    aligned_segments = []
    for i, u_seg in enumerate(ur_segments):
        start = u_seg["start"]
        end = u_seg["end"]
        dur = end - start
        ur_text = u_seg["text"].strip()

        # Find best matching translated text
        best_en = ""
        for e_seg in en_segments:
            # Overlap check
            if max(start, e_seg["start"]) < min(end, e_seg["end"]):
                best_en += (" " + e_seg["text"].strip()).strip()

        if not best_en:
            best_en = en_segments[min(i, len(en_segments) - 1)]["text"].strip() if en_segments else ur_text

        # Check for Quranic verse, Hadith, or sacred Arabic dhikr
        is_sacred, sacred_reason = is_sacred_arabic_content(ur_text)
        speaker = classify_speaker(i + 1, start, ur_text, job_slug)

        aligned_segments.append({
            "idx": i + 1,
            "start": round(start, 2),
            "end": round(end, 2),
            "duration": round(dur, 2),
            "speaker": speaker,
            "is_sacred_arabic": is_sacred,
            "sacred_reason": sacred_reason,
            "ur_text": ur_text,
            "en_text": best_en
        })

    # Save aligned bilingual transcript
    with open(output_transcript_path, "w", encoding="utf-8") as f:
        json.dump(aligned_segments, f, ensure_ascii=False, indent=2)

    txt_transcript = output_transcript_path.with_suffix(".txt")
    with open(txt_transcript, "w", encoding="utf-8") as f:
        f.write(f"LECTURE DUBBER - BILINGUAL PRODUCTION TRANSCRIPT\nJob: {job_slug}\n" + "=" * 80 + "\n\n")
        for s in aligned_segments:
            sacred_tag = f" [SACRED ARABIC PRESERVED: {s['sacred_reason']}]" if s['is_sacred_arabic'] else ""
            f.write(f"[{s['start']:06.2f}s - {s['end']:06.2f}s] ({s['speaker']}){sacred_tag}\n")
            f.write(f"  URDU:    {s['ur_text']}\n")
            f.write(f"  ENGLISH: {s['en_text']}\n\n")

    # 5. High-Clarity Voice Synthesis (Microsoft David Engine)
    print(f"\n[Stage 5/7] High-Clarity English Speech Synthesis (Microsoft David Engine)...")
    synthesizer = VoiceSynthesizer()
    segment_models = []

    # Read vocals audio in case we preserve original recitation for sacred Arabic
    voc_data, voc_sr = sf.read(str(vocals_wav), dtype="float32")
    if voc_data.ndim == 1:
        voc_data = np.column_stack([voc_data, voc_data])

    for s in aligned_segments:
        idx = s["idx"]
        start = s["start"]
        end = s["end"]
        target_dur = end - start
        is_sacred = s["is_sacred_arabic"]
        speaker = s["speaker"]
        fitted_seg_path = tts_dir / f"seg_{idx:03d}_fitted.wav"

        if not force_tts and fitted_seg_path.exists() and fitted_seg_path.stat().st_size > 1000:
            seg_obj = Segment(
                id=idx,
                job_id=job_slug,
                idx=idx,
                start=start,
                end=end,
                speaker=speaker,
                src_text=s["ur_text"],
                tgt_text=s["en_text"],
                tts_path=str(fitted_seg_path)
            )
            segment_models.append(seg_obj)
            continue

        if is_sacred:
            # PRESERVE ORIGINAL ARABIC RECITATION (Quran / Hadith)
            # Slice the exact original vocal audio for this recitation
            start_samp = int(round(start * voc_sr))
            end_samp = min(int(round(end * voc_sr)), len(voc_data))
            recitation_audio = voc_data[start_samp:end_samp]
            sf.write(str(fitted_seg_path), recitation_audio, voc_sr)
            print(f"  Segment {idx:03d} [{start:6.2f}s - {end:6.2f}s] -> Sacred Arabic Recitation Preserved Verbatim")
        else:
            # Synthesize in English with speaker-specific neural voice
            tts_text = s["en_text"]
            raw_seg_path = tts_dir / f"seg_{idx:03d}_raw.wav"

            # Synthesize with speaker-specific voice and dynamic length-scale
            synthesizer.synthesize_segment(
                text=tts_text,
                language="en",
                out_path=raw_seg_path,
                clone_voice=False,
                speaker=speaker,
                target_duration=target_dur
            )

            raw_probe = probe_media_file(raw_seg_path)
            raw_dur = raw_probe.duration

            # Calculate timing fit
            decision = calculate_timing_fit(
                original_duration=target_dur,
                tts_duration=raw_dur,
                available_pre_silence=0.15,
                available_post_silence=0.25
            )

            # Apply gentle time stretch if ratio is between 0.85 and 1.18
            if decision.effective_stretch_ratio != 1.0 and abs(decision.effective_stretch_ratio - 1.0) > 0.05:
                apply_audio_time_stretch(raw_seg_path, fitted_seg_path, decision.effective_stretch_ratio)
            else:
                shutil.copy(raw_seg_path, fitted_seg_path)

            if raw_seg_path.exists():
                try:
                    raw_seg_path.unlink()
                except Exception:
                    pass

            fitted_probe = probe_media_file(fitted_seg_path)
            voice_label = "Kusal (Sheikh)" if speaker == "sheikh_ul_wazaif" else "Reza (Narrator)"
            print(f"  Segment {idx:03d} [{start:6.2f}s - {end:6.2f}s] ({target_dur:4.1f}s slot) -> [{voice_label}] {fitted_probe.duration:4.1f}s")

        seg_obj = Segment(
            id=idx,
            job_id=job_slug,
            idx=idx,
            start=start,
            end=end,
            speaker=speaker,
            src_text=s["ur_text"],
            tgt_text=s["en_text"],
            tts_path=str(fitted_seg_path)
        )
        segment_models.append(seg_obj)

    # 6. Timeline Assembly & Broadcast Audio Mastering (-12 dB Ducking, -16 LUFS)
    print(f"\n[Stage 6/7] Timeline Vocal Assembly & Mastering (-12 dB Broadcast Ducking)...")
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
        ducking_db=12.0,  # Background music continues at -12 dB (25% volume) under voice
        target_lufs=-16.0
    )
    print(f"  Mastered Audio Mix: {dub_mix_wav.name} (-16 LUFS, smooth broadcast ducking)")

    # 7. Video Muxing & MP3 Export
    print(f"\n[Stage 7/7] Lossless Video Muxing & MP3 Export...")
    mux_result = mux_video_and_audio(
        video_path=source_to_use,
        audio_path=dub_mix_wav,
        output_path=output_video_path,
        target_lang="en",
        tolerance_seconds=3.0,
        title=f"Lecture Dubber - {job_slug}"
    )

    export_dub_mp3(dub_mix_wav, output_mp3_path)

    print("\n" + "=" * 75)
    print(f"CLIP COMPLETED SUCCESSFULLY: {job_slug}")
    print(f"  Final Video: {output_video_path.resolve()} ({output_video_path.stat().st_size / (1024*1024):.2f} MB)")
    print(f"  MP3 Audio:   {output_mp3_path.resolve()} ({output_mp3_path.stat().st_size / (1024*1024):.2f} MB)")
    print(f"  Transcript:  {output_transcript_path.resolve()}")
    print("=" * 75)

    return {
        "job_slug": job_slug,
        "video_path": str(output_video_path),
        "mp3_path": str(output_mp3_path),
        "transcript_json": str(output_transcript_path),
        "transcript_txt": str(txt_transcript),
        "duration": mux_result.duration,
        "segments_count": len(aligned_segments)
    }


def main():
    print("=" * 80)
    print("LECTURE DUBBER - AUTONOMOUS DUAL 10-MINUTE PRODUCTION RUNNER")
    print("=" * 80)

    # Clip 1: Uzbekistan Journey (10-minute segment)
    clip1_src = ROOT_DIR / "Sheikh-ul-Wazaif Ke Sath Uzbekistan Ka Rohani Safar  Bukhara o Samarkand Ke Anokhay Raaz  2026 - Ubqari (1080p, h264).mp4"
    clip1_out_video = ROOT_DIR / "final_dubbed_uzbekistan_10min.mp4"
    clip1_out_mp3 = ROOT_DIR / "dub_audio_uzbekistan_10min.mp3"
    clip1_out_trans = ROOT_DIR / "uzbekistan_10min_transcript.json"

    # Clip 2: Ramzan Taraveeh Lecture (10-minute segment)
    clip2_src = ROOT_DIR / "01 Ramzan Ul Mubarak After Taraveeh  Ubqari Tasbeeh Khana Lahore  06-05-2019 - Ubqari (1080p, h264).mp4"
    clip2_out_video = ROOT_DIR / "final_dubbed_ramzan_taraveeh_10min.mp4"
    clip2_out_mp3 = ROOT_DIR / "dub_audio_ramzan_taraveeh_10min.mp3"
    clip2_out_trans = ROOT_DIR / "ramzan_taraveeh_10min_transcript.json"

    force_tts = True  # Ensure fresh synthesis with Microsoft David high-clarity voice
    results = []

    # Process Clip 1
    if clip1_src.is_file():
        res1 = process_clip(
            video_path=clip1_src,
            job_slug="uzbekistan_journey_10m",
            output_video_path=clip1_out_video,
            output_mp3_path=clip1_out_mp3,
            output_transcript_path=clip1_out_trans,
            max_duration_seconds=600.0,
            force_tts=force_tts
        )
        results.append(res1)

    # Process Clip 2
    if clip2_src.is_file():
        res2 = process_clip(
            video_path=clip2_src,
            job_slug="ramzan_taraveeh_10m",
            output_video_path=clip2_out_video,
            output_mp3_path=clip2_out_mp3,
            output_transcript_path=clip2_out_trans,
            max_duration_seconds=600.0,
            force_tts=force_tts
        )
        results.append(res2)

    summary_file = ROOT_DIR / "production_run_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n" + "#" * 80)
    print("ALL PRODUCTION RUNS COMPLETE! SUMMARY RECORDED AT:", summary_file)
    print("#" * 80)


if __name__ == "__main__":
    main()
