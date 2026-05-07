"""Generate visual treatment + video/image prompts.

Prompts are narrative-first: the LLM builds a complete visual story arc
(protagonist, emotional journey, section callbacks, payoff) before writing
individual shot prompts. Supports Anthropic and OpenRouter providers.
"""
import json
from src import llm_client as _llm


def reroll_shot(shot, treatment_context, style_input, model="claude-sonnet-4-6"):
    """Regenerate one shot with fresh creative vision, preserving id/section/lyric_cue."""
    provider = style_input.get("provider", "anthropic")
    api_key = style_input.get("api_key", "")

    char = style_input.get("character", "")
    char_block = f"\nPROTAGONIST: {char}" if char else ""

    story_context = treatment_context.get("story_arc", {})
    arc_note = ""
    if story_context:
        arc_note = f"\nSTORY ARC: {story_context.get('opening','')}, {story_context.get('climax','')}, {story_context.get('resolution','')}"

    prompt = f"""You are a music video director. Regenerate ONE shot with a fresh take.

OVERALL CONCEPT: {treatment_context.get("concept", "")}
PALETTE: {treatment_context.get("visual_direction", {}).get("palette", "")}
STYLE MODIFIERS: {", ".join(treatment_context.get("visual_direction", {}).get("style_modifiers", []))}
VISUAL STYLE: {style_input.get("style", "")}{char_block}{arc_note}

SHOT TO REROLL:
- ID: {shot["id"]}
- Section: {shot["section"]}
- Story beat: {shot.get("story_beat", "")}
- Lyric cue: {shot.get("lyric_cue", "")}
- Current description: {shot.get("description", "")}

Generate a completely different take on this shot. Keep the same story beat and lyric context but use fresh imagery and camera work.

Return ONLY a JSON object (no fences):
{{
  "id": "{shot["id"]}",
  "section": "{shot["section"]}",
  "story_beat": "{shot.get("story_beat", "")}",
  "lyric_cue": "{shot.get("lyric_cue", "")}",
  "description": "short 5-10 word description",
  "prompt": "full video prompt with camera movement, lighting, style modifiers, under 80 words",
  "image_prompt": "single cinematic still-frame prompt for DALL-E/Midjourney, under 60 words, no camera movement verbs",
  "duration_target_sec": {shot.get("duration_target_sec", 7)}
}}"""

    text = _llm.chat(provider, api_key, model, "", prompt, max_tokens=1000)
    return _parse_json_response(text)


def generate_shots(sections, audio_data, style_input, model="claude-sonnet-4-6"):
    """Produce a complete narrative visual treatment as structured JSON."""
    provider = style_input.get("provider", "anthropic")
    api_key = style_input.get("api_key", "")

    duration = audio_data["duration"]
    n_shots_target = max(15, min(40, int(duration / 8)))

    section_summary = "\n".join([
        f"- [{s['name']}] {s['start']:.1f}s – {s['end']:.1f}s "
        f"({s['end'] - s['start']:.1f}s) | "
        f"Lines: {' / '.join(s['lines'][:4]) if s['lines'] else '(instrumental)'}"
        for s in sections
    ])

    section_names = [s["name"] for s in sections]

    prompt = _build_prompt(
        duration=duration,
        bpm=audio_data["tempo"],
        style=style_input.get("style", ""),
        mood=style_input.get("mood", ""),
        reference=style_input.get("reference", ""),
        video_tool=style_input.get("video_tool", "grok"),
        character=style_input.get("character", ""),
        style_ref=style_input.get("style_ref", ""),
        location=style_input.get("location", ""),
        section_summary=section_summary,
        section_names=section_names,
        n_shots_target=n_shots_target,
    )

    system = (
        "You are an award-winning music video director and visual storyteller. "
        "You think in narrative arcs — every video you create tells a complete emotional story "
        "that mirrors the song's lyrical journey. You output strict JSON only: no markdown "
        "fences, no preamble, no explanation before or after the JSON object."
    )
    response_text = _llm.chat(provider, api_key, model, system, prompt,
                              max_tokens=16000, cache_system=(provider == "anthropic"))
    return _parse_json_response(response_text)


def _build_prompt(*, duration, bpm, style, mood, reference, video_tool,
                  character, style_ref, location, section_summary, section_names, n_shots_target):

    if character:
        char_block = f"""
CHARACTERS / PROTAGONISTS:
{character}
Describe each character specifically in every shot they appear in so AI tools render them consistently (appearance, clothing, physicality). If multiple characters appear together, describe both.
"""
    else:
        char_block = """
PROTAGONIST:
Create a single consistent protagonist for this video. Describe them specifically in every shot they appear in (appearance, clothing, physicality) so the AI video tool can maintain visual consistency across shots.
"""

    style_ref_block = f"\nSTYLE REFERENCE: {style_ref}\nIncorporate this visual style into all shot prompts.\n" if style_ref else ""
    location_block = f"\nPRIMARY LOCATION / ENVIRONMENT: {location}\nUse this as the main world/setting where appropriate. Include specific details from this location in shot prompts.\n" if location else ""

    sections_list = ", ".join(f'"{n}"' for n in section_names)

    return f"""SONG INFO:
- Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)
- Tempo: {bpm:.1f} BPM
- Style: {style}
- Mood: {mood or '(infer from style and lyrics)'}
- Sound-alike reference: {reference or '(none)'}
- Target video tool: {video_tool}
{char_block}{style_ref_block}{location_block}
SECTIONS WITH LOCKED TIMESTAMPS:
{section_summary}

═══════════════════════════════════════════
STEP 1 — BUILD THE NARRATIVE ARC FIRST
═══════════════════════════════════════════

Before writing any shot, design the complete visual story this video tells:

1. OPENING STATE: Where is the protagonist emotionally and physically at the start?
2. INCITING MOMENT: What event or realization kicks the story into motion?
3. ESCALATION: How does tension/emotion build across the verses and pre-choruses?
4. CHORUS VISUAL IDENTITY: What is the single defining image or location for the chorus? (It must repeat and evolve each time)
5. BRIDGE TURNING POINT: What is the emotional pivot or revelation in the bridge?
6. CLIMAX: What is the peak visual/emotional moment of the whole video?
7. RESOLUTION: Where does the protagonist end up? How has something changed?

Each shot must serve this story. Lyrics are the narrator — visuals show what the lyrics mean emotionally, not literally.

═══════════════════════════════════════════
STEP 2 — SHOT REQUIREMENTS
═══════════════════════════════════════════

Generate approximately {n_shots_target} shots. Rules:

NARRATIVE RULES:
- Every shot has a "story_beat" — what is happening emotionally/narratively at this exact moment
- Shots must flow: each shot should feel like it follows from the previous one
- Chorus appearances (pass 1, 2, 3) should use the SAME location/setup but evolve emotionally (first: searching, second: believing, third: triumphant)
- The bridge must feel visually distinct — different location, lighting, or perspective
- End on a shot that feels like a resolution or earned emotional payoff

VISUAL CONSISTENCY:
- When the protagonist appears, always include their physical description so AI tools render them consistently
- Use 2-3 recurring visual motifs that appear throughout (e.g., a specific light source, a landscape feature, a symbolic object)
- Establish a consistent color palette that shifts subtly with emotional beats (e.g., cooler/desaturated in doubt, warm/golden in resolve)

PROMPT CRAFT:
- Video prompt: include subject + action, camera movement (dolly in / crane up / handheld / slow push), lighting, atmosphere, style modifiers. Under 80 words.
- Image prompt: single still frame for DALL-E/Midjourney — describe exact composition, lighting, subject pose, no camera movement verbs. Under 60 words.
- DO NOT name real people, licensed IP, or copyrighted characters
- Style modifiers to include: "cinematic, anamorphic lens, shot on Arri Alexa Mini, 35mm film grain, {style}"

SECTION MAPPING:
- Map every shot to one of these exact section names: {sections_list}
- For repeating sections use letter suffixes: "04", "04b", "04c"

═══════════════════════════════════════════
OUTPUT FORMAT — strict JSON only
═══════════════════════════════════════════

{{
  "concept": "2-3 sentence narrative pitch — who is this person, what journey do they go on, what does the audience feel at the end",
  "story_arc": {{
    "opening": "where protagonist starts emotionally and visually",
    "inciting_moment": "what kicks the story into motion",
    "escalation": "how tension builds through verses",
    "chorus_identity": "the defining image/location for every chorus",
    "bridge_turn": "the emotional pivot or revelation",
    "climax": "peak visual/emotional moment",
    "resolution": "where protagonist ends up, what changed"
  }},
  "visual_direction": {{
    "palette": "color palette and how it shifts with the emotional arc",
    "recurring_motifs": ["motif 1 + symbolic meaning", "motif 2 + meaning", "motif 3 + meaning", "motif 4 + meaning"],
    "style_modifiers": ["modifier 1", "modifier 2", "modifier 3"]
  }},
  "continuity_notes": "Specific instructions for maintaining protagonist consistency and visual continuity across shots",
  "shots": [
    {{
      "id": "01",
      "section": "INTRO",
      "story_beat": "one sentence — what is happening in the story right now",
      "lyric_cue": "first relevant lyric line or (instrumental)",
      "description": "short 5-10 word description for the timeline",
      "prompt": "full video prompt with character description, camera movement, lighting, style modifiers",
      "image_prompt": "single cinematic still-frame prompt for DALL-E/Midjourney",
      "duration_target_sec": 7
    }}
  ]
}}

Return ONLY the JSON object."""


def _parse_json_response(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text[:-3]
        text = text.lstrip("json").strip()

    first = text.find("{")
    last = text.rfind("}")
    if first >= 0 and last > first:
        text = text[first:last + 1]

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        debug_path = "/tmp/shot_generator_response.txt"
        try:
            with open(debug_path, "w") as f:
                f.write(text)
        except Exception:
            pass
        raise RuntimeError(
            f"Failed to parse JSON from Claude response: {e}\n"
            f"Raw response saved to {debug_path}"
        )
