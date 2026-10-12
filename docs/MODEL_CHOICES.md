# Model choices (candidates, NOT decisions)

> Everything below was written from memory by the assistant that generated this kit.
> **Licenses, language support and VRAM figures must be verified online in Phase 0**
> by reading each official repo, model card and LICENSE file. This is a commercial
> product: a non-commercial or research-only license disqualifies a model.
> Record results in `docs/DECISIONS.md`.

Confidence key: H = fairly sure, M = unsure, L = guess.

> **v1 scope:** the lip-sync, face detection / tracking, shot detection and face restoration rows
> are **deferred** to the later lip-sync milestone. Do not research or install them now.

| Stage | Candidates | License / language notes (to verify) | 8 GB notes |
|---|---|---|---|
| ASR + language ID | faster-whisper (CTranslate2) with Whisper large-v3 or medium; WhisperX for alignment | Whisper code and weights are MIT (H). Urdu accuracy is weaker than English (M): measure | large-v3 with int8 or int8_float16 should fit (M) |
| Voice / background separation | Demucs (htdemucs) | MIT (H); upstream repo may be archived (M): check forks | fits; run chunked |
| Translation (local) | Qwen2.5 7B Instruct (quantized, via llama.cpp or Ollama); MADLAD-400 (3B or 7B); Gemma family | Qwen2.5 7B Apache-2.0 (M, smaller sizes differ); MADLAD-400 Apache-2.0 (M); Gemma has its own terms (M). **NLLB-200 weights are CC-BY-NC (H): avoid** | 7B at 4-bit about 5 GB (M). Evaluate Urdu quality on real lecture text |
| TTS English with cloning | Chatterbox (Resemble AI); OpenVoice v2 + a base TTS; others found in research | Chatterbox MIT (M). **F5-TTS code is MIT but its pretrained weights are, as far as I know, CC-BY-NC (M): treat as research-only until verified.** XTTS-v2 is non-commercial (H): avoid. Fish-Speech weights non-commercial (M) | most fit in 8 GB (M) |
| TTS Urdu | Unknown. Needs a real research spike | Meta MMS-TTS has Urdu but is CC-BY-NC (M): avoid. Many cloning models do not list Urdu (M). Check: Piper voices, Coqui community models, Hugging Face "ur" TTS models, any Apache/MIT multilingual TTS added recently | unknown |
| Voice conversion (timbre transfer) | OpenVoice v2 tone-colour converter; Seed-VC; RVC-style models | OpenVoice v2 MIT (M); others vary (L) | light |
| Face detection / tracking | InsightFace / RetinaFace, MediaPipe | InsightFace model weights are non-commercial for some packs (M): verify. MediaPipe is Apache-2.0 (H) | light |
| Shot detection | PySceneDetect | BSD-3 (H) | CPU |
| Lip-sync | MuseTalk; LatentSync; (Wav2Lip is non-commercial (H): reference only) | MuseTalk code MIT but check dependent weights (M); LatentSync Apache-2.0 code, check weights and version VRAM needs (M) | LatentSync newer versions may need much more than 8 GB (M): benchmark. MuseTalk lighter (M) |
| Face restoration (optional) | GFPGAN, CodeFormer | CodeFormer is non-commercial (M); GFPGAN Apache-2.0 (M) | light |
| Link import | yt-dlp | Unlicense (H) | CPU |
| Media | FFmpeg, ffprobe, rubberband | LGPL/GPL depending on build (H): do not statically bundle a GPL build into a distributed product without legal review | CPU |

## Design implications

1. **Urdu voice is the project's biggest technical risk.** Expect to combine a
   plain Urdu TTS voice with voice conversion, or to ship Urdu output with a
   standard voice (no cloning) and say so clearly in the UI. Phase 0 decides.
2. **Lip-sync must be benchmarked on the real 8 GB card** with a real lecture clip
   before anything is built around it.
3. Keep every model behind an interface and record chosen model + version +
   license link per stage in `DECISIONS.md`.

## Reference repos (clone only what Phase 0 shows is needed)

See `scripts/fetch_repos.ps1`. Many of these should be installed with `pip`
instead of cloned. Reference-only (not for shipping): Wav2Lip.
