"""
Generate clean comparison video assets for GitHub:
1. docs/assets/original_lecture.mp4 (Source English lecture)
2. docs/assets/dubbed_lecture_urdu.mp4 (Dubbed Urdu lecture with Tariq neural voice + ducked acoustics)
"""

import sys
import math
import shutil
import subprocess
from pathlib import Path
import numpy as np
import soundfile as sf

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.engines.tts.voice_synthesizer import FallbackTTSEngine
from backend.app.db.models.segment import Segment
from backend.app.pipeline.audio_mixer import assemble_timeline_vocals, mix_vocals_and_background
from backend.app.pipeline.video_muxer import mux_video_and_audio

FEYNMAN_URDU_SEGMENTS = [
    (1, 0.02, 3.02, "اب میں اس بات پر گفتگو کروں گا کہ ہم نیا قانون کیسے تلاش کرتے ہیں۔"),
    (2, 4.12, 6.78, "عام طور پر، ہم درج ذیل طریقے سے نیا قانون تلاش کرتے ہیں۔"),
    (3, 7.02, 15.08, "پہلے ہم ایک اندازہ لگاتے ہیں، پھر اس اندازے کے نتائج کا حساب لگاتے ہیں،"),
    (4, 17.04, 21.38, "تاکہ دیکھیں کہ اگر یہ قانون درست ہے تو اس کے کیا اثرات اور نتائج ہوں گے۔"),
    (5, 22.06, 29.98, "اور پھر ہم ان حسابی نتائج کا موازنہ قدرت، تجربات اور مشاہدات سے کرتے ہیں،"),
    (6, 32.66, 35.80, "ہم براہ راست مشاہدے سے موازنہ کرتے ہیں تاکہ دیکھیں کہ کیا یہ کام کرتا ہے۔"),
    (7, 39.64, 44.09, "اگر یہ تجربے سے اختلاف رکھتا ہے، تو یہ غلط ہے۔"),
    (8, 45.96, 48.68, "اس سادہ سے جملے میں ہی سائنس کی اصل کلید چھپی ہے۔"),
    (9, 49.42, 51.56, "اس سے کوئی فرق نہیں پڑتا کہ آپ کا اندازہ کتنا خوبصورت ہے۔"),
    (10, 51.64, 55.42, "اس سے کوئی فرق نہیں پڑتا کہ اندازہ کس نے لگایا یا اس کا نام کیا ہے۔"),
    (11, 55.86, 58.84, "اگر یہ تجربے کے خلاف ہے، تو یہ غلط ہے۔"),
    (12, 59.26, 60.04, "بس یہی سب کچھ ہے، اس کے علاوہ کچھ نہیں۔")
]


def main():
    print("=================================================================", flush=True)
    print(" GENERATING ORIGINAL & DUBBED COMPARISON ASSETS", flush=True)
    print("=================================================================", flush=True)

    source_video = ROOT_DIR / "storage" / "test_feynman_1min.mp4"
    if not source_video.is_file():
        print(f"Source video not found: {source_video}")
        sys.exit(1)

    work_dir = ROOT_DIR / "storage" / "comparison_build"
    tts_dir = work_dir / "tts"
    work_dir.mkdir(parents=True, exist_ok=True)
    tts_dir.mkdir(parents=True, exist_ok=True)

    assets_dir = ROOT_DIR / "docs" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    # 1. Synthesize 12 segments into Urdu with Tariq
    print("\n[Step 1/4] Synthesizing 12 Urdu segments with Tariq neural voice...", flush=True)
    tts = FallbackTTSEngine()
    seg_models = []

    for idx, start, end, text in FEYNMAN_URDU_SEGMENTS:
        dur = end - start
        out_wav = tts_dir / f"seg_{idx:04d}.wav"
        print(f"  Segment {idx} ({dur:.2f}s): {text[:40]}...", flush=True)
        tts.synthesize(
            text=text,
            language="ur",
            out_path=str(out_wav),
            target_duration=dur,
            voice="tariq"
        )
        s = Segment(
            id=f"seg-{idx}",
            job_id="comparison-demo",
            idx=idx,
            start=start,
            end=end,
            speaker="speaker_0",
            src_text="",
            tgt_text=text,
            tts_path=str(out_wav)
        )
        seg_models.append(s)

    # 2. Assemble timeline vocals
    print("\n[Step 2/4] Assembling full 62.55s dubbed vocal track...", flush=True)
    dub_vocals_path = work_dir / "dub_vocals.wav"
    assemble_timeline_vocals(seg_models, 62.55, dub_vocals_path)

    # 3. Mix with background audio
    print("\n[Step 3/4] Mixing with isolated background acoustics and EBU R128 ducking...", flush=True)
    bg_path = ROOT_DIR / "storage" / "jobs" / "0d1a458e-4efe-4369-b04e-172a25ba192f" / "audio" / "background.wav"
    if not bg_path.is_file():
        # Fallback to silent/mild background
        bg_path = work_dir / "bg_silence.wav"
        silence = np.zeros((int(44100 * 62.55), 2), dtype=np.float32)
        sf.write(str(bg_path), silence, 44100)

    dub_mix_path = work_dir / "dub_mix.wav"
    mix_vocals_and_background(
        dub_vocals_path=dub_vocals_path,
        background_path=bg_path,
        output_mix_path=dub_mix_path,
        ducking_db=12.0,
        target_lufs=-16.0
    )

    # 4. Mux dubbed video (Single primary dubbed audio track only!)
    print("\n[Step 4/4] Muxing video with primary dubbed audio track...", flush=True)
    dubbed_video_path = assets_dir / "dubbed_lecture_urdu.mp4"
    original_video_path = assets_dir / "original_lecture_english.mp4"

    # Copy original video directly to assets
    shutil.copy2(str(source_video), str(original_video_path))
    print(f"  Copied original English lecture to: {original_video_path.name} ({original_video_path.stat().st_size/1024/1024:.2f} MB)")

    # Build clean single-audio MP4 for dubbed version
    cmd = [
        "ffmpeg", "-y",
        "-i", str(source_video),
        "-i", str(dub_mix_path),
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-metadata", "title=Lecture Dubber - Dubbed in Urdu (Tariq Scholar)",
        str(dubbed_video_path)
    ]
    subprocess.run(cmd, check=True)
    print(f"  Muxed dubbed Urdu lecture to: {dubbed_video_path.name} ({dubbed_video_path.stat().st_size/1024/1024:.2f} MB)")

    # Also update demo_dubbed_lecture.mp4 to point to this single-audio dubbed version
    shutil.copy2(str(dubbed_video_path), str(assets_dir / "demo_dubbed_lecture.mp4"))
    print(f"  Updated demo_dubbed_lecture.mp4 with clean single-audio Urdu track.")

    print("\n=================================================================", flush=True)
    print(" COMPARISON ASSETS SUCCESSFULLY GENERATED!", flush=True)
    print("=================================================================", flush=True)


if __name__ == "__main__":
    main()
