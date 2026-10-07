import re
from typing import List, Optional
from backend.app.engines.base import WordTimestamp, TranscriptSegment

# Terminal punctuation in Latin and Urdu
TERMINAL_PUNCTUATION = {".", "!", "?", "۔", "؟"}
PAUSE_PUNCTUATION = {",", ";", ":", "-", "،", "؛"}


def merge_words_into_sentence_segments(
    words: List[WordTimestamp],
    min_duration: float = 2.0,
    max_duration: float = 15.0,
    pause_threshold: float = 0.6
) -> List[TranscriptSegment]:
    """
    Merges word-level timestamps into natural, sentence-level segments.
    - Targets 2 to 15 seconds per segment.
    - Splits on natural silence pauses (>= pause_threshold seconds).
    - Splits on terminal punctuation ('.', '!', '?', '۔', '؟').
    - Prevents unnatural run-on segments beyond max_duration.
    """
    if not words:
        return []

    segments: List[TranscriptSegment] = []
    current_words: List[WordTimestamp] = []
    seg_idx = 1

    def flush_segment():
        nonlocal seg_idx, current_words
        if not current_words:
            return
        text = " ".join(w.word.strip() for w in current_words).strip()
        start = current_words[0].start
        end = current_words[-1].end
        segments.append(
            TranscriptSegment(
                idx=seg_idx,
                start=round(start, 3),
                end=round(end, 3),
                text=text,
                words=list(current_words),
                speaker="speaker_0"
            )
        )
        seg_idx += 1
        current_words = []

    for i, word in enumerate(words):
        current_words.append(word)
        curr_text = word.word.strip()
        curr_dur = word.end - current_words[0].start

        has_next = i + 1 < len(words)
        next_word = words[i + 1] if has_next else None

        # Check for pause
        has_pause = (next_word.start - word.end >= pause_threshold) if next_word else False

        # Check for punctuation
        has_terminal_punct = any(curr_text.endswith(p) for p in TERMINAL_PUNCTUATION)
        has_pause_punct = any(curr_text.endswith(p) for p in PAUSE_PUNCTUATION)

        # Decision 1: Terminal punctuation and reached min_duration
        if has_terminal_punct and curr_dur >= min_duration:
            flush_segment()
            continue

        # Decision 2: Significant speech pause and reached min_duration
        if has_pause and curr_dur >= min_duration:
            flush_segment()
            continue

        # Decision 3: Approaching max_duration, split on pause punctuation or any pause
        if curr_dur >= (max_duration - 2.0) and (has_pause_punct or has_pause):
            flush_segment()
            continue

        # Decision 4: Hard limit reached, force flush to prevent oversized segment
        if curr_dur >= max_duration:
            flush_segment()
            continue

    flush_segment()
    return segments
