#!/usr/bin/env python3
"""Compose slide images and audio files into a video using ffmpeg.

Usage:
    python compose_video.py <slides_dir> <audio_dir> [-o output.mp4] [--notes notes.json]

Requires: ffmpeg installed (brew install ffmpeg)
"""

import argparse
import glob
import json
import os
import subprocess
import sys
import tempfile

# Allow imports from the same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    DEFAULT_WATERMARK,
    WATERMARK_POSITIONS,
    SUBTITLE_FRONTMATTER_KEYS,
    WATERMARK_FRONTMATTER_KEYS,
)
from subtitle import create_ass_subtitle, generate_srt, get_audio_duration


def get_sorted_files(directory: str, extensions: "list[str]") -> "list[str]":
    """Get sorted list of files matching given extensions.

    Deduplicates by base name (e.g. audio_001.mp3 and audio_001.wav → keep first).
    """
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(directory, f"*.{ext}")))
    files.sort(key=lambda f: os.path.basename(f))

    seen = {}
    unique = []
    for f in files:
        base = os.path.splitext(os.path.basename(f))[0]
        if base not in seen:
            seen[base] = True
            unique.append(f)
    return unique


def build_watermark_filter(watermark: dict) -> str:
    """Build ffmpeg drawtext filter string for watermark."""
    wm = dict(DEFAULT_WATERMARK)
    wm.update(watermark)

    if not wm["text"]:
        return ""

    pos = WATERMARK_POSITIONS.get(wm["position"], WATERMARK_POSITIONS["top_right"])
    x_expr = pos[0].format(m=wm["margin"])
    y_expr = pos[1].format(m=wm["margin"])
    escaped_text = wm["text"].replace("'", "\\'").replace(":", "\\:")
    escaped_font = wm["font"].replace("'", "\\'")

    return (
        f"drawtext=text='{escaped_text}'"
        f":fontfile='':font='{escaped_font}'"
        f":fontsize={wm['fontsize']}"
        f":fontcolor={wm['color']}@{wm['opacity']}"
        f":x={x_expr}:y={y_expr}"
    )


def create_slide_segment(
    image_path: str, audio_path: str, output_path: str,
    resolution: str = "1920:1080", fps: int = 30,
    subtitle_sentences: "list[dict]" = None,
    subtitle_style: dict = None,
    watermark: dict = None,
) -> None:
    """Create a video segment from one slide image + audio."""
    duration = get_audio_duration(audio_path)

    vf_parts = [
        f"scale={resolution}:force_original_aspect_ratio=decrease",
        f"pad={resolution}:(ow-iw)/2:(oh-ih)/2",
    ]

    # Watermark (rendered below subtitles)
    if watermark:
        wm_filter = build_watermark_filter(watermark)
        if wm_filter:
            vf_parts.append(wm_filter)

    # Subtitles (rendered on top)
    ass_path = None
    if subtitle_sentences:
        ass_path = output_path + ".ass"
        create_ass_subtitle(subtitle_sentences, duration, ass_path, style=subtitle_style)
        escaped_ass = ass_path.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
        vf_parts.append(f"ass='{escaped_ass}'")

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", image_path,
        "-i", audio_path,
        "-c:v", "libx264", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-vf", ",".join(vf_parts),
        "-r", str(fps),
        "-t", str(duration),
        "-shortest",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if ass_path and os.path.exists(ass_path):
        os.unlink(ass_path)

    if result.returncode != 0:
        print(f"Error creating segment: {result.stderr}", file=sys.stderr)
        sys.exit(1)


def concatenate_segments(segment_paths: "list[str]", output_path: str) -> None:
    """Concatenate video segments into final video."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for seg in segment_paths:
            f.write(f"file '{os.path.abspath(seg)}'\n")
        concat_file = f.name

    try:
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error concatenating: {result.stderr}", file=sys.stderr)
            sys.exit(1)
    finally:
        os.unlink(concat_file)


def build_style_from_metadata(meta: dict, cli_args: dict, key_map: dict) -> dict:
    """Build a style dict from metadata + CLI overrides using a key mapping."""
    style = {}
    for md_key, style_key in key_map.items():
        if md_key in meta:
            style[style_key] = meta[md_key]
    # CLI overrides
    for cli_key, style_key in cli_args.items():
        if cli_key is not None:
            style[style_key] = cli_key
    return style


def main():
    parser = argparse.ArgumentParser(
        description="Compose slide images + audio into video."
    )
    parser.add_argument("slides_dir", help="Directory containing slide PNG images")
    parser.add_argument("audio_dir", help="Directory containing audio files")
    parser.add_argument("-o", "--output", default="output.mp4")
    parser.add_argument("--resolution", default="1920:1080")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--notes", default=None, help="Path to notes.json")
    parser.add_argument("--no-subtitle", action="store_true")
    # Subtitle overrides
    parser.add_argument("--sub-font", default=None)
    parser.add_argument("--sub-fontsize", type=int, default=None)
    parser.add_argument("--sub-color", default=None)
    parser.add_argument("--sub-outline-color", default=None)
    parser.add_argument("--sub-outline", type=int, default=None)
    parser.add_argument("--sub-margin-v", type=int, default=None)
    # Watermark overrides
    parser.add_argument("--watermark", default=None)
    parser.add_argument("--wm-opacity", type=float, default=None)
    parser.add_argument("--wm-position", default=None,
                        choices=["top_right", "top_left", "bottom_right", "bottom_left"])
    parser.add_argument("--wm-fontsize", type=int, default=None)
    parser.add_argument("--wm-color", default=None)
    args = parser.parse_args()

    # Collect files
    slides = get_sorted_files(args.slides_dir, ["png", "jpg", "jpeg"])
    audio_files = get_sorted_files(args.audio_dir, ["mp3", "wav"])

    if not slides:
        print(f"Error: No images in {args.slides_dir}", file=sys.stderr)
        sys.exit(1)
    if not audio_files:
        print(f"Error: No audio in {args.audio_dir}", file=sys.stderr)
        sys.exit(1)
    if len(slides) != len(audio_files):
        print(f"Error: {len(slides)} slides != {len(audio_files)} audio files", file=sys.stderr)
        sys.exit(1)

    print(f"Composing {len(slides)} slides into video...")
    print(f"Resolution: {args.resolution}, FPS: {args.fps}")

    # Load notes and build configs
    subtitle_data = [None] * len(slides)
    subtitle_style = {}
    watermark_cfg = {}
    notes_data = None

    if args.notes:
        try:
            with open(args.notes, "r", encoding="utf-8") as f:
                notes_data = json.load(f)
            meta = notes_data.get("metadata", {})

            # Subtitle style: metadata → CLI
            subtitle_style = build_style_from_metadata(
                meta, {
                    args.sub_font: "font",
                    args.sub_fontsize: "fontsize",
                    args.sub_color: "primary_color",
                    args.sub_outline_color: "outline_color",
                    args.sub_outline: "outline",
                    args.sub_margin_v: "margin_v",
                }, SUBTITLE_FRONTMATTER_KEYS,
            )

            # Watermark: metadata → CLI
            watermark_cfg = build_style_from_metadata(
                meta, {
                    args.watermark: "text",
                    args.wm_opacity: "opacity",
                    args.wm_position: "position",
                    args.wm_fontsize: "fontsize",
                    args.wm_color: "color",
                }, WATERMARK_FRONTMATTER_KEYS,
            )

            # Generate SRT
            srt_path = args.output.rsplit(".", 1)[0] + ".srt"
            entries = generate_srt(notes_data, audio_files, srt_path)
            print(f"Subtitles: {srt_path}")

            if not args.no_subtitle:
                subtitle_data = [e.get("sentences", []) for e in entries]
                print("Burned-in subtitles: per-sentence")
            else:
                print("Burned-in subtitles: disabled (SRT only)")

        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load notes ({e})", file=sys.stderr)

    if watermark_cfg.get("text"):
        print(f"Watermark: \"{watermark_cfg['text']}\"")

    print()

    # Compose segments
    with tempfile.TemporaryDirectory() as tmp_dir:
        segments = []
        for i, (slide, audio) in enumerate(zip(slides, audio_files), start=1):
            seg_path = os.path.join(tmp_dir, f"segment_{i:03d}.mp4")
            print(f"  Segment {i}/{len(slides)}: {os.path.basename(slide)} + {os.path.basename(audio)}")
            create_slide_segment(
                slide, audio, seg_path, args.resolution, args.fps,
                subtitle_sentences=subtitle_data[i - 1],
                subtitle_style=subtitle_style,
                watermark=watermark_cfg,
            )
            segments.append(seg_path)

        print(f"\nConcatenating {len(segments)} segments...")
        concatenate_segments(segments, args.output)

    print(f"Done! Video saved to {args.output}")


if __name__ == "__main__":
    main()
