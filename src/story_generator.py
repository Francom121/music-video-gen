"""Generate scene-by-scene visual treatments for any story-based project.

Supports: anime, kids cartoon, short film, rap battle, ad, documentary, etc.
Also handles chat-based iteration — Claude patches specific scenes in response
to natural language instructions without regenerating the full treatment.
"""
import json
import anthropic

PROJECT_TYPES = [
    "Anime / Manga Series",
    "Kids Cartoon",
    "Short Film",
    "Rap Battle / Hip-Hop Visual",
    "Music Video (no audio)",
    "Brand / Ad Campaign",
    "Documentary",
    "Sci-Fi / Fantasy Epic",
    "Horror / Thriller",
    "Comedy Sketch",
    "Social Media Series",
    "Other / Custom",
]


def generate_scenes(brief, style_input, model="claude-sonnet-4-6"):
    """Generate a full scene breakdown with video + image prompts from a story brief."""
    client = anthropic.Anthropic()

    n_scenes = style_input.get("n_scenes", 12)
    project_type = style_input.get("project_type", "Short Film")
    tone = style_input.get("tone", "")
    character = style_input.get("character", "")
    reference = style_input.get("reference", "")
    video_tool = style_input.get("video_tool", "grok")
    style_ref = style_input.get("style_ref", "")
    location = style_input.get("location", "")

    prompt = _build_scene_prompt(
        brief=brief,
        project_type=project_type,
        tone=tone,
        character=character,
        reference=reference,
        video_tool=video_tool,
        n_scenes=n_scenes,
        style_ref=style_ref,
        location=location,
    )

    message = client.messages.create(
        model=model,
        max_tokens=16000,
        system=[{
            "type": "text",
            "text": (
                "You are an award-winning creative director and visual storyteller. "
                "You specialize in turning story concepts into vivid, production-ready "
                "scene breakdowns with AI-generation prompts. "
                "You output strict JSON only — no markdown fences, no preamble."
            ),
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{"role": "user", "content": prompt}],
    )

    text = "".join(b.text for b in message.content if hasattr(b, "text")).strip()
    return _parse_json(text)


def iterate_scenes(current_treatment, instruction, style_input, model="claude-sonnet-4-6"):
    """Apply a natural-language change instruction to the current treatment.

    Claude returns the full updated treatment JSON with only the affected
    scenes changed — everything else is preserved exactly.
    """
    client = anthropic.Anthropic()

    character = style_input.get("character", "")
    char_block = f"\nPROTAGONIST: {character}" if character else ""

    current_json = json.dumps(current_treatment, indent=2)

    prompt = f"""You are updating an existing visual treatment based on a creative direction note.

CURRENT TREATMENT:
{current_json}

CHANGE INSTRUCTION:
"{instruction}"
{char_block}

RULES:
- Apply the instruction faithfully — change only what's needed
- If the instruction targets specific scenes (e.g. "scene 3", "the climax"), only edit those
- If it's a global change (e.g. "make everything darker", "add a sidekick character"), update all affected scenes
- Keep all scene IDs, section names, and the overall structure identical
- Update "concept", "story_arc", or "continuity_notes" only if the change warrants it
- Return the COMPLETE updated treatment JSON — not just the changed parts

Return ONLY the JSON object, no fences, no explanation."""

    message = client.messages.create(
        model=model,
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}],
    )

    text = "".join(b.text for b in message.content if hasattr(b, "text")).strip()
    return _parse_json(text)


def reroll_scene(scene, treatment_context, style_input, model="claude-sonnet-4-6"):
    """Regenerate a single scene with fresh creative vision."""
    client = anthropic.Anthropic()

    char = style_input.get("character", "")
    char_block = f"\nPROTAGONIST: {char}" if char else ""

    prompt = f"""You are a creative director. Regenerate ONE scene with a completely fresh take.

OVERALL CONCEPT: {treatment_context.get("concept", "")}
PROJECT TYPE: {style_input.get("project_type", "")}
TONE: {style_input.get("tone", "")}
PALETTE: {treatment_context.get("visual_direction", {}).get("palette", "")}{char_block}

SCENE TO REROLL:
- ID: {scene["id"]}
- Act: {scene.get("act", "")}
- Story beat: {scene.get("story_beat", "")}
- Current description: {scene.get("description", "")}

Generate a completely different visual approach for this scene. Same story beat, fresh imagery.

Return ONLY a JSON object (no fences):
{{
  "id": "{scene["id"]}",
  "act": "{scene.get("act", "")}",
  "story_beat": "{scene.get("story_beat", "")}",
  "description": "short 5-10 word description",
  "prompt": "full video prompt with camera work, lighting, style modifiers, under 80 words",
  "image_prompt": "single cinematic still-frame for DALL-E/Midjourney, under 60 words, no camera movement verbs",
  "duration_sec": {scene.get("duration_sec", 8)}
}}"""

    message = client.messages.create(
        model=model,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in message.content if hasattr(b, "text")).strip()
    return _parse_json(text)


def _build_scene_prompt(*, brief, project_type, tone, character, reference, video_tool, n_scenes,
                        style_ref="", location=""):
    if character:
        char_block = f"""
CHARACTERS:
{character}
Describe each character specifically in every scene they appear in so AI tools render them consistently. If multiple characters appear together, describe all of them.
"""
    else:
        char_block = """
PROTAGONIST:
Invent a compelling protagonist that fits the brief. Describe them physically in every scene
they appear in so AI tools render them consistently across shots.
"""

    style_ref_block = f"\nSTYLE REFERENCE: {style_ref}\nIncorporate this visual style into all scene and prompt descriptions.\n" if style_ref else ""
    location_block = f"\nPRIMARY LOCATION / ENVIRONMENT: {location}\nUse this as the main world/setting where appropriate, referencing specific details in scene prompts.\n" if location else ""

    return f"""PROJECT BRIEF:
Type: {project_type}
Tone: {tone or "(infer from brief)"}
Reference / Inspiration: {reference or "(none)"}
Target video tool: {video_tool}
{char_block}{style_ref_block}{location_block}
STORY / IDEA:
{brief}

═══════════════════════════════════════════
STEP 1 — DESIGN THE NARRATIVE ARC
═══════════════════════════════════════════

Before writing scenes, build the complete story structure:
1. OPENING: World, character, and emotional state at the start
2. INCITING MOMENT: What disrupts the status quo?
3. RISING ACTION: How does tension/stakes escalate?
4. MIDPOINT SHIFT: A twist, revelation, or escalation that changes everything
5. CLIMAX: The peak confrontation or emotional moment
6. RESOLUTION: How does it end? What changed?

═══════════════════════════════════════════
STEP 2 — WRITE {n_scenes} SCENES
═══════════════════════════════════════════

Each scene must:
- Have a clear "story_beat" — what is happening emotionally/narratively RIGHT NOW
- Flow naturally from the previous scene
- Match the tone and visual style of the project type
- Include specific character descriptions when protagonist appears
- Use 2-3 recurring visual motifs throughout for consistency

Assign each scene to an act: "Act 1", "Act 2", "Act 3" (or "Cold Open", "Act 1"... for episodic)

PROMPT RULES:
- Video prompt: subject + action, camera movement, lighting, atmosphere, style modifiers. Under 80 words.
- Image prompt: single still frame for DALL-E/Midjourney — composition, lighting, pose. No camera verbs. Under 60 words.
- Style modifiers: "cinematic, anamorphic lens, shot on Arri Alexa, 35mm film grain" — adapt to project type
  (e.g. for anime: "anime cel animation, Studio Ghibli lighting, hand-drawn detail"
   for kids cartoon: "bright saturated colors, Pixar-style 3D, expressive character design"
   for horror: "desaturated, high contrast, practical lighting, grain")
- DO NOT name real people or licensed IP

OUTPUT FORMAT — strict JSON only, no fences:
{{
  "concept": "2-3 sentence pitch — protagonist, journey, emotional payoff",
  "project_type": "{project_type}",
  "story_arc": {{
    "opening": "world and emotional state at start",
    "inciting_moment": "what disrupts the status quo",
    "rising_action": "how tension escalates",
    "midpoint": "twist or revelation",
    "climax": "peak moment",
    "resolution": "how it ends, what changed"
  }},
  "visual_direction": {{
    "palette": "color palette and how it shifts with the emotional arc",
    "recurring_motifs": ["motif 1 + meaning", "motif 2 + meaning", "motif 3 + meaning"],
    "style_modifiers": ["modifier 1", "modifier 2", "modifier 3"]
  }},
  "continuity_notes": "How to keep protagonist and world visually consistent across scenes",
  "scenes": [
    {{
      "id": "01",
      "act": "Act 1",
      "story_beat": "one sentence — what is happening in the story right now",
      "description": "short 5-10 word scene description",
      "prompt": "full video prompt",
      "image_prompt": "still-frame prompt for DALL-E/Midjourney",
      "duration_sec": 8
    }}
  ]
}}

Return ONLY the JSON object."""


def _parse_json(text):
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
        try:
            with open("/tmp/story_generator_response.txt", "w") as f:
                f.write(text)
        except Exception:
            pass
        raise RuntimeError(f"Failed to parse JSON from Claude: {e}")
