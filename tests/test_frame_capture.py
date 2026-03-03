"""Tests for frame capture module."""

from __future__ import annotations

import base64
from pathlib import Path
from unittest.mock import MagicMock

from resolve_ai.frame_capture import load_frame_as_base64
from resolve_ai.resolve_connection import ResolveContext


def test_load_frame_as_base64(tmp_path: Path) -> None:
    img_path = tmp_path / "test.jpg"
    img_path.write_bytes(b"\xff\xd8\xff\xe0test-jpeg-data")

    result = load_frame_as_base64(img_path)
    decoded = base64.b64decode(result)
    assert decoded == b"\xff\xd8\xff\xe0test-jpeg-data"


def test_capture_frames_gallery_calls_api(tmp_path: Path) -> None:
    """Test that gallery capture calls the right Resolve API methods."""
    mock_album = MagicMock()
    mock_album.ExportStills.return_value = True
    mock_album.DeleteStills.return_value = True

    mock_gallery = MagicMock()
    mock_gallery.GetCurrentStillAlbum.return_value = mock_album

    mock_timeline = MagicMock()
    stills = [MagicMock(), MagicMock()]
    mock_timeline.GrabAllStills.return_value = stills

    ctx = ResolveContext(
        resolve=MagicMock(),
        project_manager=MagicMock(),
        project=MagicMock(),
        timeline=mock_timeline,
        gallery=mock_gallery,
    )

    # Create fake exported files so the glob finds them
    temp_dir = tmp_path / "stills"
    temp_dir.mkdir()
    (temp_dir / "clip_001.jpg").write_bytes(b"fake1")
    (temp_dir / "clip_002.jpg").write_bytes(b"fake2")

    from resolve_ai.frame_capture import capture_frames_gallery

    results = capture_frames_gallery(ctx, temp_dir)

    mock_timeline.GrabAllStills.assert_called_once_with(2)
    mock_album.ExportStills.assert_called_once()
    mock_album.DeleteStills.assert_called_once_with(stills)
    assert len(results) == 2
