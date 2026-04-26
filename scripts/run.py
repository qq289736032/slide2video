#!/usr/bin/env python3
"""One-command pipeline: Markdown → Video.

Usage:
    python run.py <input.md> [-o output.mp4] [--voice ...] [--watermark ...]

Runs the full pipeline:
  1. parse_notes.py  → notes.json + clean markdown
  2. marp CLI         → slide images
  3. generate_audio.py → audio files
  4. compose_video.py  → final video + SRT
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def check_dependency(name: str, test_cmd: "list[str]", install_hint: str) -> bool:
    """Check if a command-line tool is available."""
    try:
        subprocess.run(test_cmd, capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        print(f"✗ {name} not found. Install: {install_hint}", file=sys.stderr)
        return False


def check_all_dependencies() -> bool:
    """Check all required dependencies are installed."""
    ok = True
    if not check_dependency("ffmpeg", ["ffmpeg", "-version"], "brew install ffmpeg"):
        ok = False
    if not check_dependency("marp", ["marp", "--version"], "npm install -g @marp-team/marp-cli"):
        ok = False
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        print("✗ edge-tts not found. Install: pip install edge-tts", file=sys.stderr)
        ok = False
    return ok


def run_step(step_name: str, cmd: "list[str]") -> None:
    """Run a pipeline step, exit on failure."""
    print(f"\n{'='*60}")
    print(f"  {step_name}")
    print(f"{'='*60}\n")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"\n✗ Failed at: {step_name}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Slide Video: Markdown → Video in one command.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py presentation.md
  python run.py presentation.md -o my_video.mp4
  python run.py presentation.md --voice zh-CN-XiaoxiaoNeural
  python run.py presentation.md --watermark "@MyChannel"
        """,
    )
    parser.add_argument("input", help="Path to Marp Markdown file")
    parser.add_argument(
        "-o", "--output", default=None,
        help="Output video path (default: <input_name>.mp4)",
    )
    parser.add_argument("--voice", default=None, help="Override TTS voice")
    parser.add_argument("--watermark", default=None, help="Watermark text")
    parser.add_argument("--wm-opacity", type=float, default=None, help="Watermark opacity")
    parser.add_argument("--wm-position", default=None, help="Watermark position")
    parser.add_argument("--resolution", default="1920:1080", help="Video resolution (default: 1920:1080)")
    parser.add_argument("--fps", type=int, default=30, help="Video frame rate (default: 30)")
    parser.add_argument("--no-subtitle", action="store_true", help="Disable burned-in subtitles")
    parser.add_argument("--theme", default=None, help="Marp theme name or CSS file path")
    parser.add_argument("--keep-temp", action="store_true", help="Keep intermediate files")
    args = parser.parse_args()

    # Check dependencies
    print("Checking dependencies...")
    if not check_all_dependencies():
        print("\n✗ Missing dependencies. Please install them first.", file=sys.stderr)
        sys.exit(1)
    print("✓ All dependencies found\n")

    # Resolve paths
    input_path = os.path.abspath(args.input)
    if not os.path.exists(input_path):
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    input_name = os.path.splitext(os.path.basename(input_path))[0]
    output_path = args.output or f"{input_name}.mp4"
    output_path = os.path.abspath(output_path)

    # Create temp working directory (or use input dir if --keep-temp)
    if args.keep_temp:
        work_dir = os.path.join(os.path.dirname(input_path), f"{input_name}_build")
        os.makedirs(work_dir, exist_ok=True)
        tmp_context = None
    else:
        tmp_context = tempfile.TemporaryDirectory()
        work_dir = tmp_context.name

    try:
        notes_json = os.path.join(work_dir, "notes.json")
        clean_md = os.path.join(work_dir, f"{input_name}_clean.md")
        slides_dir = os.path.join(work_dir, "slides")
        audio_dir = os.path.join(work_dir, "audio")
        os.makedirs(slides_dir, exist_ok=True)
        os.makedirs(audio_dir, exist_ok=True)

        # Step 1: Parse notes
        run_step("Step 1/4: Preparing (parse notes + clean markdown)", [
            sys.executable,
            os.path.join(SCRIPT_DIR, "prepare.py"),
            input_path,
            "-o", notes_json,
            "--clean-md", clean_md,
        ])

        # Step 2: Render slides with Marp
        marp_cmd = [
            "marp", "--images", "png",
            clean_md,
            "-o", os.path.join(slides_dir, "slide.png"),
        ]
        if args.theme:
            theme_path = args.theme
            # If just a name, look in skill's themes/ directory
            if not os.path.exists(theme_path) and not theme_path.endswith(".css"):
                theme_path = os.path.join(SCRIPT_DIR, "..", "themes", f"{args.theme}.css")
            if os.path.exists(theme_path):
                marp_cmd.extend(["--theme", os.path.abspath(theme_path)])
            else:
                print(f"Warning: Theme not found: {args.theme}", file=sys.stderr)
        run_step("Step 2/4: Rendering slides (Marp)", marp_cmd)

        # Step 3: Generate audio
        audio_cmd = [
            sys.executable,
            os.path.join(SCRIPT_DIR, "generate_audio.py"),
            notes_json,
            "-o", audio_dir,
        ]
        if args.voice:
            audio_cmd.extend(["--voice", args.voice])
        run_step("Step 3/4: Generating audio (edge-tts)", audio_cmd)

        # Step 4: Compose video
        compose_cmd = [
            sys.executable,
            os.path.join(SCRIPT_DIR, "compose_video.py"),
            slides_dir, audio_dir,
            "-o", output_path,
            "--notes", notes_json,
            "--resolution", args.resolution,
            "--fps", str(args.fps),
        ]
        if args.no_subtitle:
            compose_cmd.append("--no-subtitle")
        if args.watermark:
            compose_cmd.extend(["--watermark", args.watermark])
        if args.wm_opacity is not None:
            compose_cmd.extend(["--wm-opacity", str(args.wm_opacity)])
        if args.wm_position:
            compose_cmd.extend(["--wm-position", args.wm_position])
        run_step("Step 4/4: Composing video (ffmpeg)", compose_cmd)

        # Done
        srt_path = output_path.rsplit(".", 1)[0] + ".srt"
        print(f"\n{'='*60}")
        print(f"  ✓ Done!")
        print(f"{'='*60}")
        print(f"\n  Video: {output_path}")
        if os.path.exists(srt_path):
            print(f"  SRT:   {srt_path}")
        if args.keep_temp:
            print(f"  Build: {work_dir}")
        print()

    finally:
        if tmp_context:
            tmp_context.cleanup()


if __name__ == "__main__":
    main()
