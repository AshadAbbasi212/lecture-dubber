"""
Subtitle and Closed Captions Generator (SRT & WebVTT)
Generates synchronized subtitle tracks with clean formatting and speaker labels.
"""

from pathlib import Path
from typing import List, Union, Any


def format_timestamp_srt(seconds: float) -> str:
    """Format seconds into SRT timestamp: HH:MM:SS,mmm"""
    if seconds < 0:
        seconds = 0.0
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milli = int(round((seconds - int(seconds)) * 1000))
    if milli >= 1000:
        milli = 999
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{milli:03d}"


def format_timestamp_vtt(seconds: float) -> str:
    """Format seconds into WebVTT timestamp: HH:MM:SS.mmm"""
    if seconds < 0:
        seconds = 0.0
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milli = int(round((seconds - int(seconds)) * 1000))
    if milli >= 1000:
        milli = 999
    return f"{hrs:02d}:{mins:02d}:{secs:02d}.{milli:03d}"


def _get_field(seg: Any, field: str, default: Any = "") -> Any:
    if isinstance(seg, dict):
        return seg.get(field, default)
    return getattr(seg, field, default)


def generate_srt(segments: List[Any], output_path: Path, include_speaker: bool = True) -> Path:
    """
    Generates standard SubRip (.srt) subtitle file from segments.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = []

    for i, seg in enumerate(segments, start=1):
        start = float(_get_field(seg, "start", 0.0))
        end = float(_get_field(seg, "end", start + 2.0))
        text = str(_get_field(seg, "tgt_text") or _get_field(seg, "en_text") or _get_field(seg, "text", "")).strip()
        speaker = str(_get_field(seg, "speaker", "")).strip()

        if not text:
            continue

        start_ts = format_timestamp_srt(start)
        end_ts = format_timestamp_srt(end)

        speaker_label = ""
        if include_speaker and speaker:
            spk_display = "Sheikh-ul-Wazaif" if "sheikh" in speaker.lower() else ("Narrator" if "narrator" in speaker.lower() else speaker.capitalize())
            speaker_label = f"[{spk_display}] "

        lines.append(str(i))
        lines.append(f"{start_ts} --> {end_ts}")
        lines.append(f"{speaker_label}{text}")
        lines.append("")

    content = "\n".join(lines)
    output_path.write_text(content, encoding="utf-8")
    return output_path


def generate_vtt(segments: List[Any], output_path: Path, include_speaker: bool = True) -> Path:
    """
    Generates standard WebVTT (.vtt) subtitle file from segments.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["WEBVTT", ""]

    for i, seg in enumerate(segments, start=1):
        start = float(_get_field(seg, "start", 0.0))
        end = float(_get_field(seg, "end", start + 2.0))
        text = str(_get_field(seg, "tgt_text") or _get_field(seg, "en_text") or _get_field(seg, "text", "")).strip()
        speaker = str(_get_field(seg, "speaker", "")).strip()

        if not text:
            continue

        start_ts = format_timestamp_vtt(start)
        end_ts = format_timestamp_vtt(end)

        speaker_tag = ""
        if include_speaker and speaker:
            spk_display = "Sheikh-ul-Wazaif" if "sheikh" in speaker.lower() else ("Narrator" if "narrator" in speaker.lower() else speaker.capitalize())
            speaker_tag = f"<v {spk_display}>"

        lines.append(f"{start_ts} --> {end_ts}")
        lines.append(f"{speaker_tag}{text}")
        lines.append("")

    content = "\n".join(lines)
    output_path.write_text(content, encoding="utf-8")
    return output_path
