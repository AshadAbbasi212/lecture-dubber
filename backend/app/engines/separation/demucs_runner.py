import argparse
import json
import sys
import time
from pathlib import Path
import numpy as np
import soundfile as sf
import torch

try:
    from demucs.apply import apply_model
    from demucs.pretrained import get_model
except ImportError:
    print(json.dumps({"status": "error", "message": "demucs package is not installed in this Python environment."}))
    sys.exit(1)


def run_separation(input_path: Path, out_dir: Path, device: str = "auto"):
    out_dir.mkdir(parents=True, exist_ok=True)
    vocals_out = out_dir / "vocals.wav"
    bg_out = out_dir / "background.wav"

    if device == "auto":
        target_device = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        target_device = device

    # Read audio with soundfile
    data, sr = sf.read(str(input_path), dtype="float32")
    # Ensure stereo (channels, time)
    if data.ndim == 1:
        data = np.column_stack([data, data])
    elif data.shape[1] > 2:
        data = data[:, :2]

    duration = len(data) / sr

    # Model input format: (batch, channels, time)
    audio_tensor = torch.tensor(data.T, dtype=torch.float32).unsqueeze(0)

    # Load Demucs htdemucs
    model = get_model("htdemucs")
    model.to(target_device)
    model.eval()

    with torch.no_grad():
        # split=True chunks long files (30-60m) to preserve VRAM
        sources = apply_model(model, audio_tensor.to(target_device), device=target_device, split=True, overlap=0.25)

    # sources shape: (batch, num_sources, channels, time)
    # Stems: 0=drums, 1=bass, 2=other, 3=vocals
    vocals_tensor = sources[0, 3].cpu().numpy().T
    bg_tensor = (sources[0, 0] + sources[0, 1] + sources[0, 2]).cpu().numpy().T

    sf.write(str(vocals_out), vocals_tensor, sr)
    sf.write(str(bg_out), bg_tensor, sr)

    return {
        "status": "ok",
        "vocals": str(vocals_out),
        "background": str(bg_out),
        "duration": duration,
        "sample_rate": sr,
        "device_used": target_device
    }


def main():
    parser = argparse.ArgumentParser(description="Standalone Demucs stem separator")
    parser.add_argument("--input", required=True, help="Input WAV file")
    parser.add_argument("--out-dir", required=True, help="Output directory")
    parser.add_argument("--device", default="auto", choices=["auto", "cuda", "cpu"])
    args = parser.parse_args()

    try:
        res = run_separation(Path(args.input), Path(args.out_dir), args.device)
        print(json.dumps(res))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
