import argparse
import json
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from faster_whisper import WhisperModel
except ImportError:
    print(json.dumps({"status": "error", "message": "faster-whisper package not installed in environment."}))
    sys.exit(1)


def run_transcription(audio_path: Path, model_size: str = "base", language: str = None, device: str = "auto", compute_type: str = "auto", task: str = "transcribe"):
    import torch

    # Automatic device & compute type determination based on hardware capabilities
    if device == "auto":
        if torch.cuda.is_available():
            cap = torch.cuda.get_device_capability()
            # Maxwell (compute capability 5.0) lacks INT8/FP16 tensor cores. CPU int8 is 4x faster on AVX2.
            if cap[0] < 6 or compute_type == "int8":
                device = "cpu"
                compute_type = "int8"
            else:
                device = "cuda"
                if compute_type == "auto":
                    compute_type = "float16"
        else:
            device = "cpu"
            if compute_type == "auto":
                compute_type = "int8"

    if compute_type == "auto":
        compute_type = "int8" if device == "cpu" else "float32"

    # Initialize model
    model = WhisperModel(model_size, device=device, compute_type=compute_type)

    # Transcribe with word timestamps and Silero VAD
    segments_gen, info = model.transcribe(
        str(audio_path),
        language=language,
        task=task,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500)
    )

    all_words = []
    raw_segments = []

    for seg in segments_gen:
        words_list = []
        if seg.words:
            for w in seg.words:
                words_list.append({
                    "word": w.word,
                    "start": round(w.start, 3),
                    "end": round(w.end, 3),
                    "probability": round(w.probability, 3)
                })
                all_words.append({
                    "word": w.word,
                    "start": round(w.start, 3),
                    "end": round(w.end, 3),
                    "probability": round(w.probability, 3)
                })

        raw_segments.append({
            "start": round(seg.start, 3),
            "end": round(seg.end, 3),
            "text": seg.text.strip(),
            "words": words_list
        })

    return {
        "status": "ok",
        "language": info.language,
        "language_probability": round(info.language_probability, 4),
        "duration": round(info.duration, 2),
        "words": all_words,
        "raw_segments": raw_segments
    }


def main():
    parser = argparse.ArgumentParser(description="Standalone Faster-Whisper ASR runner")
    parser.add_argument("--audio", required=True, help="Input audio file")
    parser.add_argument("--model", default="base", help="Model size (base, small, medium, large-v3)")
    parser.add_argument("--language", default=None, help="Forced language code (optional)")
    parser.add_argument("--device", default="auto", choices=["auto", "cuda", "cpu"])
    parser.add_argument("--compute-type", default="auto")
    parser.add_argument("--task", default="transcribe", choices=["transcribe", "translate"])
    args = parser.parse_args()

    try:
        lang = args.language if args.language and args.language != "None" else None
        res = run_transcription(Path(args.audio), args.model, lang, args.device, args.compute_type, task=args.task)
        print(json.dumps(res, ensure_ascii=True))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=True))
        sys.exit(1)


if __name__ == "__main__":
    main()
