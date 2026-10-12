"""
Subtitle and Closed Captions Generator (SRT & WebVTT)
Generates synchronized subtitle tracks with clean formatting, speaker labels,
and multi-language subtitle bundle packages (.ZIP).
"""

import zipfile
from pathlib import Path
from typing import List, Union, Any, Optional


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


def generate_srt(segments: List[Any], output_path: Path, include_speaker: bool = True, use_source_text: bool = False) -> Path:
    """
    Generates standard SubRip (.srt) subtitle file from segments.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = []

    for i, seg in enumerate(segments, start=1):
        start = float(_get_field(seg, "start", 0.0))
        end = float(_get_field(seg, "end", start + 2.0))
        if use_source_text:
            text = str(_get_field(seg, "src_text") or _get_field(seg, "text", "")).strip()
        else:
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


def generate_bilingual_srt(segments: List[Any], output_path: Path) -> Path:
    """
    Generates synchronized bilingual SRT containing both target dubbed text and original source text.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = []

    for i, seg in enumerate(segments, start=1):
        start = float(_get_field(seg, "start", 0.0))
        end = float(_get_field(seg, "end", start + 2.0))
        tgt_text = str(_get_field(seg, "tgt_text") or _get_field(seg, "en_text") or "").strip()
        src_text = str(_get_field(seg, "src_text") or _get_field(seg, "text", "")).strip()
        speaker = str(_get_field(seg, "speaker", "")).strip()

        if not tgt_text and not src_text:
            continue

        start_ts = format_timestamp_srt(start)
        end_ts = format_timestamp_srt(end)

        spk_display = f"[{speaker.capitalize()}] " if speaker else ""

        lines.append(str(i))
        lines.append(f"{start_ts} --> {end_ts}")
        if tgt_text and src_text and tgt_text != src_text:
            lines.append(f"{spk_display}{tgt_text}\n({src_text})")
        else:
            lines.append(f"{spk_display}{tgt_text or src_text}")
        lines.append("")

    content = "\n".join(lines)
    output_path.write_text(content, encoding="utf-8")
    return output_path


def generate_transcript_txt(segments: List[Any], output_path: Path, title: str = "Lecture Transcript") -> Path:
    """
    Generates an educational, timestamped text transcript suitable for reading or printing.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"===========================================================",
        f"  {title.upper()}",
        f"  Generated by Lecture Dubber (Local AI Platform)",
        f"===========================================================",
        ""
    ]

    for seg in segments:
        start = float(_get_field(seg, "start", 0.0))
        end = float(_get_field(seg, "end", start + 2.0))
        tgt = str(_get_field(seg, "tgt_text") or _get_field(seg, "en_text") or "").strip()
        src = str(_get_field(seg, "src_text") or _get_field(seg, "text", "")).strip()
        speaker = str(_get_field(seg, "speaker", "Speaker")).strip()

        start_fmt = f"{int(start//60):02d}:{int(start%60):02d}"
        end_fmt = f"{int(end//60):02d}:{int(end%60):02d}"

        lines.append(f"[{start_fmt} - {end_fmt}] {speaker.upper()}:")
        if tgt:
            lines.append(f"  Target: {tgt}")
        if src:
            lines.append(f"  Source: {src}")
        lines.append("")

    content = "\n".join(lines)
    output_path.write_text(content, encoding="utf-8")
    return output_path


def create_subtitles_bundle_zip(
    segments: List[Any],
    output_zip_path: Path,
    target_lang: str,
    source_lang: str = "ur"
) -> Path:
    """
    Creates a comprehensive ZIP package with all subtitle formats and bilingual tracks:
    1. subtitles_{target_lang}.srt
    2. subtitles_{target_lang}.vtt
    3. subtitles_bilingual.srt
    4. subtitles_{source_lang}_original.srt
    5. lecture_transcript_{target_lang}.txt
    6. README.txt
    """
    output_zip_path.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = output_zip_path.parent / f"_temp_subs_{output_zip_path.stem}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        f_tgt_srt = temp_dir / f"subtitles_{target_lang}.srt"
        generate_srt(segments, f_tgt_srt, include_speaker=False)

        f_tgt_vtt = temp_dir / f"subtitles_{target_lang}.vtt"
        generate_vtt(segments, f_tgt_vtt, include_speaker=False)

        f_bilingual_srt = temp_dir / f"subtitles_bilingual_{source_lang}_{target_lang}.srt"
        generate_bilingual_srt(segments, f_bilingual_srt)

        f_src_srt = temp_dir / f"subtitles_{source_lang}_original.srt"
        generate_srt(segments, f_src_srt, include_speaker=False, use_source_text=True)

        f_txt = temp_dir / f"lecture_transcript_{target_lang}.txt"
        generate_transcript_txt(segments, f_txt, title=f"Lecture Dubbing Transcript ({source_lang} -> {target_lang})")

        f_readme = temp_dir / "README_SUBTITLES.txt"
        f_readme.write_text(
            f"Lecture Dubber - Subtitle Package\n"
            f"Target Language: {target_lang.upper()}\n"
            f"Source Language: {source_lang.upper()}\n\n"
            f"Included Files:\n"
            f"1. subtitles_{target_lang}.srt: Standard SubRip subtitles for VLC, MPV, YouTube, and media players.\n"
            f"2. subtitles_{target_lang}.vtt: WebVTT for HTML5 web players.\n"
            f"3. subtitles_bilingual_{source_lang}_{target_lang}.srt: Dual-language subtitle track.\n"
            f"4. subtitles_{source_lang}_original.srt: Original lecture source text transcript.\n"
            f"5. lecture_transcript_{target_lang}.txt: Clean text transcript with timestamps for study notes.\n\n"
            f"How to use:\n"
            f"- In VLC: Drag and drop any .srt file directly onto the playing video window.\n"
            f"- On YouTube: In Studio Subtitles tab, upload subtitles_{target_lang}.srt as a caption file.\n",
            encoding="utf-8"
        )

        with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for f in [f_tgt_srt, f_tgt_vtt, f_bilingual_srt, f_src_srt, f_txt, f_readme]:
                if f.is_file():
                    zipf.write(f, arcname=f.name)

        return output_zip_path
    finally:
        # Cleanup temporary files
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
