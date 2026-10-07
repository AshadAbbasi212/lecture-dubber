# Third-Party Licenses & Compliance Audit

This document provides a comprehensive compliance and licensing inventory for all external models, frameworks, tools, and libraries utilized by **Lecture Dubber**.

**Commercial Policy:** Lecture Dubber is engineered for commercial educational deployment. All dependencies and model weights must permit unrestricted commercial use without royalty or non-commercial restrictions (e.g., CC-BY-NC and proprietary research-only licenses are strictly prohibited).

---

## 1. AI Models & Speech Processing Weights

| Component / Model | Provider / Author | Version | License | Commercial Permitted | Official License Link / Model Card | Verification & Usage Notes |
|---|---|---|---|---|---|---|
| **Faster-Whisper / CTranslate2** | SYSTRAN / OpenAI | 1.0.x / 4.x | MIT | Yes | [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper/blob/master/LICENSE) | Code and OpenAI Whisper model weights (`base`, `small`, `large-v3`) are MIT licensed. |
| **Demucs (`htdemucs`)** | Meta AI Research | 4.1.0 | MIT | Yes | [facebookresearch/demucs](https://github.com/facebookresearch/demucs/blob/main/LICENSE) | Code and default `htdemucs` v4 model checkpoints are MIT licensed. |
| **Qwen2.5-Instruct (7B / 1.5B)** | Alibaba Cloud Qwen Team | 2.5 | Apache-2.0 | Yes | [Qwen/Qwen2.5-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct) | `Qwen2.5-7B`, `1.5B`, `0.5B`, `14B`, and `32B` are Apache-2.0. (*Note: Qwen2.5-3B and 72B use proprietary non-commercial licenses and are excluded*). |
| **OpenVoice v2** | MyShell AI | 2.0 | MIT | Yes | [myshell-ai/OpenVoice](https://github.com/myshell-ai/OpenVoice/blob/main/LICENSE) | Both codebase and official tone color converter weights are MIT licensed since v2 release (April 2024). |
| **MeloTTS** | MyShell AI | 0.1.2 | MIT | Yes | [myshell-ai/MeloTTS](https://github.com/myshell-ai/MeloTTS/blob/main/LICENSE) | English neural TTS base synthesizer; fully MIT licensed for commercial applications. |
| **Piper TTS (Urdu Voices)** | Rhasspy / Piper Team | 1.2.0 | MIT | Yes | [rhasspy/piper](https://github.com/rhasspy/piper/blob/master/LICENSE) | Fast neural ONNX runtime. Urdu voices (`ur_PK-aegis_female`, `ur_PK-fasih`) are MIT/Open Data licensed for commercial speech generation. |
| **Silero VAD** | Silero Team | 5.1 | MIT | Yes | [snakers4/silero-vad](https://github.com/snakers4/silero-vad/blob/master/LICENSE) | Integrated inside faster-whisper for speech activity segmentation. |

### Disqualified Models (Audit Blacklist)
- **Coqui XTTS-v2:** Governed by *Coqui Public Model License (CPML)*, prohibiting commercial exploitation without enterprise licensing. **Disqualified.**
- **Meta NLLB-200:** Model weights are licensed under *Creative Commons Attribution-NonCommercial 4.0 (CC-BY-NC 4.0)*. **Disqualified.**
- **F5-TTS:** Released under *CC-BY-NC 4.0* for pretrained checkpoints. **Disqualified.**
- **Qwen2.5-3B / 72B:** Governed by proprietary *Qwen Research License* with non-commercial restrictions. **Disqualified.**

---

## 2. Media Engines & CLI Binaries

| Tool | Upstream Project | Minimum Version | License | Commercial Permitted | Official Reference | Integration Isolation |
|---|---|---|---|---|---|---|
| **FFmpeg & ffprobe** | FFmpeg Developers | 6.0+ (Tested 9.0.1) | LGPL v2.1+ / GPL v2+ | Yes | [ffmpeg.org/legal.html](https://www.ffmpeg.org/legal.html) | Invoked strictly via external subprocess CLI (`settings.get_ffmpeg_cmd()`). No dynamic or static linking into proprietary binaries. |
| **yt-dlp** | yt-dlp Team | 2024.08+ | The Unlicense | Yes | [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp/blob/master/LICENSE) | Public Domain dedication. Used for safe URL audio extraction with worker-isolated rate limits. |

---

## 3. Backend Python Libraries (`backend/requirements.txt`)

| Package | Version Pin / Minimum | License | Link | Permitted Use |
|---|---|---|---|---|
| **FastAPI** | `>=0.110.0` | MIT | [tiangolo/fastapi](https://github.com/tiangolo/fastapi/blob/master/LICENSE) | Commercial API framework |
| **Uvicorn** | `>=0.29.0` | BSD-3-Clause | [encode/uvicorn](https://github.com/encode/uvicorn/blob/master/LICENSE.md) | ASGI HTTP production server |
| **SQLAlchemy** | `>=2.0.0` | MIT | [sqlalchemy/sqlalchemy](https://github.com/sqlalchemy/sqlalchemy/blob/main/LICENSE) | ORM and database engine |
| **Alembic** | `>=1.13.0` | MIT | [sqlalchemy/alembic](https://github.com/sqlalchemy/alembic/blob/main/LICENSE) | Database migration tool |
| **Pydantic** | `>=2.6.0` | MIT | [pydantic/pydantic](https://github.com/pydantic/pydantic/blob/main/LICENSE) | Data validation & schemas |
| **pydantic-settings** | `>=2.2.0` | MIT | [pydantic/pydantic-settings](https://github.com/pydantic/pydantic-settings/blob/main/LICENSE) | Environment configuration |
| **argon2-cffi** | `>=23.1.0` | MIT | [hynek/argon2-cffi](https://github.com/hynek/argon2-cffi/blob/main/LICENSE) | Password hashing (PHC winner) |
| **PyJWT** | `>=2.8.0` | MIT | [jpadilla/pyjwt](https://github.com/jpadilla/pyjwt/blob/master/LICENSE) | Cryptographic token handling |
| **SoundFile** | `>=0.12.1` | BSD-3-Clause | [bastibe/python-soundfile](https://github.com/bastibe/python-soundfile/blob/master/LICENSE) | Audio file read/write (libsndfile wrapper) |
| **NumPy** | `>=1.24.0` | BSD-3-Clause | [numpy/numpy](https://github.com/numpy/numpy/blob/main/LICENSE.txt) | Timeline buffering & sample manipulation |
| **SciPy** | `>=1.11.0` | BSD-3-Clause | [scipy/scipy](https://github.com/scipy/scipy/blob/main/LICENSE.txt) | Audio envelope and ducking filter |
| **requests** | `>=2.31.0` | Apache-2.0 | [psf/requests](https://github.com/psf/requests/blob/main/LICENSE) | HTTP networking & SSRF safe downloader |
| **python-dotenv** | `>=1.0.0` | BSD-3-Clause | [theskumar/python-dotenv](https://github.com/theskumar/python-dotenv/blob/master/LICENSE) | Configuration loading |
| **pytest** | `>=8.0.0` | MIT | [pytest-dev/pytest](https://github.com/pytest-dev/pytest/blob/main/LICENSE) | Automated test harness (dev/test) |
| **httpx** | `>=0.27.0` | BSD-3-Clause | [encode/httpx](https://github.com/encode/httpx/blob/master/LICENSE.md) | TestClient integration |

---

## 4. Frontend Dependencies (`frontend/package.json`)

| Package | Version | License | Link | Purpose |
|---|---|---|---|---|
| **Next.js** | `16.4.0` | MIT | [vercel/next.js](https://github.com/vercel/next.js/blob/canary/LICENSE) | Full-stack React 19 web application framework |
| **React & React DOM** | `19.3.0` | MIT | [facebook/react](https://github.com/facebook/react/blob/main/LICENSE) | UI component runtime |
| **Tailwind CSS** | `4.x` | MIT | [tailwindlabs/tailwindcss](https://github.com/tailwindlabs/tailwindcss/blob/main/LICENSE) | Modern utility CSS design system |
| **Lucide React** | `^1.52.0` | ISC | [lucide-icons/lucide](https://github.com/lucide-icons/lucide/blob/main/LICENSE) | High quality vector icon library |
| **TypeScript** | `5.x` | Apache-2.0 | [microsoft/TypeScript](https://github.com/microsoft/TypeScript/blob/main/LICENSE.txt) | Type-safe static analysis |

---

## 5. Summary of Compliance Status
- **Commercial Freedom:** 100% of runtime components, models, and dependencies carry permissive licenses (MIT, Apache 2.0, BSD-2/3, ISC, The Unlicense, or LGPL via CLI).
- **Zero Proprietary/Cloud APIs:** All operations run locally; no dependencies on external billing or cloud API telemetry.
- **Copyleft Boundary:** FFmpeg is invoked exclusively as a stand-alone subprocess CLI binary over standard OS process execution primitives (`subprocess.Popen`), satisfying LGPL and GPL boundary separation requirements.
