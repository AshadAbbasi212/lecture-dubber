import argparse
import json
import re
import sys
import time
from pathlib import Path

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
except ImportError:
    print(json.dumps({"status": "error", "message": "transformers or torch not installed in environment."}))
    sys.exit(1)


LANGUAGE_NAMES = {
    "en": "English",
    "es": "Spanish",
    "ar": "Arabic",
    "zh": "Chinese (Simplified Mandarin)",
    "ru": "Russian",
    "ur": "Urdu",
    "fr": "French",
    "de": "German (Deutsch)",
    "hi": "Hindi",
    "pt": "Portuguese",
    "it": "Italian",
    "tr": "Turkish",
}


def sanitize_target_text(text: str, tgt_code: str) -> str:
    """
    Cleans unwanted prefixes, line numbering, and script leaks.
    """
    if not text:
        return ""
    text = text.strip().strip('"\' \n')
    text = re.sub(r"^\d+[\.\)\-:]\s*", "", text).strip()
    text = re.sub(
        r"^(German|English|Arabic|Spanish|French|Russian|Chinese|Urdu|Deutsch)\s*(Translation)?:\s*",
        "",
        text,
        flags=re.IGNORECASE
    ).strip()

    # Filter out leaked foreign characters in Latin-script target languages
    if tgt_code in ["en", "de", "es", "fr", "it", "pt", "tr"]:
        # Strip Chinese, Cyrillic, Arabic, Devanagari characters
        text = re.sub(r"[\u4E00-\u9FFF\u0400-\u04FF\u0600-\u06FF\u0900-\u097F]", "", text).strip()

    # Filter out Latin letters if target is Arabic
    if tgt_code == "ar":
        # Keep Arabic letters, digits, punctuation, strip Latin leakages
        # Only strip if the text already contains Arabic letters
        has_ar = any('\u0600' <= c <= '\u06FF' for c in text)
        if has_ar:
            text = re.sub(r"[a-zA-Z]", "", text).strip()

    return text.strip()


def parse_numbered_output(raw_output: str, tgt_code: str) -> dict:
    """
    Extracts {item_index: translated_text} from numbered multiline LLM output.
    Supports formats: '1. text', '1) text', '1 - text', '[1] text'.
    """
    parsed = {}
    for line in raw_output.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^\[?(\d+)\]?[\.\)\-:]\s*(.+)$", line)
        if m:
            try:
                num = int(m.group(1))
                clean_txt = sanitize_target_text(m.group(2), tgt_code)
                if clean_txt:
                    parsed[num] = clean_txt
            except Exception:
                pass
    return parsed


def translate_single_segment_prompt(
    text: str,
    src_name: str,
    tgt_name: str,
    tgt_code: str,
    tok,
    model,
    device
) -> str:
    """
    Fallback single-segment translator if a line was skipped in batch.
    """
    prompt = (
        f"Translate the following speech sentence from {src_name} to natural spoken {tgt_name}.\n"
        f"Output ONLY the {tgt_name} translation:\n"
        f"Sentence: {text}\n"
        f"Translation:"
    )
    msgs = [
        {"role": "system", "content": f"You are a professional translator from {src_name} to {tgt_name}."},
        {"role": "user", "content": prompt}
    ]
    chat = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    inp = tok([chat], return_tensors="pt").to(device)
    with torch.no_grad():
        out = model.generate(
            **inp,
            max_new_tokens=96,
            do_sample=False,
            pad_token_id=tok.eos_token_id
        )
    raw = tok.decode(out[0][len(inp.input_ids[0]):], skip_special_tokens=True).strip()
    return sanitize_target_text(raw, tgt_code)


def translate_batch(
    segments_data: list,
    src_lang: str,
    tgt_lang: str,
    model_name: str = "Qwen/Qwen2.5-0.5B-Instruct"
) -> list:
    src_code = src_lang.lower()[:2]
    tgt_code = tgt_lang.lower()[:2]
    src_name = LANGUAGE_NAMES.get(src_code, "English")
    tgt_name = LANGUAGE_NAMES.get(tgt_code, "English")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32

    tok = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=dtype,
        device_map=device
    )

    batch_size = 12
    final_translations = {}

    # Check if two-step pivot (Urdu -> English -> Target) is required
    use_two_step = (src_code == "ur" and tgt_code != "en")

    for b_idx in range(0, len(segments_data), batch_size):
        batch = segments_data[b_idx : b_idx + batch_size]
        if not batch:
            continue

        valid_items = [item for item in batch if (item.get("text") or "").strip()]
        if not valid_items:
            for item in batch:
                final_translations[item.get("idx")] = ""
            continue

        numbered_src = "\n".join([f"{item['idx']}. {item['text'].strip()}" for item in valid_items])

        if use_two_step:
            # Step A: Urdu -> English
            p1 = (
                "Translate each numbered Urdu sentence into clear, natural spoken English.\n"
                "Output each sentence with its original number:\n"
                f"{numbered_src}\n"
            )
            msgs1 = [
                {"role": "system", "content": "You are a professional educational translator from Urdu to English. Output only numbered lines."},
                {"role": "user", "content": p1}
            ]
            chat1 = tok.apply_chat_template(msgs1, tokenize=False, add_generation_prompt=True)
            inp1 = tok([chat1], return_tensors="pt").to(device)
            with torch.no_grad():
                out1 = model.generate(**inp1, max_new_tokens=500, do_sample=False, pad_token_id=tok.eos_token_id)
            eng_output = tok.decode(out1[0][len(inp1.input_ids[0]):], skip_special_tokens=True).strip()

            # Step B: English -> Target
            p2 = (
                f"Translate each numbered English sentence into natural, fluent {tgt_name}.\n"
                f"Output strictly {tgt_name} sentences with their numbers:\n"
                f"{eng_output}\n"
            )
            msgs2 = [
                {"role": "system", "content": f"You are a professional translator from English to {tgt_name}. Output strictly fluent {tgt_name}."},
                {"role": "user", "content": p2}
            ]
            chat2 = tok.apply_chat_template(msgs2, tokenize=False, add_generation_prompt=True)
            inp2 = tok([chat2], return_tensors="pt").to(device)
            with torch.no_grad():
                out2 = model.generate(**inp2, max_new_tokens=500, do_sample=False, pad_token_id=tok.eos_token_id)
            tgt_output = tok.decode(out2[0][len(inp2.input_ids[0]):], skip_special_tokens=True).strip()

            parsed = parse_numbered_output(tgt_output, tgt_code)

        else:
            # Direct Translation Step
            p = (
                f"Translate each numbered sentence from {src_name} into natural, spoken {tgt_name}.\n"
                f"Output strictly {tgt_name} sentences with their numbers:\n"
                f"{numbered_src}\n"
            )
            msgs = [
                {"role": "system", "content": f"You are a professional translator from {src_name} to {tgt_name}. Output strictly fluent {tgt_name}."},
                {"role": "user", "content": p}
            ]
            chat = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
            inp = tok([chat], return_tensors="pt").to(device)
            with torch.no_grad():
                out = model.generate(**inp, max_new_tokens=500, do_sample=False, pad_token_id=tok.eos_token_id)
            tgt_output = tok.decode(out[0][len(inp.input_ids[0]):], skip_special_tokens=True).strip()

            parsed = parse_numbered_output(tgt_output, tgt_code)

        # Merge parsed lines, recover any missing line individually
        for item in batch:
            idx = item.get("idx")
            src_txt = (item.get("text") or "").strip()
            if not src_txt:
                final_translations[idx] = ""
                continue

            if idx in parsed and parsed[idx]:
                final_translations[idx] = parsed[idx]
            else:
                # Targeted single-segment fallback to guarantee 100% segment coverage
                single_res = translate_single_segment_prompt(
                    src_txt,
                    "English" if use_two_step else src_name,
                    tgt_name,
                    tgt_code,
                    tok,
                    model,
                    device
                )
                final_translations[idx] = single_res if single_res else src_txt

    results = []
    for item in segments_data:
        idx = item.get("idx")
        results.append({
            "idx": idx,
            "tgt_text": final_translations.get(idx, "")
        })

    return results


def main():
    parser = argparse.ArgumentParser(description="Standalone Multilingual Translation Runner")
    parser.add_argument("--input", required=True, help="Input JSON file with segments")
    parser.add_argument("--src-lang", default="ur", help="Source language code")
    parser.add_argument("--tgt-lang", default="en", help="Target language code")
    parser.add_argument("--output", required=True, help="Output JSON file for translated segments")
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct", help="Hugging Face model ID")
    args = parser.parse_args()

    try:
        input_file = Path(args.input)
        output_file = Path(args.output)

        with open(input_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        segments = raw_data.get("segments", raw_data if isinstance(raw_data, list) else [])
        translated = translate_batch(segments, args.src_lang, args.tgt_lang, args.model)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({"translations": translated}, f, ensure_ascii=False, indent=2)

        print(json.dumps({"status": "ok", "count": len(translated)}))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
