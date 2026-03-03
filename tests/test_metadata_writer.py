"""Tests for metadata writer module."""

from __future__ import annotations

from unittest.mock import MagicMock

from resolve_ai.metadata_writer import clear_metadata, read_metadata, write_metadata
from resolve_ai.models import (
    ClipAnalysis,
    ColoristFlags,
    SceneDescription,
    ShotDescription,
)


def test_write_metadata_sets_name_and_marker(mock_clip: MagicMock) -> None:
    analysis = ClipAnalysis(
        clip_name="Test",
        clip_index=0,
        scene=SceneDescription(scene="A dark room", lighting="Low key"),
        shot=ShotDescription(shot_size="MCU", camera_angle="Eye Level", composition="Single"),
        flags=ColoristFlags(dark_scene=True, face_cu=True),
        model="gemini-2.5-flash",
    )

    mock_clip.AddMarker.return_value = True

    result = write_metadata(mock_clip, analysis)

    assert result is True
    mock_clip.SetName.assert_called_once_with("MCU | Single | Eye Level")
    mock_clip.AddMarker.assert_called_once()

    # Verify MediaPoolItem metadata was also written
    mpi = mock_clip.GetMediaPoolItem()
    mpi.SetMetadata.assert_called()

    args = mock_clip.AddMarker.call_args.args
    assert args[0] == 0  # frame 0
    assert args[1] == "Cream"  # marker color
    assert "MCU" in args[2]  # marker name
    assert "A dark room" in args[3]  # note contains scene
    assert "Dark Scene" in args[3]  # note contains flags


def test_write_metadata_no_media_pool_item_still_works(mock_clip: MagicMock) -> None:
    """Write should work even without MediaPoolItem since we use TimelineItem."""
    mock_clip.GetMediaPoolItem.return_value = None
    mock_clip.AddMarker.return_value = True

    analysis = ClipAnalysis(
        clip_name="Gen",
        clip_index=0,
        shot=ShotDescription(shot_size="Wide Shot"),
        model="test",
    )

    result = write_metadata(mock_clip, analysis)
    assert result is True


def test_clear_metadata(mock_clip: MagicMock) -> None:
    mock_clip.DeleteMarkersByColor.return_value = True

    result = clear_metadata(mock_clip)

    assert result is True
    mock_clip.DeleteMarkersByColor.assert_called_once_with("Cream")
    mock_clip.SetName.assert_called_once_with("")


def test_read_metadata_from_marker(mock_clip: MagicMock) -> None:
    mock_clip.GetMarkers.return_value = {
        0: {
            "color": "Cream",
            "name": "AI: MCU",
            "note": "A dark room",
            "customData": '{"Scene Description":"A dark room","Water":"No"}',
        }
    }

    result = read_metadata(mock_clip)
    assert result["Scene Description"] == "A dark room"
    assert result["Water"] == "No"


def test_read_metadata_empty(mock_clip: MagicMock) -> None:
    mock_clip.GetMarkers.return_value = {}
    result = read_metadata(mock_clip)
    assert result == {}
