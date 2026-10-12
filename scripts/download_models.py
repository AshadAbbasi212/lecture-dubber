"""
Lecture Dubber - Automated Voice Model Downloader
Downloads Piper neural text-to-speech models and configuration files.
"""

import os
import sys
import urllib.request
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

MODELS_DIR = Path(__file__).resolve().parent.parent / "models" / "tts" / "piper"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

HF_PIPER = "https://huggingface.co/rhasspy/piper-voices/resolve/main"

VOICE_MODELS = {
    # English
    "en_US-ryan-medium": {
        "onnx": f"{HF_PIPER}/en/en_US/ryan/medium/en_US-ryan-medium.onnx",
        "json": f"{HF_PIPER}/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json",
    },
    "en_US-lessac-medium": {
        "onnx": f"{HF_PIPER}/en/en_US/lessac/medium/en_US-lessac-medium.onnx",
        "json": f"{HF_PIPER}/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json",
    },
    "en_US-amy-medium": {
        "onnx": f"{HF_PIPER}/en/en_US/amy/medium/en_US-amy-medium.onnx",
        "json": f"{HF_PIPER}/en/en_US/amy/medium/en_US-amy-medium.onnx.json",
    },
    "en_GB-alan-medium": {
        "onnx": f"{HF_PIPER}/en/en_GB/alan/medium/en_GB-alan-medium.onnx",
        "json": f"{HF_PIPER}/en/en_GB/alan/medium/en_GB-alan-medium.onnx.json",
    },
    # Arabic
    "ar_JO-kareem-medium": {
        "onnx": f"{HF_PIPER}/ar/ar_JO/kareem/medium/ar_JO-kareem-medium.onnx",
        "json": f"{HF_PIPER}/ar/ar_JO/kareem/medium/ar_JO-kareem-medium.onnx.json",
    },
    "arabic-emirati-female-model": {
        "onnx": "https://huggingface.co/vadimbelsky/arabic-emirati-female-piper/resolve/main/arabic-emirati-female-model.onnx",
        "json": "https://huggingface.co/vadimbelsky/arabic-emirati-female-piper/resolve/main/arabic-emirati-female-model.onnx.json",
    },
    # Urdu
    "ur_PK-fasih-medium": {
        "onnx": f"{HF_PIPER}/ur/ur_PK/fasih/medium/ur_PK-fasih-medium.onnx",
        "json": f"{HF_PIPER}/ur/ur_PK/fasih/medium/ur_PK-fasih-medium.onnx.json",
    },
    "ur_PK-aegis_female-medium": {
        "onnx": f"{HF_PIPER}/ur/ur_PK/aegis_female/medium/ur_PK-aegis_female-medium.onnx",
        "json": f"{HF_PIPER}/ur/ur_PK/aegis_female/medium/ur_PK-aegis_female-medium.onnx.json",
    },
    # Spanish
    "es_ES-davefx-medium": {
        "onnx": f"{HF_PIPER}/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx",
        "json": f"{HF_PIPER}/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx.json",
    },
    "es_ES-sharvard-medium": {
        "onnx": f"{HF_PIPER}/es/es_ES/sharvard/medium/es_ES-sharvard-medium.onnx",
        "json": f"{HF_PIPER}/es/es_ES/sharvard/medium/es_ES-sharvard-medium.onnx.json",
    },
    # German
    "de_DE-thorsten-medium": {
        "onnx": f"{HF_PIPER}/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx",
        "json": f"{HF_PIPER}/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx.json",
    },
    "de_DE-kerstin-low": {
        "onnx": f"{HF_PIPER}/de/de_DE/kerstin/low/de_DE-kerstin-low.onnx",
        "json": f"{HF_PIPER}/de/de_DE/kerstin/low/de_DE-kerstin-low.onnx.json",
    },
    # French
    "fr_FR-siwis-medium": {
        "onnx": f"{HF_PIPER}/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx",
        "json": f"{HF_PIPER}/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx.json",
    },
    "fr_FR-gilles-low": {
        "onnx": f"{HF_PIPER}/fr/fr_FR/gilles/low/fr_FR-gilles-low.onnx",
        "json": f"{HF_PIPER}/fr/fr_FR/gilles/low/fr_FR-gilles-low.onnx.json",
    },
    # Italian
    "it_IT-paola-medium": {
        "onnx": f"{HF_PIPER}/it/it_IT/paola/medium/it_IT-paola-medium.onnx",
        "json": f"{HF_PIPER}/it/it_IT/paola/medium/it_IT-paola-medium.onnx.json",
    },
    "it_IT-riccardo-x_low": {
        "onnx": f"{HF_PIPER}/it/it_IT/riccardo/x_low/it_IT-riccardo-x_low.onnx",
        "json": f"{HF_PIPER}/it/it_IT/riccardo/x_low/it_IT-riccardo-x_low.onnx.json",
    },
    # Russian
    "ru_RU-denis-medium": {
        "onnx": f"{HF_PIPER}/ru/ru_RU/denis/medium/ru_RU-denis-medium.onnx",
        "json": f"{HF_PIPER}/ru/ru_RU/denis/medium/ru_RU-denis-medium.onnx.json",
    },
    "ru_RU-irina-medium": {
        "onnx": f"{HF_PIPER}/ru/ru_RU/irina/medium/ru_RU-irina-medium.onnx",
        "json": f"{HF_PIPER}/ru/ru_RU/irina/medium/ru_RU-irina-medium.onnx.json",
    },
    # Chinese
    "zh_CN-huayan-medium": {
        "onnx": f"{HF_PIPER}/zh/zh_CN/huayan/medium/zh_CN-huayan-medium.onnx",
        "json": f"{HF_PIPER}/zh/zh_CN/huayan/medium/zh_CN-huayan-medium.onnx.json",
    },
    "zh_CN-chaowen-medium": {
        "onnx": f"{HF_PIPER}/zh/zh_CN/chaowen/medium/zh_CN-chaowen-medium.onnx",
        "json": f"{HF_PIPER}/zh/zh_CN/chaowen/medium/zh_CN-chaowen-medium.onnx.json",
    },
    # Hindi
    "hi_IN-pratham-medium": {
        "onnx": f"{HF_PIPER}/hi/hi_IN/pratham/medium/hi_IN-pratham-medium.onnx",
        "json": f"{HF_PIPER}/hi/hi_IN/pratham/medium/hi_IN-pratham-medium.onnx.json",
    },
    "hi_IN-priyamvada-medium": {
        "onnx": f"{HF_PIPER}/hi/hi_IN/priyamvada/medium/hi_IN-priyamvada-medium.onnx",
        "json": f"{HF_PIPER}/hi/hi_IN/priyamvada/medium/hi_IN-priyamvada-medium.onnx.json",
    },
    # Portuguese
    "pt_BR-faber-medium": {
        "onnx": f"{HF_PIPER}/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx",
        "json": f"{HF_PIPER}/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx.json",
    },
    # Turkish
    "tr_TR-dfki-medium": {
        "onnx": f"{HF_PIPER}/tr/tr_TR/dfki/medium/tr_TR-dfki-medium.onnx",
        "json": f"{HF_PIPER}/tr/tr_TR/dfki/medium/tr_TR-dfki-medium.onnx.json",
    },
}


def download_file(url: str, dest_path: Path):
    if dest_path.is_file() and dest_path.stat().st_size > 1000:
        print(f"  [EXISTS] {dest_path.name} ({dest_path.stat().st_size / 1024 / 1024:.2f} MB)")
        return
    print(f"  [DOWNLOADING] {dest_path.name} from {url}...")
    headers = {"User-Agent": "Mozilla/5.0"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=180) as resp, open(dest_path, "wb") as f:
        total = int(resp.headers.get("content-length", 0))
        downloaded = 0
        chunk_size = 512 * 1024
        while True:
            chunk = resp.read(chunk_size)
            if not chunk:
                break
            f.write(chunk)
            downloaded += len(chunk)
            if total > 0:
                percent = (downloaded / total) * 100
                print(f"\r    Progress: {percent:.1f}% ({downloaded / 1024 / 1024:.1f}/{total / 1024 / 1024:.1f} MB)", end="", flush=True)
        print()
    print(f"  [DONE] {dest_path.name} ({dest_path.stat().st_size / 1024 / 1024:.2f} MB)")


def main():
    print("==================================================================")
    print(" Lecture Dubber - Neural Voice Models Downloader")
    print(f" Target Directory: {MODELS_DIR}")
    print("==================================================================")

    for model_name, files in VOICE_MODELS.items():
        print(f"\nProcessing voice: {model_name}")
        onnx_file = MODELS_DIR / f"{model_name}.onnx"
        json_file = MODELS_DIR / f"{model_name}.onnx.json"

        download_file(files["onnx"], onnx_file)
        download_file(files["json"], json_file)

    print("\n==================================================================")
    print(" All voice models downloaded and verified.")
    print("==================================================================")


if __name__ == "__main__":
    main()
