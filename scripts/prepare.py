#!/usr/bin/env python3
"""Parse Marp Markdown file to extract per-slide ::: notes blocks.

Usage:
    python parse_notes.py <input.md> [-o notes.json]

Output: JSON file with slide notes and metadata.
"""

import argparse
import json
import re
import sys


def parse_frontmatter(content: str) -> "tuple[dict, str]":
    """Extract YAML frontmatter from markdown content.

    Returns (metadata_dict, remaining_content).
    """
    metadata = {}
    body = content

    # Match YAML frontmatter at the very start: ---\n...\n---
    fm_match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if fm_match:
        fm_text = fm_match.group(1)
        body = content[fm_match.end():]
        # Simple key: value parsing (no full YAML dependency)
        for line in fm_text.splitlines():
            line = line.strip()
            if ":" in line and not line.startswith("#"):
                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip()
                # Strip surrounding quotes
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                    value = value[1:-1]
                # Try to parse numeric values
                if re.match(r"^\d+(\.\d+)?$", value):
                    value = float(value) if "." in value else int(value)
                elif value.lower() in ("true", "false"):
                    value = value.lower() == "true"
                metadata[key] = value

    return metadata, body


def split_slides(body: str) -> "list[str]":
    """Split markdown body into slides by --- separator.

    Handles the Marp convention where --- on its own line separates slides.
    Skips --- inside fenced code blocks (``` or ~~~).
    """
    slides = []
    current = []
    in_code_block = False

    for line in body.split("\n"):
        # Track fenced code blocks
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_block = not in_code_block
            current.append(line)
            continue

        # Only split on --- outside code blocks
        if not in_code_block and re.match(r"^---\s*$", stripped):
            slide_text = "\n".join(current).strip()
            if slide_text:
                slides.append(slide_text)
            current = []
        else:
            current.append(line)

    # Don't forget the last slide
    slide_text = "\n".join(current).strip()
    if slide_text:
        slides.append(slide_text)

    return slides


def extract_notes(slide_content: str) -> str:
    """Extract ::: notes ... ::: block from a slide.

    Returns the notes text, or empty string if no notes block found.
    """
    match = re.search(
        r":::\s*notes\s*\n(.*?)\n\s*:::", slide_content, re.DOTALL
    )
    if match:
        return match.group(1).strip()
    return ""


def strip_notes(slide_content: str) -> str:
    """Remove ::: notes ... ::: block from a slide.

    Returns the slide content without the notes block.
    """
    cleaned = re.sub(
        r"\n*:::\s*notes\s*\n.*?\n\s*:::\s*", "", slide_content, flags=re.DOTALL
    )
    return cleaned.strip()


def generate_clean_markdown(frontmatter_text: str, slides: "list[str]") -> str:
    """Generate a clean Markdown file with notes blocks removed.

    This version can be fed directly to Marp CLI for rendering.
    """
    parts = []
    if frontmatter_text:
        parts.append(frontmatter_text)

    for i, slide in enumerate(slides):
        cleaned = strip_notes(slide)
        if i > 0:
            parts.append("---\n")
        parts.append(cleaned)

    return "\n\n".join(parts) + "\n"


def parse_markdown(filepath: str) -> "tuple[dict, str]":
    """Parse a Marp Markdown file and return structured notes data + clean markdown.

    Returns (notes_data_dict, clean_markdown_string).
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    metadata, body = parse_frontmatter(content)

    # Reconstruct frontmatter text for clean markdown
    fm_match = re.match(r"\A(---\s*\n.*?\n---\s*\n)", content, re.DOTALL)
    frontmatter_text = fm_match.group(1).strip() if fm_match else ""

    # Build output metadata
    voice = metadata.get("voice", "zh-CN-YunxiNeural")
    silence_duration = metadata.get("silence_duration", 3)

    slides = split_slides(body)

    notes_list = []
    for i, slide in enumerate(slides, start=1):
        notes_text = extract_notes(slide)
        notes_list.append({"slide": i, "notes": notes_text})

    # Generate clean markdown (no notes blocks)
    clean_md = generate_clean_markdown(frontmatter_text, slides)

    notes_data = {
        "metadata": {
            "voice": voice,
            "silence_duration": silence_duration,
            "total_slides": len(slides),
            "source": filepath,
        },
        "slides": notes_list,
    }

    # Pass through subtitle_* and watermark_* frontmatter keys to metadata
    for key, value in metadata.items():
        if key.startswith("subtitle_") or key.startswith("watermark_"):
            notes_data["metadata"][key] = value

    return notes_data, clean_md


def main():
    parser = argparse.ArgumentParser(
        description="Parse Marp Markdown and extract speaker notes."
    )
    parser.add_argument("input", help="Path to Marp Markdown file")
    parser.add_argument(
        "-o", "--output", default="notes.json",
        help="Output JSON file path (default: notes.json)",
    )
    parser.add_argument(
        "--clean-md", default=None,
        help="Output clean Markdown file (notes removed) for Marp rendering",
    )
    args = parser.parse_args()

    try:
        result, clean_md = parse_markdown(args.input)
    except FileNotFoundError:
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Write clean markdown (default: input filename with _clean suffix)
    if args.clean_md is None:
        base = args.input.rsplit(".", 1)[0]
        clean_path = base + "_clean.md"
    else:
        clean_path = args.clean_md

    with open(clean_path, "w", encoding="utf-8") as f:
        f.write(clean_md)

    print(f"Parsed {result['metadata']['total_slides']} slides → {args.output}")
    print(f"Clean Markdown (no notes) → {clean_path}")
    print(f"Voice: {result['metadata']['voice']}")


if __name__ == "__main__":
    main()
