"""
Generate 10-Second Audition Preview Audio Clips for Additional Male & Female Voices
Saves high-quality 24kHz studio WAV files to frontend/public/voices/
"""

import sys
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.engines.tts.voice_synthesizer import FallbackTTSEngine
from backend.app.ingest.media_probe import probe_media_file

VOICE_AUDITIONS = [
    # Spanish Female
    ("es", "sharvard", "sharvard.wav", "Hola a todos, bienvenidos a nuestra clase de hoy donde exploraremos los conceptos científicos esenciales."),
    # German Female
    ("de", "kerstin", "kerstin.wav", "Guten Tag liebe Studierende, ich begrüße Sie herzlich zu unserer heutigen akademischen Vorlesung."),
    # Hindi Female
    ("hi", "priyamvada", "priyamvada.wav", "नमस्ते आप सभी का आज के शैक्षणिक व्याख्यान में हार्दिक स्वागत है। आज हम मुख्य सिद्धांतों का अध्ययन करेंगे।"),
    # French Male
    ("fr", "gilles", "gilles.wav", "Bonjour à tous et bienvenue à ce cours universitaire sur les fondements théoriques des sciences modernes."),
    # Italian Male
    ("it", "riccardo", "riccardo.wav", "Buongiorno a tutti, benvenuti a questa lezione universitaria sui fondamenti dell'ingegneria e della scienza."),
    # Chinese Male
    ("zh", "chaowen", "chaowen.wav", "各位同学大家好，欢迎来到今天的学术讲座，今天我们重点探讨计算机科学的核心理论。"),
    # Arabic Female
    ("ar", "maryam", "maryam.wav", "أهلاً ومرحباً بكم جميعاً في هذه المحاضرة الأكاديمية القيمة، حيث نتناول أهم المبادئ العلمية بدقة."),
    # Urdu Female
    ("ur", "ayesha", "ayesha.wav", "تمام طلباء کو آج کے تعلیمی لیکچر میں خوش آمدید، آج ہم اہم سائنسی اور معلوماتی اصولوں کا جائزہ لیں گے۔"),
    # Urdu Male
    ("ur", "tariq", "tariq.wav", "آج کے اس اہم فکری و علمی بیان میں ہم انسانی کامیابی کے حقیقی مفہوم اور مقاصد پر روشنی ڈالیں گے۔"),
    # Portuguese Female
    ("pt", "larissa", "larissa.wav", "Olá a todos e bem-vindos a mais uma aula teórica sobre os fundamentos essenciais da ciência contemporânea."),
    # Turkish Female
    ("tr", "leyla", "leyla.wav", "Herkese merhaba arkadaşlar, bugünkü akademik dersimizde temel kavramları ve modern bilimsel gelişmeleri inceleyeceğiz.")
]

def main():
    print("==================================================================")
    print(" Generating Audition Previews for Male & Female Voice Roster")
    print("==================================================================")

    out_dir = Path("frontend/public/voices").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    engine = FallbackTTSEngine()

    for lang, voice_id, filename, script in VOICE_AUDITIONS:
        out_path = out_dir / filename
        print(f"Generating [{lang.upper()}] {voice_id} -> {filename}...")
        try:
            dur = engine.synthesize(
                text=script,
                language=lang,
                out_path=str(out_path),
                voice=voice_id,
                target_duration=10.0
            )
            probe = probe_media_file(out_path)
            print(f"  [OK] {filename}: {probe.duration:.2f}s ({out_path.stat().st_size} bytes)")
        except Exception as e:
            print(f"  [ERROR] Failed to synthesize {voice_id}: {e}")

    print("\nAudition generation complete!")

if __name__ == "__main__":
    main()
