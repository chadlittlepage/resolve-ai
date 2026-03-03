"""DaVinci Resolve API connection and wrapper."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Any

# Paths where the DaVinciResolveScript module lives
_MODULE_PATHS = [
    "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules",
    os.path.expanduser(
        "~/Library/Application Support/Blackmagic Design/"
        "DaVinci Resolve/Developer/Scripting/Modules"
    ),
    "/opt/resolve/Developer/Scripting/Modules",
    r"C:\ProgramData\Blackmagic Design\DaVinci Resolve"
    r"\Support\Developer\Scripting\Modules",
]


@dataclass
class ResolveContext:
    """Holds references to the active Resolve session objects."""

    resolve: Any
    project_manager: Any
    project: Any
    timeline: Any
    gallery: Any


def get_resolve() -> Any | None:
    """Get the DaVinci Resolve application object.

    Adds the scripting modules path to sys.path so that
    DaVinciResolveScript can self-replace with the native fusionscript library.
    """
    # Ensure the modules directory is on sys.path before importing
    for path in _MODULE_PATHS:
        if os.path.isdir(path) and path not in sys.path:
            sys.path.insert(0, path)

    try:
        import DaVinciResolveScript as DvrScript  # noqa: N813

        return DvrScript.scriptapp("Resolve")
    except (ImportError, AttributeError):
        return None


def connect() -> ResolveContext:
    """Connect to Resolve and return a context with all session objects.

    Raises SystemExit with a descriptive message on failure.
    """
    resolve = get_resolve()
    if not resolve:
        raise SystemExit(
            "Could not connect to DaVinci Resolve.\n"
            "Make sure Resolve is running with scripting enabled "
            "(Preferences > System > General > External scripting using)."
        )

    pm = resolve.GetProjectManager()
    if not pm:
        raise SystemExit("Connected to Resolve but could not access the Project Manager.")

    project = pm.GetCurrentProject()
    if not project:
        raise SystemExit("No project is currently open in Resolve.")

    timeline = project.GetCurrentTimeline()
    if not timeline:
        raise SystemExit("No timeline is currently active. Open a timeline and try again.")

    gallery = project.GetGallery()

    return ResolveContext(
        resolve=resolve,
        project_manager=pm,
        project=project,
        timeline=timeline,
        gallery=gallery,
    )


def run_scene_detect(timeline: Any) -> bool:
    """Run scene detection on the timeline, splitting it into clips at each cut.

    Must be called before gathering clips if the timeline is a single long clip.
    Returns True if successful.
    """
    result = timeline.DetectSceneCuts()
    return bool(result)


def get_timeline_clips(timeline: Any, track: int = 1) -> list[Any]:
    """Get all clips from a video track, sorted by start frame."""
    track_count = timeline.GetTrackCount("video")
    if track > track_count:
        raise SystemExit(
            f"Video track {track} does not exist. Timeline has {track_count} video track(s)."
        )

    items = timeline.GetItemListInTrack("video", track)
    if not items:
        return []

    return sorted(items, key=lambda c: c.GetStart())


def get_timeline_info(ctx: ResolveContext) -> dict[str, Any]:
    """Get summary info about the current timeline."""
    tl = ctx.timeline
    track_count = tl.GetTrackCount("video")
    clip_counts = {}
    for i in range(1, track_count + 1):
        items = tl.GetItemListInTrack("video", i)
        clip_counts[i] = len(items) if items else 0

    return {
        "project": ctx.project.GetName(),
        "timeline": tl.GetName(),
        "video_tracks": track_count,
        "clip_counts": clip_counts,
        "start_tc": tl.GetStartTimecode(),
    }
