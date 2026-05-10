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


def map_boundaries_to_sentences(
    sentences: "list[str]", word_boundaries: "list[dict]"
) -> "list[dict]":
    """Map word boundaries to sentences by text position matching.

    Assigns each word boundary to the sentence that contains it,
    then computes precise start/end times for each sentence.

    Args:
        sentences: List of sentence strings.
        word_boundaries: List of dicts with offset_ms, duration_ms, text.

    Returns:
        List of dicts with 'start_ms' and 'end_ms' for each sentence.
        Returns empty list if mapping fails.
    """
    if not sentences or not word_boundaries:
        return []

    # Build a flat text from sentences to find character positions
    # We need to map each boundary's text to a sentence
    sentence_boundaries = []  # [(start_char_pos, end_char_pos)] for each sentence

    # Reconstruct the full text from sentences and find where each sentence starts
    # Strategy: walk through word_boundaries sequentially, assign to sentences
    # by consuming characters from each sentence
    result = []
    boundary_idx = 0

    for sent in sentences:
        sent_start_ms = None
        sent_end_ms = None

        # Try to find boundaries that belong to this sentence
        # by matching boundary text against remaining sentence content
        remaining = sent
        while boundary_idx < len(word_boundaries) and remaining:
            b = word_boundaries[boundary_idx]
            b_text = b["text"]

            # Check if this boundary's text appears in the remaining sentence
            pos = remaining.find(b_text)
            if pos != -1:
                # This boundary belongs to this sentence
                if sent_start_ms is None:
                    sent_start_ms = b["offset_ms"]
                sent_end_ms = b["offset_ms"] + b["duration_ms"]
                # Consume the matched portion
                remaining = remaining[pos + len(b_text):]
                boundary_idx += 1
            elif pos == -1 and not remaining.strip():
                # Remaining is only whitespace/punctuation, move on
                break
            else:
                # Boundary text not found in remaining sentence
                # Could be punctuation was consumed or mismatch
                # Try skipping punctuation/whitespace in remaining
                stripped = remaining.lstrip("，。！？、；：""''（）【】《》…—·,.:;!? \t")
                if stripped != remaining:
                    remaining = stripped
                    continue
                # Still no match - this boundary might belong to next sentence
                break

        # If we found at least one boundary for this sentence
        if sent_start_ms is not None:
            result.append({"start_ms": sent_start_ms, "end_ms": sent_end_ms})
        else:
            # No boundary matched - will need fallback
            return []

    return result


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

    Uses WordBoundary data for precise timing when available,
    falls back to character-ratio estimation otherwise.

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
        word_boundaries = slide_info.get("word_boundaries", [])

        slide_entry = {
            "duration": duration,
            "text": notes,
            "sentences": [],
        }

        if sentences:
            # Try precise timing via WordBoundary data
            precise_timing = None
            if word_boundaries:
                precise_timing = map_boundaries_to_sentences(sentences, word_boundaries)

            if precise_timing:
                # Use precise WordBoundary timing
                for sent, timing in zip(sentences, precise_timing):
                    sent_start = timing["start_ms"] / 1000.0  # ms → seconds (relative to slide)
                    sent_end = timing["end_ms"] / 1000.0

                    slide_entry["sentences"].append({
                        "start": sent_start,
                        "end": sent_end,
                        "text": sent,
                    })

                    srt_lines.append(f"{srt_index}\n")
                    srt_lines.append(f"{format_srt_time(current_time + sent_start)} --> {format_srt_time(current_time + sent_end)}\n")
                    srt_lines.append(f"{sent}\n\n")
                    srt_index += 1
            else:
                # Fallback: character-ratio estimation
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
