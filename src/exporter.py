"""Export treatment, prompts, and timeline as markdown files + raw project JSON."""
import json
from pathlib import Path


def fmt_time(t):
    m = int(t // 60)
    s = t % 60
    return f"{m}:{s:05.2f}"


def export_all(treatment, timeline, audio_data, sections, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    _write_treatment(treatment, audio_data, sections, output_dir / "treatment.md")
    _write_prompts(treatment, output_dir / "prompts.md")
    _write_timeline(timeline, audio_data, sections, output_dir / "timeline.md")
    _write_project_json({
        "treatment": treatment,
        "timeline": timeline,
        "audio_analysis": {
            "duration": audio_data["duration"],
            "tempo": audio_data["tempo"],
            "bar_length": audio_data["bar_length"],
            "boundaries": audio_data["boundaries"],
        },
        "sections": sections,
    }, output_dir / "project.json")


def _write_treatment(treatment, audio_data, sections, path):
    lines = [
        "# Music Video Treatment",
        "",
        f"**Duration:** {fmt_time(audio_data['duration'])} | "
        f"**BPM:** {audio_data['tempo']:.1f} | "
        f"**Bar:** {audio_data['bar_length']:.2f}s",
        "",
        "## Concept",
        "",
        treatment.get("concept", ""),
        "",
        "## Visual Direction",
        "",
        f"**Palette:** {treatment['visual_direction'].get('palette', '')}",
        "",
        "**Recurring motifs:**",
    ]
    for m in treatment["visual_direction"].get("recurring_motifs", []):
        lines.append(f"- {m}")
    lines.append("")
    lines.append("**Style modifiers (add to every prompt):**")
    for m in treatment["visual_direction"].get("style_modifiers", []):
        lines.append(f"- {m}")
    lines += [
        "",
        "## Continuity Notes",
        "",
        treatment.get("continuity_notes", ""),
        "",
        "## Section Map",
        "",
    ]
    for s in sections:
        lines.append(
            f"- **{s['name']}** — {fmt_time(s['start'])} to {fmt_time(s['end'])} "
            f"({s['end'] - s['start']:.1f}s)"
        )
    path.write_text("\n".join(lines) + "\n")


def _write_prompts(treatment, path):
    lines = [
        "# Shot Prompts",
        "",
        f"Total: {len(treatment['shots'])} unique shots",
        "",
    ]
    current_section = None
    for shot in treatment["shots"]:
        if shot["section"] != current_section:
            current_section = shot["section"]
            lines += ["", f"## {current_section}", ""]

        lines.append(f"### SHOT {shot['id']}")
        if shot.get("lyric_cue"):
            lines.append(f"*Cue: \"{shot['lyric_cue']}\"*")
        lines += ["", "```", shot["prompt"], "```", ""]
    path.write_text("\n".join(lines) + "\n")


def _write_timeline(timeline, audio_data, sections, path):
    lines = [
        "# Music Video Timeline",
        "",
        f"**Duration:** {fmt_time(audio_data['duration'])} | "
        f"**BPM:** {audio_data['tempo']:.1f} | "
        f"**Bar length:** {audio_data['bar_length']:.2f}s",
        "",
    ]

    by_section = {}
    for entry in timeline:
        by_section.setdefault(entry["section"], []).append(entry)

    for section in sections:
        entries = by_section.get(section["name"], [])
        if not entries:
            continue
        lines += [
            "",
            f"## {section['name']} — {fmt_time(section['start'])} to {fmt_time(section['end'])}",
            "",
            "```",
        ]
        for e in entries:
            cue = f"  ({e['lyric_cue']})" if e.get("lyric_cue") else ""
            lines.append(
                f"[{fmt_time(e['start'])} - {fmt_time(e['end'])}]  "
                f"SHOT {e['shot_id']}  {e['description']}{cue}"
            )
        lines.append("```")
    path.write_text("\n".join(lines) + "\n")


def _write_project_json(data, path):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
