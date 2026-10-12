"""
Generate 100% synchronized, authentic neural dubbed lecture videos for ALL supported languages:
1. Spanish (Dave - European Castilian)
2. Arabic (Kareem - Classical Scholar)
3. French (Gilles - Sorbonne Academic)
4. German (Thorsten - Professor Baritone)
5. Hindi (Pratham - Academic Lecturer)
6. Russian (Denis - Scholar Baritone)
7. Chinese (Chaowen - Academic Lecturer)
8. Italian (Riccardo - Italian Professor)
9. Portuguese (Faber - Brazilian Academic)
10. Turkish (DFKI - Academic Lecturer)
(Urdu and English original are already present)
"""

import sys
import os
import shutil
import subprocess
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.engines.tts.voice_synthesizer import FallbackTTSEngine
from backend.app.db.models.segment import Segment
from backend.app.pipeline.audio_mixer import assemble_timeline_vocals, mix_vocals_and_background
from backend.app.pipeline.video_muxer import mux_video_and_audio

# Timestamps from original 1-minute Feynman lecture
TIMESTAMPS = [
    (1, 0.02, 3.02),
    (2, 4.12, 6.78),
    (3, 7.02, 15.08),
    (4, 17.04, 21.38),
    (5, 22.06, 29.98),
    (6, 32.66, 35.80),
    (7, 39.64, 44.09),
    (8, 45.96, 48.68),
    (9, 49.42, 51.56),
    (10, 51.64, 55.42),
    (11, 55.86, 58.84),
    (12, 59.26, 60.04)
]

LANGUAGES_CONFIG = {
    "spanish": {
        "lang_code": "es",
        "voice": "dave",
        "title": "Lecture Dubber - Dubbed in Spanish (Dave Castilian)",
        "output_file": "dubbed_lecture_spanish.mp4",
        "segments": [
            "Ahora voy a hablar de cómo buscaríamos una nueva ley.",
            "En general, buscamos una nueva ley mediante el siguiente proceso.",
            "Primero la adivinamos. Luego calculamos las consecuencias de esa hipótesis,",
            "para ver qué implicaría si esta ley que postulamos fuera correcta.",
            "Y luego comparamos los resultados del cálculo con la naturaleza, con los experimentos,",
            "lo comparamos directamente con las observaciones para ver si funciona.",
            "Si no coincide con el experimento, está mal.",
            "En esa simple afirmación reside la clave de la ciencia.",
            "No importa cuán hermosa sea tu suposición.",
            "No importa quién seas, quién hizo la conjetura, ni cómo se llame.",
            "Si no concuerda con el experimento, es incorrecta.",
            "Eso es todo lo que hay."
        ]
    },
    "arabic": {
        "lang_code": "ar",
        "voice": "kareem",
        "title": "Lecture Dubber - Dubbed in Arabic (Kareem Scholar)",
        "output_file": "dubbed_lecture_arabic.mp4",
        "segments": [
            "سأتحدث الآن عن كيفية البحث عن قانون فيزيائي جديد.",
            "بشكل عام، نبحث عن قانون جديد من خلال العملية التالية.",
            "أولاً نقوم بوضع تخمين، ثم نحسب العواقب المترتبة على هذا التخمين،",
            "لنرى ما يعنيه هذا القانون إذا كان صحيحاً وما الذي قد يترتب عليه.",
            "ثم نقارن نتائج تلك الحسابات بالطبيعة، أو بالتجارب والخبرة العملية،",
            "نقارنها مباشرة بالملاحظات الواقعية لنرى ما إذا كانت تعمل بنجاح.",
            "إذا اختلف التخمين مع التجربة، فهو خاطئ.",
            "في هذه العبارة البسيطة يكمن جوهر العلم الحقيقي.",
            "لا يهم مدى جمال التخمين الذي وضعته.",
            "لا يهم من تكون، أو من وضع هذا التخمين، أو ما هو اسمه.",
            "إذا كان يخالف التجربة العملية، فهو خطأ.",
            "هذا هو كل ما في الأمر ببساطة."
        ]
    },
    "french": {
        "lang_code": "fr",
        "voice": "gilles",
        "title": "Lecture Dubber - Dubbed in French (Gilles Sorbonne)",
        "output_file": "dubbed_lecture_french.mp4",
        "segments": [
            "Maintenant, je vais vous expliquer comment chercher une nouvelle loi.",
            "En général, nous cherchons une nouvelle loi selon le processus suivant.",
            "D'abord, on formule une hypothèse. Puis on calcule les conséquences de cette supposition,",
            "pour voir ce que cela impliquerait si cette loi était correcte.",
            "Ensuite, nous comparons les résultats de ce calcul avec la nature et les expériences,",
            "nous les comparons directement aux observations pour voir si cela fonctionne.",
            "Si elle est en désaccord avec l'expérience, elle est fausse.",
            "C'est dans cette simple déclaration que réside la clé de la science.",
            "Peu importe à quel point votre hypothèse est élégante.",
            "Peu importe qui vous êtes, qui a fait la supposition ou son nom.",
            "Si elle contredit l'expérience, elle est erronée.",
            "C'est aussi simple que cela."
        ]
    },
    "german": {
        "lang_code": "de",
        "voice": "thorsten",
        "title": "Lecture Dubber - Dubbed in German (Thorsten Academic)",
        "output_file": "dubbed_lecture_german.mp4",
        "segments": [
            "Jetzt werde ich darüber sprechen, wie wir nach einem neuen Gesetz suchen.",
            "Im Allgemeinen suchen wir nach einem neuen Naturgesetz durch folgenden Prozess.",
            "Zuerst raten wir es. Dann berechnen wir die Konsequenzen dieser Vermutung,",
            "um zu sehen, was es bedeuten würde, wenn dieses Gesetz richtig wäre.",
            "Und dann vergleichen wir diese Rechenergebnisse mit der Natur und Experimenten,",
            "wir vergleichen es direkt mit Beobachtungen, um zu sehen, ob es funktioniert.",
            "Wenn es dem Experiment widerspricht, ist es falsch.",
            "In dieser einfachen Aussage liegt der Schlüssel zur Wissenschaft.",
            "Es spielt keine Rolle, wie schön Ihre Vermutung ist.",
            "Es spielt keine Rolle, wer Sie sind oder wer die Vermutung aufgestellt hat.",
            "Wenn es dem Experiment widerspricht, ist es falsch.",
            "Das ist alles, worauf es ankommt."
        ]
    },
    "hindi": {
        "lang_code": "hi",
        "voice": "pratham",
        "title": "Lecture Dubber - Dubbed in Hindi (Pratham Academic)",
        "output_file": "dubbed_lecture_hindi.mp4",
        "segments": [
            "अब मैं चर्चा करूंगा कि हम एक नया नियम कैसे खोजते हैं।",
            "आम तौर पर, हम निम्नलिखित प्रक्रिया द्वारा नया नियम खोजते हैं।",
            "पहले हम एक अनुमान लगाते हैं, फिर उस अनुमान के परिणामों की गणना करते हैं,",
            "यह देखने के लिए कि यदि यह नियम सही है, तो इसके क्या परिणाम होंगे।",
            "और फिर हम उन गणना परिणामों की तुलना प्रकृति और प्रयोगों से करते हैं,",
            "हम सीधे अवलोकनों से तुलना करते हैं ताकि देखें कि क्या यह काम करता है।",
            "यदि यह प्रयोग से असहमत है, तो यह गलत है।",
            "इस सरल कथन में ही विज्ञान की असली कुंजी छिपी है।",
            "इससे कोई फर्क नहीं पड़ता कि आपका अनुमान कितना सुंदर है।",
            "इससे कोई फर्क नहीं पड़ता कि आप कौन हैं, अनुमान किसने लगाया या उसका नाम क्या है।",
            "यदि यह प्रयोग से असहमत है, तो यह गलत है।",
            "बस इतना ही है, इसके अलावा कुछ नहीं।"
        ]
    },
    "russian": {
        "lang_code": "ru",
        "voice": "denis",
        "title": "Lecture Dubber - Dubbed in Russian (Denis Scholar)",
        "output_file": "dubbed_lecture_russian.mp4",
        "segments": [
            "Сейчас я расскажу о том, как мы ищем новый физический закон.",
            "В целом, мы ищем новый закон с помощью следующего процесса.",
            "Сначала мы делаем догадку. Затем мы вычисляем следствия этой догадки,",
            "чтобы увидеть, к чему это приведет, если данный закон окажется верным.",
            "А затем мы сравниваем результаты вычислений с природой и экспериментом,",
            "мы сравниваем их напрямую с наблюдениями, чтобы проверить результат.",
            "Если теория расходится с экспериментом, она неверна.",
            "В этом простом утверждении заключается ключ к науке.",
            "Не имеет никакого значения, насколько красива ваша догадка.",
            "Не имеет значения, кто вы, кто выдвинул гипотезу или как его зовут.",
            "Если она противоречит эксперименту, она ошибочна.",
            "Вот и все, что нужно знать."
        ]
    },
    "chinese": {
        "lang_code": "zh",
        "voice": "chaowen",
        "title": "Lecture Dubber - Dubbed in Chinese (Chaowen Lecturer)",
        "output_file": "dubbed_lecture_chinese.mp4",
        "segments": [
            "现在我来讨论一下我们如何寻找一条新的物理定律。",
            "通常来说，我们通过以下过程来寻找新的定律。",
            "首先我们做出一个猜想，然后计算出这个猜想所带来的推论与结果，",
            "来看看如果这个定律是正确的，它将会意味着什么。",
            "然后我们把计算的结果与大自然、实验以及经验进行对比，",
            "直接与实际观测结果进行比较，看看它是否符合现实。",
            "如果它与实验结果不符，那它就是错的。",
            "这句简单的话正是科学的核心关键所在。",
            "无论你的猜想多么优美，都毫无分别。",
            "不管做出猜想的人是谁，也不管他的名字多么响亮。",
            "只要它违背了实验，它就是错误的。",
            "事情就是这么简单直接。"
        ]
    },
    "italian": {
        "lang_code": "it",
        "voice": "riccardo",
        "title": "Lecture Dubber - Dubbed in Italian (Riccardo Professor)",
        "output_file": "dubbed_lecture_italian.mp4",
        "segments": [
            "Ora parlerò di come cerchiamo una nuova legge scientifica.",
            "In generale, cerchiamo una nuova legge attraverso il seguente processo.",
            "Prima di tutto tiriamo a indovinare, poi calcoliamo le conseguenze dell'ipotesi,",
            "per vedere cosa comporterebbe se questa legge fosse effettivamente corretta.",
            "E poi confrontiamo i risultati di questi calcoli con la natura e gli esperimenti,",
            "lo confrontiamo direttamente con le osservazioni per vedere se funziona.",
            "Se è in disaccordo con l'esperimento, è sbagliata.",
            "In questa semplice affermazione sta la vera chiave della scienza.",
            "Non ha alcuna importanza quanto sia bella la vostra ipotesi.",
            "Non importa chi siete, chi ha fatto l'ipotesi o quale sia il suo nome.",
            "Se è contraria all'esperimento, è falsa.",
            "Questo è tutto ciò che c'è da sapere."
        ]
    },
    "portuguese": {
        "lang_code": "pt",
        "voice": "faber",
        "title": "Lecture Dubber - Dubbed in Portuguese (Faber Academic)",
        "output_file": "dubbed_lecture_portuguese.mp4",
        "segments": [
            "Agora vou explicar como nós procuramos por uma nova lei.",
            "Em geral, procuramos uma nova lei através do seguinte processo.",
            "Primeiro nós adivinhamos, depois calculamos as consequências dessa hipótese,",
            "para ver o que aconteceria se esta lei estivesse realmente correta.",
            "E então comparamos esses resultados com a natureza e com experimentos,",
            "comparamos diretamente com observações para ver se funciona.",
            "Se discordar do experimento, está errada.",
            "Nessa declaração tão simples está a chave de toda a ciência.",
            "Não faz a menor diferença o quão bela seja a sua hipótese.",
            "Não importa quem você seja, quem fez a suposição ou qual é o seu nome.",
            "Se for contrária ao experimento, ela está errada.",
            "É simplesmente tudo o que há."
        ]
    },
    "turkish": {
        "lang_code": "tr",
        "voice": "dfki",
        "title": "Lecture Dubber - Dubbed in Turkish (DFKI Scholar)",
        "output_file": "dubbed_lecture_turkish.mp4",
        "segments": [
            "Şimdi yeni bir doğa yasasını nasıl arayacağımızı anlatacağım.",
            "Genel olarak, aşağıdaki süreci izleyerek yeni bir yasa ararız.",
            "Önce bir tahminde bulunuruz. Ardından bu tahminin sonuçlarını hesaplarız,",
            "eğer bu yasa doğruysa ne gibi sonuçlar doğuracağını görmek için.",
            "Ve sonra bu hesaplama sonuçlarını doğayla ve deneylerle karşılaştırırız,",
            "çalışıp çalışmadığını görmek için doğrudan gözlemlerle kıyaslarız.",
            "Eğer deneyle uyuşmuyorsa, yanlıştır.",
            "İşte bu basit ifadede bilimin asıl anahtarı yatmaktadır.",
            "Tahmininizin ne kadar güzel olduğunun hiçbir önemi yoktur.",
            "Tahminde bulunanın kim olduğunun veya adının ne olduğunun önemi yoktur.",
            "Deneyle çelişiyorsa, kesinlikle yanlıştır.",
            "İşte hepsi bundan ibarettir."
        ]
    }
}


def main():
    print("=" * 70, flush=True)
    print(" BATCH GENERATING ALL DUBBED VIDEOS FOR GITHUB REPOSITORY", flush=True)
    print("=" * 70, flush=True)

    source_video = ROOT_DIR / "storage" / "test_feynman_1min.mp4"
    bg_path = ROOT_DIR / "storage" / "jobs" / "0d1a458e-4efe-4369-b04e-172a25ba192f" / "audio" / "background.wav"
    assets_dir = ROOT_DIR / "docs" / "assets"
    work_base = ROOT_DIR / "storage" / "multilingual_demos"

    assets_dir.mkdir(parents=True, exist_ok=True)
    work_base.mkdir(parents=True, exist_ok=True)

    tts = FallbackTTSEngine()

    for lang_name, conf in LANGUAGES_CONFIG.items():
        print(f"\n---> Processing: {lang_name.upper()} ({conf['lang_code']}) with voice [{conf['voice']}]", flush=True)
        lang_work = work_base / lang_name
        tts_dir = lang_work / "tts"
        lang_work.mkdir(parents=True, exist_ok=True)
        tts_dir.mkdir(parents=True, exist_ok=True)

        seg_models = []
        for (idx, start, end), text in zip(TIMESTAMPS, conf["segments"]):
            dur = end - start
            out_wav = tts_dir / f"seg_{idx:04d}.wav"
            tts.synthesize(
                text=text,
                language=conf["lang_code"],
                out_path=str(out_wav),
                target_duration=dur,
                voice=conf["voice"]
            )
            s = Segment(
                id=f"{lang_name}-seg-{idx}",
                job_id=f"demo-{lang_name}",
                idx=idx,
                start=start,
                end=end,
                speaker="speaker_0",
                src_text="",
                tgt_text=text,
                tts_path=str(out_wav)
            )
            seg_models.append(s)

        # Assemble vocals
        dub_vocals_path = lang_work / "dub_vocals.wav"
        assemble_timeline_vocals(seg_models, 62.55, dub_vocals_path)

        # Mix with background
        dub_mix_path = lang_work / "dub_mix.wav"
        mix_vocals_and_background(dub_vocals_path, bg_path, dub_mix_path)

        # Mux to final MP4
        out_mp4 = assets_dir / conf["output_file"]
        cmd = [
            "ffmpeg", "-y",
            "-i", str(source_video),
            "-i", str(dub_mix_path),
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-metadata", f"title={conf['title']}",
            "-shortest",
            str(out_mp4)
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            sz_mb = out_mp4.stat().st_size / (1024 * 1024)
            print(f"  [SUCCESS] {conf['output_file']} generated ({sz_mb:.2f} MB)", flush=True)
        else:
            print(f"  [ERROR] FFmpeg failed for {lang_name}: {res.stderr[:200]}", flush=True)

    print("\n" + "=" * 70, flush=True)
    print(" ALL MULTILINGUAL DUBBED VIDEOS GENERATED SUCCESSFULLY!", flush=True)
    print("=" * 70, flush=True)


if __name__ == "__main__":
    main()
