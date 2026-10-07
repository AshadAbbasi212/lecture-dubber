import time
import torch
from faster_whisper import WhisperModel

audio_file = "spikes/test_data/speech_sample.wav"

configs = [
    ("base", "cpu", "int8"),
    ("base", "cuda", "float32"),
    ("small", "cpu", "int8"),
    ("small", "cuda", "float32"),
]

for model_size, device, compute_type in configs:
    print(f"\n--- Testing {model_size} on {device} ({compute_type}) ---")
    try:
        t0 = time.time()
        model = WhisperModel(model_size, device=device, compute_type=compute_type)
        load_time = time.time() - t0
        
        t0 = time.time()
        segments, info = model.transcribe(audio_file, beam_size=5, word_timestamps=True)
        text = " ".join([seg.text for seg in segments])
        transcribe_time = time.time() - t0
        
        print(f"Load time: {load_time:.2f}s | Transcribe time: {transcribe_time:.2f}s (Audio duration: {info.duration:.2f}s)")
        print(f"Detected language: {info.language} (probability: {info.language_probability:.2%})")
        print(f"Recognized text: {text.strip()}")
        if device == "cuda":
            print(f"Peak VRAM: {torch.cuda.max_memory_allocated()/(1024**2):.1f} MiB")
            torch.cuda.reset_peak_memory_stats()
    except Exception as e:
        print(f"Failed: {e}")
