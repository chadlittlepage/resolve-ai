"""Write AI analysis results back to DaVinci Resolve clip metadata."""

from __future__ import annotations

from typing import Any

from resolve_ai.models import ClipAnalysis

# All metadata keys that this tool writes
AI_METADATA_KEYS = [
    "Scene Description",
    "Lighting",
    "Scene Keywords",
    "Color Palette",
    "Location",
    "Time of Day",
    "Shot Size",
    "Camera Angle",
    "Camera Movement",
    "Composition",
    "Specialty",
    "Animation Cut",
    "Backs",
    "Non-Fade Transitions",
    "Flashes",
    "Quick Cuts",
    "1-Shots Long",
    "Bright Scene",
    "Dark Scene",
    "Mixed Textures",
    "Yellows",
    "Landscape",
    "Large Flat Surface",
    "Face CU",
    "No Face Then Face",
    "Skin Tones",
    "Moving Trees",
    "Water",
    "AI Analysis Date",
    "AI Model",
]


def write_metadata(clip: Any, analysis: ClipAnalysis) -> bool:
    """Write analysis results to clip metadata.

    Uses MediaPoolItem.SetMetadata() for each field.
    Returns True if all fields were written successfully.
    """
    media_pool_item = clip.GetMediaPoolItem()
    if not media_pool_item:
        return False

    meta = analysis.to_metadata_dict()
    return bool(media_pool_item.SetMetadata(meta))


def clear_metadata(clip: Any) -> bool:
    """Remove all AI-generated metadata from a clip.

    Sets each AI metadata key to an empty string.
    """
    media_pool_item = clip.GetMediaPoolItem()
    if not media_pool_item:
        return False

    empty = {key: "" for key in AI_METADATA_KEYS}
    return bool(media_pool_item.SetMetadata(empty))


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
