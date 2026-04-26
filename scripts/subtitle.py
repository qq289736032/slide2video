"""Subtitle generation: SRT and ASS formats with per-sentence timing."""

import os
import re
import subprocess
import sys

from config import DEFAULT_SUBTITLE_STYLE


def get_audio_duration(audio_path: str) -> float:
    """Get duration of an audio file using ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error getting duration of {audio_path}: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return float(result.stdout.strip())


def split_sentences(text: str) -> "list[str]":
    """Split text into sentences for subtitle display.

    Splits on Chinese sentence endings (。！？) and newlines.
    English periods only split when followed by space + uppercase,
    to avoid breaking things like 'skill.md'.
    """
    if not text.strip():
        return []
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    sentences = []
    for line in lines:
        parts = re.split(r"(?<=[。！？])\s*", line)
        expanded = []
        for part in parts:
            sub = re.split(r"(?<=[.!?])\s+(?=[A-Z])", part)
            expanded.extend(sub)
        sentences.extend([s.strip() for s in expanded if s.strip()])
    return sentences


def format_srt_time(seconds: float) -> str:
    """Format seconds to SRT timestamp: HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def format_ass_time(seconds: float) -> str:
    """Format seconds to ASS timestamp: H:MM:SS.cc"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def generate_srt(notes_data: dict, audio_files: "list[str]", output_path: str) -> "list[dict]":
    """Generate SRT subtitle file with per-sentence timing.

    Returns list of per-slide entries with sentence timing for ASS generation.
    """
    slides = notes_data.get("slides", [])
    entries = []
    current_time = 0.0
    srt_index = 1
    srt_lines = []

    for i, (slide_info, audio_path) in enumerate(zip(slides, audio_files)):
        duration = get_audio_duration(audio_path)
        notes = slide_info.get("notes", "").strip()
        sentences = split_sentences(notes)

        slide_entry = {
            "duration": duration,
            "text": notes,
            "sentences": [],
        }

        if sentences:
            total_chars = sum(len(s) for s in sentences)
            sent_time = current_time
            for sent in sentences:
                ratio = len(sent) / total_chars if total_chars > 0 else 1.0 / len(sentences)
                sent_dur = duration * ratio
                sent_end = sent_time + sent_dur

                slide_entry["sentences"].append({
                    "start": sent_time - current_time,
                    "end": sent_end - current_time,
                    "text": sent,
                })

                srt_lines.append(f"{srt_index}\n")
                srt_lines.append(f"{format_srt_time(sent_time)} --> {format_srt_time(sent_end)}\n")
                srt_lines.append(f"{sent}\n\n")
                srt_index += 1
                sent_time = sent_end

        entries.append(slide_entry)
        current_time += duration

    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(srt_lines)

    return entries


def create_ass_subtitle(sentences: "list[dict]", duration: float,
                        output_path: str, style: dict = None) -> None:
    """Create ASS subtitle file with per-sentence timing.

    Each sentence appears and disappears individually, like movie subtitles.
    """
    s = dict(DEFAULT_SUBTITLE_STYLE)
    if style:
        s.update(style)

    bold_flag = -1 if s["bold"] else 0
    ass_header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        "PlayResX: 1920\n"
        "PlayResY: 1080\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Default,{s['font']},{s['fontsize']},{s['primary_color']},"
        f"&H000000FF,{s['outline_color']},{s['back_color']},{bold_flag},"
        f"0,0,0,100,100,0,0,1,{s['outline']},{s['shadow']},2,40,40,"
        f"{s['margin_v']},1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, "
        "MarginV, Effect, Text\n"
    )

    dialogue_lines = []
    for sent in sentences:
        start = format_ass_time(sent["start"])
        end = format_ass_time(sent["end"])
        text = sent["text"].replace("\n", "\\N")
        dialogue_lines.append(
            f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n"
        )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ass_header)
        f.writelines(dialogue_lines)
