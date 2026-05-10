#!/usr/bin/env python3
"""Generate audio files from notes.json using edge-tts.

Usage:
    python generate_audio.py <notes.json> [-o audio/] [--voice zh-CN-YunxiNeural]

Requires: pip install edge-tts
"""

import argparse
import asyncio
import json
import os
import re
import struct
import subprocess
import sys
import tempfile
import wave

# Maximum characters per TTS chunk. Texts longer than this are split at
# sentence boundaries to avoid edge-tts truncation or timeout.
MAX_TTS_CHARS = 2000


def split_text_chunks(text: str, max_chars: int = MAX_TTS_CHARS) -> "list[str]":
    """Split long text into chunks at sentence boundaries.

    Each chunk will be at most max_chars characters. Splits on Chinese
    sentence endings (。！？) and English sentence endings (.!?) followed
    by whitespace. Falls back to hard split if no sentence boundary found.
    """
    if len(text) <= max_chars:
        return [text]

    # Split into sentences first
    sentences = re.split(r"(?<=[。！？])\s*|(?<=[.!?])\s+", text)
    sentences = [s for s in sentences if s.strip()]

    chunks = []
    current = ""

    for sent in sentences:
        if not current:
            current = sent
        elif len(current) + len(sent) <= max_chars:
            current += sent
        else:
            if current:
                chunks.append(current)
            current = sent

    if current:
        chunks.append(current)

    # Handle edge case: a single sentence longer than max_chars → hard split
    final_chunks = []
    for chunk in chunks:
        if len(chunk) <= max_chars:
            final_chunks.append(chunk)
        else:
            # Hard split at max_chars boundaries
            for i in range(0, len(chunk), max_chars):
                final_chunks.append(chunk[i:i + max_chars])

    return final_chunks


async def generate_tts(text: str, voice: str, output_path: str) -> "list[dict]":
    """Generate TTS audio for given text using edge-tts with WordBoundary.

    Uses stream() with boundary='WordBoundary' to collect precise timing
    data for each word/character while generating audio.

    Returns:
        List of word boundary dicts, each containing:
        - offset_ms: start time in milliseconds
        - duration_ms: duration in milliseconds
        - text: the word/character text
    """
    import edge_tts

    communicate = edge_tts.Communicate(text, voice, boundary="WordBoundary")

    word_boundaries = []
    audio_data = bytearray()

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data.extend(chunk["data"])
        elif chunk["type"] == "WordBoundary":
            word_boundaries.append({
                "offset_ms": chunk["offset"] / 10000,  # 100ns → ms
                "duration_ms": chunk["duration"] / 10000,
                "text": chunk["text"],
            })

    # Write collected audio data to file
    with open(output_path, "wb") as f:
        f.write(audio_data)

    return word_boundaries


async def generate_tts_chunked(text: str, voice: str, output_path: str) -> "list[dict]":
    """Generate TTS audio, splitting long text into chunks if needed.

    For short texts (≤ MAX_TTS_CHARS), behaves identically to generate_tts.
    For long texts, splits at sentence boundaries, generates each chunk
    separately, then concatenates with ffmpeg (stream copy, no re-encode).

    Returns:
        Combined list of word boundary dicts with accumulated time offsets.
    """
    chunks = split_text_chunks(text)

    if len(chunks) == 1:
        return await generate_tts(chunks[0], voice, output_path)

    print(f"    (long text: {len(text)} chars → {len(chunks)} chunks)")

    all_boundaries = []

    with tempfile.TemporaryDirectory() as tmp_dir:
        chunk_paths = []
        time_offset_ms = 0.0

        for i, chunk in enumerate(chunks):
            chunk_path = os.path.join(tmp_dir, f"chunk_{i:03d}.mp3")
            boundaries = await generate_tts(chunk, voice, chunk_path)

            # Accumulate time offset from previous chunks
            for b in boundaries:
                all_boundaries.append({
                    "offset_ms": b["offset_ms"] + time_offset_ms,
                    "duration_ms": b["duration_ms"],
                    "text": b["text"],
                })

            # Get this chunk's audio duration for offset accumulation
            if boundaries:
                last = boundaries[-1]
                chunk_end_ms = last["offset_ms"] + last["duration_ms"]
                time_offset_ms += chunk_end_ms
            else:
                # Fallback: use ffprobe to get duration
                cmd = [
                    "ffprobe", "-v", "quiet",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    chunk_path,
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    time_offset_ms += float(result.stdout.strip()) * 1000

            chunk_paths.append(chunk_path)

        # Concatenate chunks with ffmpeg
        concat_file = os.path.join(tmp_dir, "concat.txt")
        with open(concat_file, "w") as f:
            for p in chunk_paths:
                f.write(f"file '{p}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error concatenating audio chunks: {result.stderr}", file=sys.stderr)
            sys.exit(1)

    return all_boundaries


def generate_silence(output_path: str, duration_sec: float) -> None:
    """Generate a silent WAV audio file.

    Output path should end with .wav. compose_video handles both mp3 and wav.
    """
    sample_rate = 24000
    num_channels = 1
    sample_width = 2  # 16-bit
    num_frames = int(sample_rate * duration_sec)

    with wave.open(output_path, "w") as wav_file:
        wav_file.setnchannels(num_channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        silence = struct.pack("<h", 0) * num_frames
        wav_file.writeframes(silence)


async def process_slides(notes_data: dict, output_dir: str, voice_override: "str | None") -> None:
    """Process all slides and generate audio files.

    Also collects WordBoundary timing data and writes it back to notes_data
    for precise subtitle alignment.
    """
    metadata = notes_data["metadata"]
    voice = voice_override or metadata.get("voice", "zh-CN-YunxiNeural")
    silence_duration = metadata.get("silence_duration", 3)
    slides = notes_data["slides"]

    os.makedirs(output_dir, exist_ok=True)

    print(f"Generating audio for {len(slides)} slides...")
    print(f"Voice: {voice}")
    print(f"Silence duration for empty notes: {silence_duration}s")
    print()

    for slide in slides:
        idx = slide["slide"]
        notes = slide["notes"]
        filename = f"audio_{idx:03d}.mp3"
        filepath = os.path.join(output_dir, filename)

        if notes:
            print(f"  Slide {idx}: Generating TTS → {filename}")
            boundaries = await generate_tts_chunked(notes, voice, filepath)
            slide["word_boundaries"] = boundaries
        else:
            wav_filename = f"audio_{idx:03d}.wav"
            wav_filepath = os.path.join(output_dir, wav_filename)
            print(f"  Slide {idx}: No notes → {wav_filename} ({silence_duration}s silence)")
            generate_silence(wav_filepath, silence_duration)
            slide["word_boundaries"] = []

    print(f"\nDone! Audio files saved to {output_dir}/")


def main():
    parser = argparse.ArgumentParser(
        description="Generate audio from notes.json using edge-tts."
    )
    parser.add_argument("input", help="Path to notes.json")
    parser.add_argument(
        "-o", "--output-dir", default="audio",
        help="Output directory for audio files (default: audio/)",
    )
    parser.add_argument(
        "--voice", default=None,
        help="Override TTS voice (e.g., zh-CN-XiaoxiaoNeural)",
    )
    args = parser.parse_args()

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            notes_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    asyncio.run(process_slides(notes_data, args.output_dir, args.voice))

    # Write back notes_data with word_boundaries
    with open(args.input, "w", encoding="utf-8") as f:
        json.dump(notes_data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
