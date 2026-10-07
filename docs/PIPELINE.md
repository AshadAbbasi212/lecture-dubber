# Processing pipeline

Every stage reads inputs from storage, writes outputs to storage, records
artifacts, reports progress, and is skipped if its output exists.

## Stage 1: Ingest
Fetch or assemble the source file, validate with `ffprobe`, enforce limits,
store as `source.mp4` (remux if needed; do not re-encode unless required).

## Stage 2: Extract audio
`ffmpeg -i source.mp4 -vn -ac 2 -ar 44100 original.wav` (keep a 16 kHz mono copy for ASR).

## Stage 3: Separate voice and background
Demucs (or an equivalent permissively licensed separator) produces `vocals.wav`
and `background.wav`. Run on the whole file in overlapping chunks to fit 8 GB.
`vocals.wav` is also the source of the **voice reference clip** (see Stage 7).

## Stage 4: Transcribe and detect language
faster-whisper / WhisperX on `vocals.wav`. Output word-level timestamps and the
detected language (with probability). For long lectures process in windows with
VAD so memory stays flat. Merge words into **sentence-level segments** (target
2 to 15 seconds each) and write `transcript.json`.
Watch out: ASR quality is weaker for some languages (including Urdu). Report the
detected language and confidence to the user and let them override it.

## Stage 5: Translate
Local LLM or MT model (chosen in Phase 0). For each segment:
- give the model neighbouring segments as context;
- ask for short, spoken-style sentences, clear for learners;
- apply a glossary (technical terms, names) for consistency across the lecture;
- give a **length budget** (target characters or syllables from the source
  duration and the target language's typical speaking rate), and generate a
  shorter alternative if the first result overshoots by more than about 15%.
Write `translation.json` and the `segments` rows.
Quality gate: a second automatic pass flags segments where meaning may have
drifted (back-translation similarity) so the reviewer sees them first.

## Stage 6: Review (user)
Job enters `awaiting_review`. The UI shows original vs translated text with
flags. Edits are saved to `segments.tgt_text` with `edited_by_user = true`.
`approve` moves on. Edited segments override any later automatic rewrite.

## Stage 7: Synthesize (voice generation)
Goal: target-language speech in the speaker's voice.
- Build a clean **reference clip** (10 to 30 s) from `vocals.wav`: low noise, one speaker, neutral delivery.
- Two possible designs (Phase 0 decides which works for each language):
  A. A TTS model that clones directly across languages.
  B. A good plain TTS voice for the language, followed by a **voice conversion**
     model that moves the result to the speaker's timbre. (Likely needed for
     Urdu if no cloning TTS exists with a commercial license.)
- Generate per segment, measure duration, then **fit to timing**:
  1. ratio = tts_duration / original_duration;
  2. if ratio within about 0.9 to 1.15, time-stretch slightly (rubberband / atempo);
  3. otherwise request a shorter or longer translation and regenerate;
  4. never stretch beyond about 1.25 (sounds robotic); allow the segment to borrow
     adjacent silence instead.
- Save `tts/seg_XXXX.wav` and the stretch ratio.

## Stage 8: Mix
Place segments on a timeline at their original start times, add `background.wav`
at its original level, apply light ducking and loudness normalisation
(about -16 LUFS). Output `dub_mix.wav`.

## Stage 9: Lip-sync (DEFERRED: not built in v1)

> Kept as the design for the later milestone. Do not implement or install lip-sync models in v1.
- Split the video into shots (PySceneDetect).
- For each shot, run face detection and tracking. Lip-sync only shots with a
  clear, mostly frontal, large-enough face. Others keep the original video.
- Cut the new audio to match each shot, run the lip-sync model on the face crop,
  blend the result back into the frame (with face restoration only if it fits the
  VRAM and license budget).
- Process in short clips (for example 20 to 60 seconds) and write each result
  to disk so a crash loses at most one clip.
- Quality gate: if the model's output fails a sanity check (face lost, large
  artifacts), fall back to the original video for that clip.
- This is the slowest stage on 8 GB. Benchmark it in Phase 0 and show an
  honest time estimate to users.

## Stage 10: Mux
v1: copy the original video stream untouched, attach `dub_mix.wav`, write
`final.mp4` with AI-dubbed metadata, verify duration and A/V sync.

(Later milestone: concatenate the lip-synced shots instead of copying the original video.)

## GPU / VRAM discipline
- One GPU stage at a time, guarded by a lock.
- Each model runs in a subprocess; exit frees VRAM.
- Use half precision or int8 where quality allows; record peak VRAM per stage in logs.

## Progress reporting
Each stage reports `(stage, done_units, total_units)`. The API converts this into
an overall percentage using stage weights measured during benchmarking.
