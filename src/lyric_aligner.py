"""Align lyric sections (from [Section] markers) to detected audio boundaries."""
import re


SECTION_PATTERN = re.compile(r'^\s*\[([^\]]+)\]\s*$')


def parse_lyrics(text):
    """Parse lyrics with [Section] markers into ordered list of {name, lines}."""
    sections = []
    current = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        match = SECTION_PATTERN.match(line)
        if match:
            if current:
                sections.append(current)
            current = {"name": match.group(1).strip(), "lines": []}
        else:
            if current is None:
                current = {"name": "INTRO", "lines": []}
            current["lines"].append(line)
    if current:
        sections.append(current)
    return sections


def align_lyrics(lyrics_text, audio_data, word_timestamps=None):
    """Map each lyric section to a {start, end} timestamp.

    If Whisper word timestamps are available, use them for precise alignment.
    Otherwise, fall back to proportional distribution snapped to detected boundaries.
    """
    parsed = parse_lyrics(lyrics_text)
    if not parsed:
        raise ValueError(
            "No sections found in lyrics. Use [Intro], [Verse 1], [Chorus] etc."
        )

    if word_timestamps:
        return _align_with_words(parsed, audio_data, word_timestamps)
    return _align_by_boundaries(parsed, audio_data)


def _align_by_boundaries(parsed_sections, audio_data):
    """Distribute sections proportionally by line count, snap to detected boundaries."""
    duration = audio_data["duration"]
    boundaries = sorted(audio_data["boundaries"])
    if not boundaries or boundaries[0] > 0.5:
        boundaries = [0.0] + boundaries
    if boundaries[-1] < duration - 0.5:
        boundaries = boundaries + [duration]

    # Weight sections by line count (sections with more lyrics take more time)
    weights = [max(len(s["lines"]), 1) for s in parsed_sections]
    total_weight = sum(weights)

    aligned = []
    cursor = 0.0
    for section, weight in zip(parsed_sections, weights):
        target_duration = (weight / total_weight) * duration
        target_end = cursor + target_duration
        # Snap to nearest boundary within 3 seconds
        snapped_end = target_end
        for b in boundaries:
            if b <= cursor + 0.5:
                continue
            if abs(b - target_end) < 3.0:
                snapped_end = b
                break
        snapped_end = min(snapped_end, duration)
        aligned.append({
            "name": section["name"],
            "lines": section["lines"],
            "start": cursor,
            "end": snapped_end,
        })
        cursor = snapped_end

    if aligned:
        aligned[-1]["end"] = duration
    return aligned


def _align_with_words(parsed_sections, audio_data, words):
    """Find each section's start by matching its first lyric line to whisper words."""
    aligned = []
    word_idx = 0

    for section in parsed_sections:
        start_time = None
        if section["lines"]:
            first_line = section["lines"][0]
            start_time = _find_line_start(first_line, words, word_idx)
            if start_time is not None:
                # Advance word_idx past this match
                word_idx = _advance_past_time(words, start_time, word_idx)

        if start_time is None:
            start_time = aligned[-1]["end"] if aligned else 0.0

        if aligned:
            aligned[-1]["end"] = start_time

        aligned.append({
            "name": section["name"],
            "lines": section["lines"],
            "start": start_time,
            "end": audio_data["duration"],  # placeholder, fixed by next iteration
        })

    if aligned:
        aligned[-1]["end"] = audio_data["duration"]
    return aligned


def _find_line_start(line, words, start_idx):
    """Find the timestamp where this lyric line begins in the word stream."""
    line_words = [_normalize(w) for w in line.split() if _normalize(w)]
    if not line_words:
        return None

    target = line_words[0]
    # Try exact match first
    for j in range(start_idx, len(words)):
        norm = _normalize(words[j]["word"])
        if norm == target or norm.startswith(target):
            return words[j]["start"]
    # Fuzzy fallback: substring match
    for j in range(start_idx, len(words)):
        norm = _normalize(words[j]["word"])
        if target in norm or norm in target:
            return words[j]["start"]
    return None


def _advance_past_time(words, t, start_idx):
    for j in range(start_idx, len(words)):
        if words[j]["start"] >= t:
            return j + 1
    return len(words)


def _normalize(s):
    return ''.join(c.lower() for c in s if c.isalnum())
