"""Write AI analysis results to DaVinci Resolve timeline clips.

Uses TimelineItem.SetName() and TimelineItem.AddMarker() which are per-clip,
unlike MediaPoolItem.SetMetadata() which is shared across all clips from the
same source (breaks with scene-detected timelines).
"""

from __future__ import annotations

import json
from typing import Any

from resolve_ai.models import ClipAnalysis

# Marker color for AI analysis markers
MARKER_COLOR = "Cream"
MARKER_NAME_PREFIX = "AI"


def _build_clip_name(analysis: ClipAnalysis) -> str:
    """Build a short descriptive clip name from the analysis."""
    parts: list[str] = []
    if analysis.shot.shot_size:
        parts.append(analysis.shot.shot_size)
    if analysis.shot.composition:
        parts.append(analysis.shot.composition)
    if analysis.shot.camera_angle:
        parts.append(analysis.shot.camera_angle)
    return " | ".join(parts) if parts else analysis.clip_name


def _build_marker_note(analysis: ClipAnalysis) -> str:
    """Build the marker note with full analysis details."""
    lines: list[str] = []

    if analysis.scene.scene:
        lines.append(analysis.scene.scene)

    detail_parts: list[str] = []
    if analysis.scene.lighting:
        detail_parts.append(f"Lighting: {analysis.scene.lighting}")
    if analysis.scene.palette:
        detail_parts.append(f"Palette: {analysis.scene.palette}")
    if analysis.scene.location:
        detail_parts.append(f"Location: {analysis.scene.location}")
    if analysis.scene.time_of_day:
        detail_parts.append(f"Time: {analysis.scene.time_of_day}")
    if detail_parts:
        lines.append(" | ".join(detail_parts))

    shot_parts: list[str] = []
    if analysis.shot.shot_size:
        shot_parts.append(f"Size: {analysis.shot.shot_size}")
    if analysis.shot.camera_angle:
        shot_parts.append(f"Angle: {analysis.shot.camera_angle}")
    if analysis.shot.camera_movement:
        shot_parts.append(f"Move: {analysis.shot.camera_movement}")
    if analysis.shot.composition:
        shot_parts.append(f"Comp: {analysis.shot.composition}")
    if analysis.shot.specialty and analysis.shot.specialty.lower() != "none":
        shot_parts.append(f"Style: {analysis.shot.specialty}")
    if shot_parts:
        lines.append(" | ".join(shot_parts))

    # Colorist flags - only Yes flags
    flag_map = {
        "Animation Cut": analysis.flags.animation_cut,
        "Backs": analysis.flags.backs,
        "Non-Fade Transitions": analysis.flags.non_fade_transitions,
        "Flashes": analysis.flags.flashes,
        "Quick Cuts": analysis.flags.quick_cuts,
        "1-Shots Long": analysis.flags.one_shots_long,
        "Bright Scene": analysis.flags.bright_scene,
        "Dark Scene": analysis.flags.dark_scene,
        "Mixed Textures": analysis.flags.mixed_textures,
        "Yellows": analysis.flags.yellows,
        "Landscape": analysis.flags.landscape,
        "Large Flat Surface": analysis.flags.large_flat_surface,
        "Face CU": analysis.flags.face_cu,
        "No Face Then Face": analysis.flags.no_face_then_face,
        "Skin Tones": analysis.flags.skin_tones,
        "Moving Trees": analysis.flags.moving_trees,
        "Water": analysis.flags.water,
    }
    yes_flags = [k for k, v in flag_map.items() if v]
    if yes_flags:
        lines.append(f"Flags: {', '.join(yes_flags)}")

    if analysis.scene.keywords:
        lines.append(f"Keywords: {analysis.scene.keywords}")

    return "\n".join(lines)


def _build_custom_data(analysis: ClipAnalysis) -> str:
    """Build JSON custom data for programmatic access."""
    return json.dumps(analysis.to_metadata_dict(), separators=(",", ":"))


def write_metadata(clip: Any, analysis: ClipAnalysis) -> bool:
    """Write analysis to a timeline clip using SetName and AddMarker.

    These methods are per-TimelineItem, so each clip gets its own data
    even when multiple clips share the same source MediaPoolItem.
    """
    # Set clip name to short descriptor
    name = _build_clip_name(analysis)
    clip.SetName(name)

    # Add marker at frame 0 (relative to clip start) with full details
    note = _build_marker_note(analysis)
    custom_data = _build_custom_data(analysis)
    marker_name = f"{MARKER_NAME_PREFIX}: {analysis.shot.shot_size or 'Analysis'}"

    result = clip.AddMarker(
        0,  # frameId: first frame of clip
        MARKER_COLOR,  # color
        marker_name,  # name
        note,  # note
        1,  # duration (1 frame)
        custom_data,  # customData (JSON)
    )

    return bool(result)


def clear_metadata(clip: Any) -> bool:
    """Remove all AI markers and reset clip name."""
    # Delete all markers with our color
    result = clip.DeleteMarkersByColor(MARKER_COLOR)

    # Reset clip name to empty (Resolve will show source name)
    clip.SetName("")

    return bool(result)


def read_metadata(clip: Any) -> dict[str, str]:
    """Read AI analysis from clip markers."""
    markers = clip.GetMarkers()
    if not markers:
        return {}

    # Find first marker with our color
    for _frame_id, marker in markers.items():
        if marker.get("color") == MARKER_COLOR and marker.get("name", "").startswith(
            MARKER_NAME_PREFIX
        ):
            custom = marker.get("customData", "")
            if custom:
                return json.loads(custom)  # type: ignore[no-any-return]

    return {}
