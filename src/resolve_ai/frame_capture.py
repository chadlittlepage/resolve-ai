"""Frame capture from DaVinci Resolve timeline clips."""

from __future__ import annotations

import base64
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image

from resolve_ai.resolve_connection import ResolveContext


def capture_frames_gallery(
    ctx: ResolveContext,
    temp_dir: Path,
) -> list[Path]:
    """Capture middle-frame stills from all clips via the gallery (batch).

    Switches to the Color page (required for gallery operations),
    then returns a list of exported JPEG paths in clip order.
    """
    resolve = ctx.resolve
    timeline = ctx.timeline
    gallery = ctx.gallery

    # Gallery/stills operations require the Color page
    resolve.OpenPage("color")

    if not gallery:
        raise RuntimeError("Could not access the gallery. Is a project open?")

    album = gallery.GetCurrentStillAlbum()
    if not album:
        raise RuntimeError("No current still album. Open the gallery and try again.")

    # Grab middle frame from every clip
    stills = timeline.GrabAllStills(2)
    if not stills:
        raise RuntimeError("GrabAllStills returned no stills. Is the timeline empty?")

    temp_dir.mkdir(parents=True, exist_ok=True)

    # Export as JPEG
    success = album.ExportStills(stills, str(temp_dir), "clip_", "jpg")
    if not success:
        album.DeleteStills(stills)
        raise RuntimeError("ExportStills failed. Check gallery permissions.")

    # Clean up gallery
    album.DeleteStills(stills)

    # Collect exported files in order
    exported = sorted(temp_dir.glob("clip_*.jpg"))
    return exported


def capture_frames_playhead(
    ctx: ResolveContext,
    clips: list[Any],
    temp_dir: Path,
) -> list[Path]:
    """Capture a middle-frame still from each clip using ExportCurrentFrameAsStill.

    Fallback when gallery approach fails. Moves playhead to each clip's midpoint
    and exports one frame at a time. Returns list of JPEG paths in clip order.
    """
    resolve = ctx.resolve
    timeline = ctx.timeline
    project = ctx.project

    # ExportCurrentFrameAsStill works from Color page
    resolve.OpenPage("color")

    temp_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    for i, clip in enumerate(clips):
        start = clip.GetStart()
        duration = clip.GetDuration()
        mid_frame = start + duration // 2

        timeline.SetCurrentTimecode(str(mid_frame))

        out_path = temp_dir / f"clip_{i:04d}.jpg"
        success = project.ExportCurrentFrameAsStill(str(out_path))
        if success and out_path.exists():
            paths.append(out_path)
        else:
            paths.append(Path(""))  # placeholder for failed capture

    return paths


def capture_frame_thumbnail(
    timeline: Any,
    clip: Any,
) -> bytes:
    """Capture a frame using GetCurrentClipThumbnailImage (Color page).

    Moves playhead to clip midpoint, grabs the thumbnail, and returns JPEG bytes.
    Requires the Color page to be active.
    """
    # Move playhead to middle of clip
    start = clip.GetStart()
    duration = clip.GetDuration()
    mid_frame = start + duration // 2

    # Convert frame number to timecode
    # GetStartTimecode gives us the timeline start TC; we need frame-based positioning
    timeline.SetCurrentTimecode(str(mid_frame))

    thumb = timeline.GetCurrentClipThumbnailImage()
    if not thumb or not thumb.get("data"):
        raise RuntimeError(f"No thumbnail data for clip at frame {mid_frame}")

    width = thumb["width"]
    height = thumb["height"]
    raw_bytes = base64.b64decode(thumb["data"])

    # Convert RGB raw to JPEG via Pillow
    img = Image.frombytes("RGB", (width, height), raw_bytes)
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        img.save(f, format="JPEG", quality=85)
        return Path(f.name).read_bytes()


def capture_frame_playhead(
    ctx: ResolveContext,
    clip: Any,
    output_path: Path,
) -> Path:
    """Capture a frame by moving playhead and exporting via Project API.

    Fallback method when gallery approach is not available.
    """
    timeline = ctx.timeline
    project = ctx.project

    start = clip.GetStart()
    duration = clip.GetDuration()
    mid_frame = start + duration // 2

    timeline.SetCurrentTimecode(str(mid_frame))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    success = project.ExportCurrentFrameAsStill(str(output_path))
    if not success:
        raise RuntimeError(f"ExportCurrentFrameAsStill failed for frame {mid_frame}")

    return output_path


def load_frame_as_base64(path: Path) -> str:
    """Read a JPEG file and return its base64-encoded content."""
    return base64.b64encode(path.read_bytes()).decode("utf-8")
