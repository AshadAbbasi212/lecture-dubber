import time
import torch
import numpy as np
import soundfile as sf
import os
from pathlib import Path

# Create a synthetic 15-second multi-tone test audio with "voice" (harmonics) and "background" (sine rumble)
sr = 44100
duration = 15.0 # seconds
t = np.linspace(0, duration, int(sr * duration), endpoint=False)

# Simulated vocals: speech-frequency formants (200Hz, 800Hz, 2500Hz) modulated
vocals = 0.5 * np.sin(2 * np.pi * 220 * t) * (np.sin(2 * np.pi * 2 * t) > 0)
vocals += 0.3 * np.sin(2 * np.pi * 880 * t) * (np.sin(2 * np.pi * 2 * t) > 0)

# Simulated background: 60Hz hum + 440Hz background music pad
bg = 0.2 * np.sin(2 * np.pi * 60 * t) + 0.15 * np.sin(2 * np.pi * 440 * t)

mix = vocals + bg
# Stereo
mix_stereo = np.column_stack([mix, mix])

test_dir = Path("spikes/test_data")
test_dir.mkdir(parents=True, exist_ok=True)
mix_path = test_dir / "sample_mix.wav"
sf.write(str(mix_path), mix_stereo, sr)
print(f"Generated test audio at {mix_path}")

# Run Demucs separation
from demucs.apply import apply_model
from demucs.pretrained import get_model

print("Loading Demucs model...")
t0 = time.time()
model = get_model('htdemucs')
model.cpu()
load_time = time.time() - t0
print(f"Demucs loaded in {load_time:.2f}s")

# Prepare tensor (batch, channels, time)
audio_tensor = torch.tensor(mix_stereo.T, dtype=torch.float32).unsqueeze(0)
print("Applying Demucs separation...")
t0 = time.time()
with torch.no_grad():
    sources = apply_model(model, audio_tensor, device='cpu', split=True, overlap=0.25)
sep_time = time.time() - t0
print(f"Separation finished in {sep_time:.2f}s for {duration}s audio (RTF: {sep_time/duration:.2f}x)")

# sources shape: (batch, num_sources, channels, time)
# Demucs sources order: drums, bass, other, vocals
vocals_tensor = sources[0, 3].cpu().numpy().T
bg_tensor = (sources[0, 0] + sources[0, 1] + sources[0, 2]).cpu().numpy().T

sf.write(str(test_dir / "separated_vocals.wav"), vocals_tensor, sr)
sf.write(str(test_dir / "separated_bg.wav"), bg_tensor, sr)
print("Separated files written successfully.")
