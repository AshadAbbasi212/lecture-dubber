import sys
import time
import json
import torch
from pathlib import Path

# Force utf-8 for Windows console
sys.stdout.reconfigure(encoding='utf-8')

from transformers import AutoModelForCausalLM, AutoTokenizer

test_sentences_en = [
    "Today we will study gradient descent and backpropagation in deep neural networks.",
    "A binary search tree has a lookup time complexity of O(log n) on average.",
    "Mitochondria are often referred to as the powerhouse of the biological cell.",
    "Newton's second law states that force equals mass multiplied by acceleration.",
    "Quantum computing uses qubits that can exist in a superposition of states.",
    "Photosynthesis converts carbon dioxide and sunlight into glucose and oxygen.",
    "Operating systems manage hardware resources through virtual memory and scheduling.",
    "In statistics, the central limit theorem explains why normal distributions are common.",
    "Supply and demand curves determine the equilibrium market price of goods.",
    "Plate tectonics explains continental drift and the cause of major earthquakes.",
]

test_sentences_ur = [
    "آج ہم ڈیپ نیورل نیٹ ورکس میں گریڈینٹ ڈیسینٹ اور بیک پروپیگیشن کا مطالعہ کریں گے۔",
    "بائنری سرچ ٹری میں اوسطاً تلاش کرنے کی لاگت لاگ این ہوتی ہے۔",
    "مائٹوکونڈریا کو عام طور پر خلیے کا پاور ہاؤس کہا جاتا ہے۔",
    "نیوٹن کا دوسرا قانون بیان کرتا ہے کہ قوت ماس اور ایکسلریشن کے ضرب کے برابر ہے۔",
    "کوانٹم کمپیوٹنگ کیوبٹس کا استعمال کرتی ہے جو سپر پوزیشن میں رہ سکتے ہیں۔",
    "فوٹو سنتھیسس کاربن ڈائی آکسائیڈ اور سورج کی روشنی کو گلوکوز اور آکسیجن میں تبدیل کرتا ہے۔",
    "آپریٹنگ سسٹم ورچوئل میموری اور شیڈولنگ کے ذریعے ہارڈ ویئر کے وسائل کا انتظام کرتے ہیں۔",
    "شماریات میں مرکزی حد کا نظریہ بتاتا ہے کہ نارمل ڈسٹری بیوشن کیوں عام ہے۔",
    "طلب اور رسد کے خطوط اشیاء کی مارکیٹ میں متوازن قیمت کا تعین کرتے ہیں۔",
    "پلیٹ ٹیکٹونکس براعظموں کے بہاؤ اور بڑے زلزلوں کی وجوہات کی وضاحت کرتی ہے۔",
]

print("Loading Qwen2.5-0.5B-Instruct...")
model_name = "Qwen/Qwen2.5-0.5B-Instruct"
t0 = time.time()
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float32,
    device_map="cpu"
)
load_time = time.time() - t0
print(f"Model loaded in {load_time:.2f}s")

def translate(text, src_lang, tgt_lang, max_words=None):
    constraint = f" Keep the translation concise (under {max_words} words)." if max_words else ""
    prompt = f"Translate the following educational lecture sentence from {src_lang} to {tgt_lang}. Output only the translation, no explanation.{constraint}\nSentence: {text}"
    messages = [
        {"role": "system", "content": "You are a professional educational translator specializing in clear academic explanations."},
        {"role": "user", "content": prompt}
    ]
    text_input = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([text_input], return_tensors="pt")
    
    t0 = time.time()
    outputs = model.generate(**inputs, max_new_tokens=64, do_sample=False)
    elapsed = time.time() - t0
    
    generated_ids = [output_ids[len(input_ids):] for input_ids, output_ids in zip(inputs.input_ids, outputs)]
    response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
    return response, elapsed

results = {"en_to_ur": [], "ur_to_en": [], "length_control": []}

print("\n--- Evaluating English to Urdu (10 sentences) ---")
for i, sent in enumerate(test_sentences_en, 1):
    trans, el = translate(sent, "English", "Urdu")
    results["en_to_ur"].append({"idx": i, "en": sent, "ur": trans, "time_s": round(el, 2)})
    print(f"[{i}/10] Translated in {el:.2f}s")

print("\n--- Evaluating Length Control ---")
sent = "A binary search tree has a lookup time complexity of O(log n) on average."
orig, _ = translate(sent, "English", "Urdu")
short, _ = translate(sent, "English", "Urdu", max_words=6)
results["length_control"].append({"orig": orig, "short": short})
print(f"Length control test finished")

print("\n--- Evaluating Urdu to English (10 sentences) ---")
for i, sent in enumerate(test_sentences_ur, 1):
    trans, el = translate(sent, "Urdu", "English")
    results["ur_to_en"].append({"idx": i, "ur": sent, "en": trans, "time_s": round(el, 2)})
    print(f"[{i}/10] Translated in {el:.2f}s")

out_file = Path("spikes/test_data/translation_results.json")
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\nAll 20 translations written to {out_file} successfully!")
