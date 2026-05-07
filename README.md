# Music Video Generator

A CLI tool that takes a song + lyrics and produces a complete AI-music-video plan: visual treatment, shot-by-shot prompts ready for Grok/Runway/Seedance, and a frame-accurate timeline locked to your audio's actual BPM and section structure.

## What it does

1. **Analyzes audio** with librosa — detects tempo, beat grid, energy contour, and section boundaries
2. **Transcribes lyrics** with Whisper (local or OpenAI API) — gets word-level timestamps for precise lyric sync
3. **Aligns sections** — matches your `[Section]` markers to the actual song structure
4. **Generates visual treatment** with Claude — creates concept, palette, motifs, and ~25-35 unique shot prompts
5. **Builds timeline** — slots each shot into time-coded chunks aligned to bar boundaries
6. **Exports**: `treatment.md`, `prompts.md`, `timeline.md`, `project.json`

## Setup

```bash
# 1. Clone or unzip into a project folder, cd into it
cd music-video-gen

# 2. Create a venv (recommended on macOS to avoid system Python issues)
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install ffmpeg (needed by whisper for audio decoding)
brew install ffmpeg   # macOS
# or:  apt install ffmpeg   # Linux

# 5. Set up API keys
cp .env.example .env
# Edit .env with your keys:
#   ANTHROPIC_API_KEY (required)
#   OPENAI_API_KEY    (only needed for --whisper api)
```

## Usage

```bash
python generate.py \
  /path/to/song.wav \
  /path/to/lyrics.txt \
  --style "anthemic pop, cinematic golden hour, OneRepublic energy" \
  --reference "OneRepublic Counting Stars" \
  --mood "uplifting, awe-filled, triumphant" \
  --output ./output/watch-the-sky
```

Then check `./output/watch-the-sky/` for:
- `treatment.md` — concept and visual direction
- `prompts.md` — every shot prompt, ready to copy into Grok
- `timeline.md` — drag-and-drop timeline with timestamps
- `project.json` — raw structured data for further automation

### Options

| Flag | Default | Description |
|---|---|---|
| `--style` | (required) | Style description for shot generation |
| `--mood` | "" | Optional mood description |
| `--reference` | "" | Sound-alike artist/song |
| `--output` | `./output` | Output folder |
| `--whisper` | `local` | Transcription mode: `local` / `api` / `skip` |
| `--whisper-model` | `medium` | Local Whisper size: `tiny` / `base` / `small` / `medium` / `large` |
| `--video-tool` | `grok` | Target video gen tool — affects prompt phrasing |
| `--shot-model` | `claude-sonnet-4-6` | Claude model for shot generation |

### Lyrics format

Use `[Section Name]` markers between sections. Each line of lyric content goes on its own line.

```
[Intro]
Oh-oh-oh
Watch the sky

[Verse 1]
First line of verse one
Second line of verse one
...
```

Section names are arbitrary — `[Bridge]`, `[Pre-Chorus]`, `[Drop]`, whatever. The tool maps them to detected audio sections by line count and energy.

## How it handles song structure

- **With Whisper word timestamps**: each section starts at the exact moment its first lyric word is sung (0.1s precision)
- **Without Whisper** (`--whisper skip`): sections are distributed proportionally by line count, snapped to detected energy/spectral boundaries (~2s precision)

Either way, all clip cuts within a section snap to the half-bar grid so they land on the beat.

## Iterating

If the generated shots aren't right:
1. Edit `prompts.md` directly
2. Or rerun `generate.py` — Claude generates fresh treatment each time
3. Or tweak the prompt template in `src/shot_generator.py`

## Cost estimate

Per 4-minute song:
- Whisper local: free, takes 5-15 min on CPU, ~30 sec on GPU
- Whisper API: ~$0.025
- Claude Sonnet shot gen: ~$0.05-0.15
- Claude Opus shot gen (`--shot-model claude-opus-4-7`): ~$0.50-1.00

Total per song: under $1 with Opus, under $0.20 with Sonnet.

## Roadmap ideas

- Streamlit UI for drag-and-drop song upload
- Auto-call Grok/Runway/Seedance API to actually generate the videos
- Image-to-video continuity (generate one keyframe, use it for all shots of the same character)
- Batch mode: drop a folder of songs, get a folder of timelines
- DAW export: write a `.fcpxml` or `.edl` so the timeline imports straight into Final Cut / Resolve
