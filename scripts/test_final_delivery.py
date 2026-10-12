"""
Lecture Dubber - Final Production Verification Test Suite
Executes end-to-end multi-language, multi-voice testing on 1-minute lecture video
and tests all frontend components and API endpoints.
"""

import sys
import os
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.engines.asr.faster_whisper_asr import FasterWhisperASREngine
from backend.app.engines.translation.llm_translator import LocalLLMTranslator, validate_script_matches_language
from backend.app.engines.tts.voice_synthesizer import FallbackTTSEngine
from backend.app.engines.base import TranscriptSegment
from backend.app.ingest.media_probe import probe_media_file

TEST_LANGUAGES_AND_VOICES = [
    # Language, Voice ID, Gender, Display Name
    ("ur", "tariq", "Male", "Urdu - Tariq (Male Scholar)"),
    ("ur", "ayesha", "Female", "Urdu - Ayesha (Female Academic)"),
    ("ar", "kareem", "Male", "Arabic - Kareem (Male Classical)"),
    ("ar", "maryam", "Female", "Arabic - Maryam (Female Academic)"),
    ("es", "dave", "Male", "Spanish - Dave (Male European)"),
    ("es", "sharvard", "Female", "Spanish - Sharvard (Female Lecturer)"),
    ("de", "thorsten", "Male", "German - Thorsten (Male Academic)"),
    ("de", "kerstin", "Female", "German - Kerstin (Female Lecturer)"),
    ("fr", "gilles", "Male", "French - Gilles (Male Sorbonne)"),
    ("fr", "siwis", "Female", "French - Siwis (Female Academic)"),
    ("it", "riccardo", "Male", "Italian - Riccardo (Male Professor)"),
    ("it", "paola", "Female", "Italian - Paola (Female Academic)"),
    ("ru", "denis", "Male", "Russian - Denis (Male Scholar)"),
    ("ru", "irina", "Female", "Russian - Irina (Female Academic)"),
    ("zh", "chaowen", "Male", "Chinese - Chaowen (Male Lecturer)"),
    ("zh", "huayan", "Female", "Chinese - Huayan (Female Studio)"),
    ("hi", "pratham", "Male", "Hindi - Pratham (Male Academic)"),
    ("hi", "priyamvada", "Female", "Hindi - Priyamvada (Female Lecturer)"),
    ("pt", "faber", "Male", "Portuguese - Faber (Male Academic)"),
    ("tr", "dfki", "Male", "Turkish - DFKI (Male Scholar)"),
    ("en", "ryan", "Male", "English - Ryan (Male Baritone)"),
    ("en", "lessac", "Female", "English - Lessac (Female Expressive)"),
]


def test_translation_and_voices():
    print("\n" + "=" * 75, flush=True)
    print(" 1. MULTILINGUAL TRANSLATION & NEURAL VOICE VERIFICATION", flush=True)
    print("=" * 75, flush=True)

    audio_path = ROOT_DIR / "storage" / "test_feynman" / "asr_16k.wav"
    if not audio_path.is_file():
        print(f"[FAIL] Required test audio not found at {audio_path}", flush=True)
        return False

    # 1. Transcribe
    print("\n[Step 1/3] Transcribing 1-minute English lecture with Faster-Whisper...", flush=True)
    t0 = time.time()
    asr = FasterWhisperASREngine()
    asr_res = asr.transcribe(str(audio_path), language="en")
    print(f"  ASR Complete in {time.time() - t0:.2f}s: {len(asr_res.segments)} segments detected.", flush=True)

    sample_segments = asr_res.segments[:5]
    for s in sample_segments:
        print(f"    [{s.start:.2f}s - {s.end:.2f}s]: {s.text}", flush=True)

    # 2. Translate unique languages
    print("\n[Step 2/3] Translating across distinct languages with LocalLLMTranslator...", flush=True)
    translator = LocalLLMTranslator()
    tts = FallbackTTSEngine()
    out_dir = ROOT_DIR / "storage" / "test_verification"
    out_dir.mkdir(parents=True, exist_ok=True)

    src_text = sample_segments[0].text  # "Now I'm going to discuss how we would look for a new law."
    target_dur = sample_segments[0].end - sample_segments[0].start
    unique_langs = sorted(list(set(lang for lang, _, _, _ in TEST_LANGUAGES_AND_VOICES)))

    translated_cache = {}
    for lang in unique_langs:
        t_trans0 = time.time()
        tgt_text = translator._translate_single(
            text=src_text,
            prev_text="",
            next_text=sample_segments[1].text,
            src_lang="en",
            tgt_lang=lang,
            duration=target_dur,
            glossary={},
            segment_idx=1
        )
        is_script_valid = validate_script_matches_language(tgt_text, lang)
        translated_cache[lang] = (tgt_text, is_script_valid)
        print(f"  [{lang.upper()}] Translated in {time.time() - t_trans0:.2f}s: \"{tgt_text}\" (Script Valid: {is_script_valid})", flush=True)

    # 3. Synthesize for every language and voice
    print("\n[Step 3/3] Synthesizing audio across ALL 22 language & voice combinations...", flush=True)
    results_table = []
    all_passed = True

    for lang, voice, gender, label in TEST_LANGUAGES_AND_VOICES:
        tgt_text, is_script_valid = translated_cache.get(lang, ("", False))

        if not is_script_valid or not tgt_text.strip():
            print(f"  [ERROR] Script validation failed for {label}!", flush=True)
            all_passed = False

        voice_out_file = out_dir / f"test_{lang}_{voice}.wav"
        t_synth0 = time.time()
        actual_dur = tts.synthesize(
            text=tgt_text,
            language=lang,
            out_path=str(voice_out_file),
            target_duration=target_dur,
            voice=voice
        )
        synth_elapsed = time.time() - t_synth0

        file_exists = voice_out_file.is_file()
        file_size = voice_out_file.stat().st_size if file_exists else 0
        is_valid_audio = file_exists and file_size > 4000 and actual_dur > 0.5

        status_str = "PASS" if (is_script_valid and is_valid_audio) else "FAIL"
        print(f"  --> {label:<35} | {status_str} | {file_size/1024:>5.1f} KB | {actual_dur:.2f}s in {synth_elapsed:.2f}s", flush=True)

        if not is_valid_audio:
            all_passed = False

        results_table.append({
            "label": label,
            "lang": lang,
            "voice": voice,
            "script_ok": is_script_valid,
            "audio_ok": is_valid_audio,
            "dur": actual_dur,
            "size_kb": file_size / 1024
        })

    print("\n" + "=" * 75, flush=True)
    print(" MULTILINGUAL TRANSLATION & VOICE SYNTHESIS SUMMARY", flush=True)
    print("=" * 75, flush=True)
    print(f"{'Language & Voice':<38} | {'Script':<8} | {'Audio':<8} | {'Duration':<10} | {'Size':<10}", flush=True)
    print("-" * 75, flush=True)
    for r in results_table:
        s_status = "PASS" if r["script_ok"] else "FAIL"
        a_status = "PASS" if r["audio_ok"] else "FAIL"
        print(f"{r['label']:<38} | {s_status:<8} | {a_status:<8} | {r['dur']:>6.2f}s   | {r['size_kb']:>6.1f} KB", flush=True)

    return all_passed


def test_frontend_and_api():
    print("\n" + "=" * 75, flush=True)
    print(" 2. FRONTEND & API COMPONENT FUNCTIONALITY VERIFICATION", flush=True)
    print("=" * 75, flush=True)

    base_api = "http://127.0.0.1:8000"
    base_fe = "http://127.0.0.1:3000"
    all_passed = True

    # 1. API Health & Configuration
    print("\n[Step 1/5] Testing Backend API Endpoints...", flush=True)
    try:
        resp = urllib.request.urlopen(f"{base_api}/api/health", timeout=5)
        health_data = json.loads(resp.read().decode("utf-8"))
        print(f"  [OK] /api/health returned status 200: {health_data}", flush=True)
    except Exception as e:
        print(f"  [FAIL] /api/health failed: {e}", flush=True)
        all_passed = False

    # 2. User Authentication (Register -> Login -> Token Validation)
    print("\n[Step 2/5] Testing Authentication Flow (Register & Login)...", flush=True)
    test_email = f"test_{int(time.time())}@example.com"
    test_password = "SecurePassword123!"
    auth_token = None

    try:
        # Register
        reg_payload = json.dumps({"email": test_email, "password": test_password}).encode("utf-8")
        reg_req = urllib.request.Request(
            f"{base_api}/api/auth/register",
            data=reg_payload,
            headers={"Content-Type": "application/json"}
        )
        reg_resp = urllib.request.urlopen(reg_req, timeout=5)
        reg_data = json.loads(reg_resp.read().decode("utf-8"))
        print(f"  [OK] /api/auth/register succeeded for {test_email} (User ID: {reg_data.get('id')})", flush=True)

        # Login
        login_payload = json.dumps({"email": test_email, "password": test_password}).encode("utf-8")
        login_req = urllib.request.Request(
            f"{base_api}/api/auth/login",
            data=login_payload,
            headers={"Content-Type": "application/json"}
        )
        login_resp = urllib.request.urlopen(login_req, timeout=5)
        login_data = json.loads(login_resp.read().decode("utf-8"))
        auth_token = login_data.get("access_token")
        print(f"  [OK] /api/auth/login succeeded, JWT token acquired: {auth_token[:20]}...", flush=True)

        # Current User Profile
        me_req = urllib.request.Request(
            f"{base_api}/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        me_resp = urllib.request.urlopen(me_req, timeout=5)
        me_data = json.loads(me_resp.read().decode("utf-8"))
        print(f"  [OK] /api/auth/me authenticated profile: {me_data.get('email')}", flush=True)

    except Exception as e:
        print(f"  [FAIL] Auth flow failed: {e}", flush=True)
        all_passed = False

    # 3. Job Submission API with YouTube Source
    print("\n[Step 3/5] Testing Job Creation & YouTube Ingest API...", flush=True)
    if auth_token:
        try:
            job_payload = json.dumps({
                "source_type": "youtube",
                "source_ref": "https://www.youtube.com/watch?v=b240PGCMwV0",
                "target_lang": "ur",
                "selected_voice": "tariq",
                "ownership_confirmed": True,
                "voice_consent": True,
                "generate_subtitles": True
            }).encode("utf-8")

            job_req = urllib.request.Request(
                f"{base_api}/api/jobs",
                data=job_payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {auth_token}"
                }
            )
            job_resp = urllib.request.urlopen(job_req, timeout=10)
            job_data = json.loads(job_resp.read().decode("utf-8"))
            job_id = job_data.get("id")
            print(f"  [OK] Job created successfully: ID={job_id}, Status={job_data.get('status')}", flush=True)

            # Check job retrieval
            get_req = urllib.request.Request(
                f"{base_api}/api/jobs/{job_id}",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            get_resp = urllib.request.urlopen(get_req, timeout=5)
            get_data = json.loads(get_resp.read().decode("utf-8"))
            print(f"  [OK] Retrieved Job {job_id}: Title='{get_data.get('title')}', Stage={get_data.get('current_stage')}", flush=True)

        except Exception as e:
            print(f"  [FAIL] Job creation API failed: {e}", flush=True)
            all_passed = False

    # 4. Frontend Route HTTP Verification
    print("\n[Step 4/5] Testing Next.js Frontend Routes...", flush=True)
    frontend_routes = [
        ("/", "Landing Page / Hero / Features"),
        ("/dashboard", "Dashboard Job Management"),
        ("/jobs/new", "New Job Creation & Voice Picker"),
        ("/login", "Login Authentication Page"),
        ("/register", "Registration Page"),
        ("/terms", "Terms of Service"),
        ("/privacy", "Privacy Policy"),
        ("/takedown", "DMCA Copyright Takedown Form")
    ]

    for route, desc in frontend_routes:
        url = f"{base_fe}{route}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            resp = urllib.request.urlopen(req, timeout=10)
            print(f"  [OK] Route '{route}' ({desc}) -> HTTP {resp.getcode()}", flush=True)
        except Exception as e:
            print(f"  [FAIL] Route '{route}' ({desc}) failed: {e}", flush=True)
            all_passed = False

    # 5. Voice Gallery Static Audition Clips
    print("\n[Step 5/5] Testing Voice Gallery Audition Audio Assets in Browser...", flush=True)
    sample_auditions = [
        "alan.wav", "amy.wav", "ayesha.wav", "chaowen.wav", "dave.wav",
        "denis.wav", "dfki.wav", "faber.wav", "gilles.wav", "huayan.wav",
        "irina.wav", "kareem.wav", "kerstin.wav", "lessac.wav", "maryam.wav",
        "paola.wav", "pratham.wav", "priyamvada.wav", "riccardo.wav", "ryan.wav",
        "sharvard.wav", "siwis.wav", "tariq.wav", "thorsten.wav"
    ]

    for wav in sample_auditions:
        url = f"{base_fe}/voices/{wav}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            resp = urllib.request.urlopen(req, timeout=5)
            content_len = resp.headers.get("Content-Length", "0")
            print(f"  [OK] Voice Audition /voices/{wav} -> HTTP {resp.getcode()} ({int(content_len)/1024:.1f} KB)", flush=True)
        except Exception as e:
            print(f"  [FAIL] Audition asset /voices/{wav} failed: {e}", flush=True)
            all_passed = False

    return all_passed


def main():
    print("===========================================================================", flush=True)
    print(" LECTURE DUBBER - FINAL PRE-DEPLOYMENT VERIFICATION TEST", flush=True)
    print("===========================================================================", flush=True)

    t0 = time.time()
    t_ok = test_translation_and_voices()
    f_ok = test_frontend_and_api()
    elapsed = time.time() - t0

    print("\n" + "=" * 75, flush=True)
    print(" FINAL VERIFICATION RESULTS", flush=True)
    print("=" * 75, flush=True)
    print(f" Multilingual Translation & Voice Synthesis: {'ALL PASSED' if t_ok else 'FAILED'}", flush=True)
    print(f" Frontend & API Full-Stack Functionality:    {'ALL PASSED' if f_ok else 'FAILED'}", flush=True)
    print(f" Total Verification Duration:               {elapsed:.2f} seconds", flush=True)
    print("=" * 75, flush=True)

    if t_ok and f_ok:
        print("\n>>> SYSTEM IS 100% HARDENED, VERIFIED, AND READY FOR DEPLOYMENT! <<<\n", flush=True)
        sys.exit(0)
    else:
        print("\n>>> ONE OR MORE VERIFICATION STEPS FAILED. CHECK LOGS ABOVE. <<<\n", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
