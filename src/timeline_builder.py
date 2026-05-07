"""Build a clip-by-clip timeline mapping shots to time slots, snapped to bar grid."""


def build_timeline(sections, audio_data, treatment):
    """Generate ordered list of timeline entries with start/end times."""
    bar_length = audio_data["bar_length"]
    half_bar = bar_length / 2  # snap to half-bar grid (every 2 beats)

    # Group shots by section name (case-insensitive)
    shots_by_section = {}
    for shot in treatment["shots"]:
        key = shot["section"].upper().strip()
        shots_by_section.setdefault(key, []).append(shot)

    timeline = []
    for section in sections:
        section_key = section["name"].upper().strip()
        section_shots = shots_by_section.get(section_key, [])

        # Fuzzy match if exact key not found
        if not section_shots:
            for k, v in shots_by_section.items():
                if k in section_key or section_key in k:
                    section_shots = v
                    break

        if not section_shots:
            continue

        section_dur = section["end"] - section["start"]
        n = len(section_shots)
        slot_dur = section_dur / n

        cursor = section["start"]
        for i, shot in enumerate(section_shots):
            if i == n - 1:
                end = section["end"]
            else:
                target_end = cursor + slot_dur
                # Snap to nearest half-bar from section start
                bars_offset = round((target_end - section["start"]) / half_bar)
                end = section["start"] + bars_offset * half_bar
                end = min(max(end, cursor + 1.0), section["end"])

            timeline.append({
                "section": section["name"],
                "start": cursor,
                "end": end,
                "shot_id": shot["id"],
                "description": shot.get("description") or shot.get("prompt", "")[:80],
                "lyric_cue": shot.get("lyric_cue", ""),
            })
            cursor = end

    return timeline
