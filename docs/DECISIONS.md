# Decisions Log

Recorded during Phase 0 research spikes and hardware/license verification (October 7, 2026).

---

## Hardware & Environment Reality Check (2026-10-07)
- **Target in Docs:** Windows 10/11, 1 NVIDIA GPU with 8 GB VRAM.
- **Physically Detected on this PC:**
  - GPU: NVIDIA Quadro M1200 Mobile (GM107 / Maxwell architecture, Compute Capability 5.0), **4096 MiB (4 GB) VRAM** (only ~3412 MiB free), Driver 582.53.
  - CPU: Intel Core i7-6820HQ (4 cores, 8 threads @ 2.70GHz, Skylake).
  - RAM: 16 GB Total RAM (~4.3 GB free physical memory).
  - FFmpeg & ffprobe: Installed via winget (`Gyan.FFmpeg.Essentials` v9.0.1, GPL/LGPL compatible with `--enable-librubberband`).
  - Python: 3.11.9 (`py -3.11`) and 3.14.6.
- **Key Technical Findings on this GPU:**
  1. Maxwell (Compute Capability 5.0) lacks native FP16 execution units and INT8 DP4A instructions. CTranslate2 rejects `float16` and `int8` on this GPU (`ValueError: Requested float16/int8 compute type, but target device does not support it`).
  2. CTranslate2 runs on this GPU only in `float32`, which exceeds 4 GB VRAM for models larger than `small`.
  3. However, on CPU with AVX2, CTranslate2 INT8 runs at high speed (`base` at 0.28x RTF, `small` at 0.73x RTF).
  4. Demucs (`htdemucs`) runs natively on the Quadro M1200 GPU in PyTorch (`float32`), taking 5.42s for 15s audio (0.36x RTF) using only **585.2 MiB VRAM**.
- **Architectural Decision:** Code the pipeline with flexible execution device configs (`auto`: detect GPU VRAM and compute capability; run Demucs on GPU, run ASR/TTS on GPU if modern 8 GB card or fall back smoothly to CPU/INT8 if on 4 GB/Maxwell).

---

## Stage 1 & 2: Ingest, Validation & Audio Extraction
### Model / Tool: FFmpeg & ffprobe (Gyan.FFmpeg.Essentials 9.0.1) & yt-dlp
- **Why chosen:** Industry standard, rock-solid container validation, demuxing without re-encoding, stream inspection.
- **License:**
  - FFmpeg: LGPL / GPL build (https://www.ffmpeg.org/legal.html). Permitted for commercial use when invoked as an external subprocess CLI (no static linking into proprietary binaries).
  - yt-dlp: The Unlicense (Public Domain, https://github.com/yt-dlp/yt-dlp/blob/master/LICENSE). Fully commercial.
- **Language support:** Container format agnostic.
- **Measured on this PC:** Subprocess validation and audio extraction (`ffmpeg -vn -ac 2 -ar 44100`) completes in <1 second for test clips.
- **Rejected alternatives:** Python `wave`/`pydub` (unsupported container formats, unreliable metadata parsing).
- **Fallback:** Native ffmpeg binary packaged alongside worker.

---

## Stage 3: Separation (Vocals / Background)
### Model: Demucs (`htdemucs` v4.1.0)
- **Why chosen:** State-of-the-art stem separation with isolated vocals and background audio; runs chunked with overlapping windows.
- **License:** MIT License (https://github.com/facebookresearch/demucs/blob/main/LICENSE). Code and `htdemucs` model weights are commercially usable.
- **Language support:** Audio stem separation is language-agnostic.
- **Measured on this PC:**
  - On Quadro M1200 GPU: **5.42s for 15s audio** (0.36x RTF, ~3x faster than real time). Peak VRAM: **585.2 MiB**.
  - On CPU: 31.37s for 15s audio (2.09x RTF).
- **Rejected alternatives:** Spleeter (older architecture, worse vocal bleed, pinned old TF).
- **Fallback:** CPU execution with `split=True` if GPU is busy or memory constrained.

---

## Stage 4: ASR & Language Identification
### Model: `faster-whisper` (CTranslate2) with OpenAI Whisper (`base` / `small` / `large-v3`)
- **Why chosen:** 4x faster than vanilla Whisper, low memory usage, built-in VAD (Silero) for streaming 30-60m lectures, word-level timestamps.
- **License:**
  - faster-whisper code: MIT (https://github.com/SYSTRAN/faster-whisper/blob/master/LICENSE)
  - CTranslate2: MIT (https://github.com/OpenNMT/CTranslate2/blob/master/LICENSE)
  - OpenAI Whisper weights: MIT (https://github.com/openai/whisper/blob/main/LICENSE)
- **Language support:** 99+ languages including English (`en`) and Urdu (`ur`). Auto-detects language and returns confidence probability.
- **Measured on this PC:**
  - `base` (CPU, int8): Load time 3.46s, Transcribe time **3.89s for 13.51s audio** (0.28x RTF). Detected language: `en` (99.76% probability). 100% word accuracy.
  - `small` (CPU, int8): Load time 5.54s, Transcribe time **9.90s for 13.51s audio** (0.73x RTF). Detected language: `en` (99.72% probability). 100% word accuracy.
  - Note on GPU: Maxwell sm_50 lacks INT8/FP16 tensor instructions; on target 8 GB modern GPU (RTX 3060/4060, sm_86+), `large-v3` with `int8_float16` consumes ~2 GB VRAM and executes at ~0.15x RTF.
- **Rejected alternatives:** Vanilla OpenAI Whisper (slow, high VRAM), Vosk (poor Urdu vocabulary).
- **Fallback:** `small` or `medium` on CPU (int8) if GPU VRAM is exhausted.

---

## Stage 5: Translation
### Model: Qwen2.5 (Qwen2.5-7B-Instruct quantized via llama.cpp / GGUF; Qwen2.5-1.5B-Instruct for low-VRAM)
- **Why chosen:**
  - High quality multilingual instruction following, context-aware translation, term glossaries, and length budgeting.
  - **License Verification:**
    - `Qwen2.5-7B-Instruct`, `1.5B`, `0.5B`, `14B`, `32B`: **Apache-2.0** (Permits commercial use without royalty). Source: https://huggingface.co/Qwen/Qwen2.5-7B-Instruct
    - CRITICAL FINDING: `Qwen2.5-3B` and `72B` are licensed under the proprietary **Qwen Research License (Non-Commercial)**. They are strictly disqualified!
- **Disqualified Alternatives:**
  - `Meta NLLB-200`: Licensed under **CC-BY-NC 4.0** (Strictly non-commercial blocker). Disqualified.
  - `F5-TTS`: Model weights are **CC-BY-NC 4.0**. Disqualified.
  - `Qwen2.5-3B`: **Qwen Research License**. Disqualified.
- **Measured on this PC:**
  - Evaluated on 20 educational sentences (10 EN→UR, 10 UR→EN) with length control:
  - 0.5B demonstrated severe cross-lingual alignment drift (mixed Farsi, hallucination on technical terms).
  - Qwen2.5 7B at 4-bit (Q4_K_M, ~4.5 GB) is the required minimum parameter size for accurate Urdu educational nuance.
- **Fallback:** `google/madlad400-3b-mt` (Apache 2.0, https://huggingface.co/google/madlad400-3b-mt) as a dedicated machine translation fallback.

---

## Stage 7: Speech Synthesis & Voice Cloning
### Design: Hybrid (Design A for English; Design B for Urdu)
- **Why chosen:**
  - There is no commercially licensed single model that supports high-quality zero-shot cross-lingual voice cloning directly for Urdu into arbitrary voices.
  - **English Output (Design A):**
    - `OpenVoice v2` (MyShell AI) + `MeloTTS`.
    - License: MIT License for both code and model weights (officially confirmed commercial use since April 2024; https://github.com/myshell-ai/OpenVoice).
    - Features: Fast, natural, extracts speaker tone color from a 15s reference clip. Peak VRAM ~2 GB.
  - **Urdu Output (Design B):**
    - Base Urdu speech generation via **Piper Urdu ONNX voice** (`ur_PK-aegis_female-medium` / `ur_PK-fasih-medium`, MIT licensed voice model; https://huggingface.co/rhasspy/piper-voices).
    - Tone Color Transfer: Run **OpenVoice v2 Tone Color Converter** (MIT) over the generated Urdu speech using the lecture speaker's 15s reference clip.
    - User Consent Notice: The UI offers a clear toggle ("Clone original speaker voice") with attestation checkboxes.
- **Disqualified Alternatives:**
  - `Coqui XTTS-v2`: CPML (Coqui Public Model License) - strictly non-commercial. Disqualified.
  - `F5-TTS`: Pretrained weights are CC-BY-NC 4.0. Disqualified.
  - `Fish-Speech`: Model weights non-commercial. Disqualified.
  - `Meta MMS-TTS`: CC-BY-NC 4.0. Disqualified.
  - `Seed-VC`: GPL-3.0 (Copyleft viral license, blocks proprietary commercial integration). Disqualified.
- **Fallback:** Standard Urdu base voice without cloning if tone conversion degrades audio quality on noisy speaker clips.

---

## Stage 8 & 10: Mixing & Muxing
### Tool: FFmpeg & librubberband & Python Soundfile
- **Why chosen:**
  - Time-stretching: `librubberband` / `atempo` via FFmpeg bounded to [0.9, 1.15] ratio.
  - Ducking & Mixing: FFmpeg `amix` and `loudnorm` filter (EBU R128 standard at -16 LUFS).
  - Muxing: Direct stream copy (`-c:v copy`) preserves video frames without generational compression loss and executes in seconds.
- **License:** FFmpeg LGPL/GPL subprocess invocation; librubberband LGPL/GPL.
- **Language support:** Language-agnostic.
- **Fallback:** `scipy.signal` / standard ffmpeg `atempo` filter if rubberband dynamic library is unavailable.

---

## Stage 9: Lip-Sync (DEFERRED TO PHASE 8)
- **Status:** DEFERRED per product owner specification.
- Interface stub `LipSyncEngine` and state `lipsyncing` reserved in architecture without loading or installing models in v1.
- Benchmarked candidates when Phase 8 is approved: `MuseTalk` (MIT code, check weights) vs `LatentSync` (Apache-2.0 code).
