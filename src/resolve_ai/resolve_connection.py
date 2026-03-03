"""DaVinci Resolve API connection and wrapper."""

from __future__ import annotations

import importlib.util
import os
from dataclasses import dataclass
from typing import Any


@dataclass
class ResolveContext:
    """Holds references to the active Resolve session objects."""

    resolve: Any
    project_manager: Any
    project: Any
    timeline: Any
    gallery: Any


def get_resolve() -> Any | None:
    """Get the DaVinci Resolve application object."""
    try:
        import DaVinciResolveScript as DvrScript  # noqa: N813

        return DvrScript.scriptapp("Resolve")
    except ImportError:
        pass

    possible_paths = [
        "/Library/Application Support/Blackmagic Design/"
        "DaVinci Resolve/Developer/Scripting/Modules/",
        os.path.expanduser(
            "~/Library/Application Support/Blackmagic Design/"
            "DaVinci Resolve/Developer/Scripting/Modules/"
        ),
        "/opt/resolve/Developer/Scripting/Modules/",
        r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules\\",
    ]

    for path in possible_paths:
        module_path = os.path.join(path, "DaVinciResolveScript.py")
        if os.path.exists(module_path):
            spec = importlib.util.spec_from_file_location("DaVinciResolveScript", module_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module.scriptapp("Resolve")

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
