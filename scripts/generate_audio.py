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
import struct
import sys
import wave


async def generate_tts(text: str, voice: str, output_path: str) -> None:
    """Generate TTS audio for given text using edge-tts."""
    import edge_tts

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


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
    """Process all slides and generate audio files."""
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
            await generate_tts(notes, voice, filepath)
        else:
            wav_filename = f"audio_{idx:03d}.wav"
            wav_filepath = os.path.join(output_dir, wav_filename)
            print(f"  Slide {idx}: No notes → {wav_filename} ({silence_duration}s silence)")
            generate_silence(wav_filepath, silence_duration)

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


if __name__ == "__main__":
    main()
