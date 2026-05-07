#!/usr/bin/env python3
"""Music video timeline + prompts generator.

Usage:
    python generate.py song.wav lyrics.txt --style "anthemic pop, cinematic golden hour"

Requires:
    - ANTHROPIC_API_KEY in environment (or .env file)
    - openai-whisper installed locally (or OPENAI_API_KEY for API mode)
"""
import argparse
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.audio_analyzer import analyze_audio
from src.transcriber import transcribe
from src.lyric_aligner import align_lyrics
from src.shot_generator import generate_shots
from src.timeline_builder import build_timeline
from src.exporter import export_all


def main():
    parser = argparse.ArgumentParser(
        description="Generate music video shot list, prompts, and timeline from audio + lyrics",
    )
    parser.add_argument("audio", help="Path to audio file (wav/mp3/m4a)")
    parser.add_argument("lyrics", help="Path to lyrics file with [Section] markers")
    parser.add_argument("--style", required=True,
                        help="Style description, e.g. 'anthemic pop, cinematic, golden hour'")
    parser.add_argument("--mood", default="",
                        help="Mood description (optional)")
    parser.add_argument("--reference", default="",
                        help="Sound-alike reference, e.g. 'OneRepublic Counting Stars'")
    parser.add_argument("--output", default="./output",
                        help="Output directory (default: ./output)")
    parser.add_argument("--whisper", choices=["local", "api", "skip"], default="local",
                        help="Transcription method (default: local)")
    parser.add_argument("--whisper-model", default="medium",
                        help="Whisper model size for local mode (tiny/base/small/medium/large)")
    parser.add_argument("--video-tool", default="grok",
                        help="Target video gen tool (grok/runway/seedance) — affects prompt style")
    parser.add_argument("--shot-model", default="claude-sonnet-4-6",
                        help="Claude model for shot generation")
    args = parser.parse_args()

    audio_path = Path(args.audio)
    lyrics_path = Path(args.lyrics)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not audio_path.exists():
        sys.exit(f"ERROR: Audio file not found: {audio_path}")
    if not lyrics_path.exists():
        sys.exit(f"ERROR: Lyrics file not found: {lyrics_path}")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ERROR: ANTHROPIC_API_KEY not set. Add it to .env or export it.")

    print(f"\n{'='*60}\n MUSIC VIDEO GENERATOR\n{'='*60}\n")

    # 1. Audio analysis
    print(f"[1/5] Analyzing audio: {audio_path.name}")
    audio_data = analyze_audio(str(audio_path))
    print(f"      Duration: {audio_data['duration']:.2f}s")
    print(f"      Tempo: {audio_data['tempo']:.1f} BPM")
    print(f"      Bar length: {audio_data['bar_length']:.3f}s")
    print(f"      Detected boundaries: {len(audio_data['boundaries'])}")

    # 2. Transcription
    word_timestamps = None
    if args.whisper != "skip":
        print(f"\n[2/5] Transcribing audio (whisper={args.whisper})...")
        try:
            word_timestamps = transcribe(
                str(audio_path),
                method=args.whisper,
                model=args.whisper_model,
            )
            print(f"      Got {len(word_timestamps)} word timestamps")
        except Exception as e:
            print(f"      WARNING: Transcription failed ({e})")
            print(f"      Continuing with proportional alignment.")
    else:
        print(f"\n[2/5] Skipping transcription")

    # 3. Align lyrics to audio
    print(f"\n[3/5] Aligning lyrics to audio sections...")
    lyrics_text = lyrics_path.read_text()
    sections = align_lyrics(lyrics_text, audio_data, word_timestamps)
    print(f"      Aligned {len(sections)} sections:")
    for s in sections:
        print(f"        {s['name']:30s} {s['start']:6.2f} - {s['end']:6.2f}")

    # 4. Generate visual treatment + shot prompts
    print(f"\n[4/5] Generating visual treatment via {args.shot_model}...")
    style_input = {
        "style": args.style,
        "mood": args.mood,
        "reference": args.reference,
        "video_tool": args.video_tool,
    }
    treatment = generate_shots(sections, audio_data, style_input, model=args.shot_model)
    print(f"      Generated {len(treatment['shots'])} shots")

    # 5. Build timeline + export
    print(f"\n[5/5] Building timeline + exporting files...")
    timeline = build_timeline(sections, audio_data, treatment)
    export_all(treatment, timeline, audio_data, sections, output_dir)
    print(f"      Files written to: {output_dir.absolute()}")
    print(f"\n{'='*60}\n Done. Files: treatment.md  prompts.md  timeline.md  project.json\n{'='*60}\n")


if __name__ == "__main__":
    main()
