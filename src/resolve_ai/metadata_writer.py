"""Write AI analysis results back to DaVinci Resolve clip metadata."""

from __future__ import annotations

from typing import Any

from resolve_ai.models import ClipAnalysis

# Mapping of our analysis fields to Resolve's built-in metadata keys
FIELD_MAP = {
    "Description": "scene",
    "Tone": "lighting",
    "Keywords": "keywords",
    "Location": "location",
    "Environment": "time_of_day",
    "Shot Type": "shot_size",
    "Angle": "camera_angle",
    "Shot": "camera_movement",
    "Category": "composition",
    "Scene": "specialty",
}

# All Resolve metadata keys that this tool writes
AI_METADATA_KEYS = [
    "Description",
    "Tone",
    "Keywords",
    "Location",
    "Environment",
    "Shot Type",
    "Angle",
    "Shot",
    "Category",
    "Scene",
    "Comments",
    "Colorist",
]


def _build_resolve_metadata(analysis: ClipAnalysis) -> dict[str, str]:
    """Convert a ClipAnalysis to Resolve's built-in metadata fields."""
    meta: dict[str, str] = {}

    # Scene description fields
    meta["Description"] = analysis.scene.scene
    meta["Tone"] = analysis.scene.lighting
    meta["Keywords"] = analysis.scene.keywords
    meta["Location"] = analysis.scene.location
    meta["Environment"] = analysis.scene.time_of_day

    # Shot description fields
    meta["Shot Type"] = analysis.shot.shot_size
    meta["Angle"] = analysis.shot.camera_angle
    meta["Shot"] = analysis.shot.camera_movement
    meta["Category"] = analysis.shot.composition
    meta["Scene"] = analysis.shot.specialty

    # Pack palette + flags + system info into Comments
    parts: list[str] = []

    if analysis.scene.palette:
        parts.append(f"Palette: {analysis.scene.palette}")

    # Colorist flags - only include Yes flags
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
        parts.append(f"Flags: {', '.join(yes_flags)}")

    parts.append(f"AI: {analysis.model} | {analysis.analysis_date}")

    meta["Comments"] = " | ".join(parts)

    # Store model in Colorist field for easy filtering
    meta["Colorist"] = f"AI ({analysis.model})"

    return meta


def write_metadata(clip: Any, analysis: ClipAnalysis) -> bool:
    """Write analysis results to clip metadata.

    Uses MediaPoolItem.SetMetadata() with Resolve's built-in field names.
    Returns True if at least the core fields were written successfully.
    """
    media_pool_item = clip.GetMediaPoolItem()
    if not media_pool_item:
        return False

    meta = _build_resolve_metadata(analysis)

    success = True
    for key, value in meta.items():
        if not media_pool_item.SetMetadata(key, value):
            success = False

    return success


def clear_metadata(clip: Any) -> bool:
    """Remove all AI-generated metadata from a clip."""
    media_pool_item = clip.GetMediaPoolItem()
    if not media_pool_item:
        return False

    success = True
    for key in AI_METADATA_KEYS:
        if not media_pool_item.SetMetadata(key, ""):
            success = False

    return success


def read_metadata(clip: Any) -> dict[str, str]:
    """Read current AI metadata from a clip."""
    media_pool_item = clip.GetMediaPoolItem()
    if not media_pool_item:
        return {}

    result: dict[str, str] = {}
    all_meta = media_pool_item.GetMetadata()
    if not all_meta:
        return {}

    for key in AI_METADATA_KEYS:
        val = all_meta.get(key, "")
        if val:
            result[key] = val

    return result
