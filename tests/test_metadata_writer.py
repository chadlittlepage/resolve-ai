"""Tests for metadata writer module."""

from __future__ import annotations

from unittest.mock import MagicMock

from resolve_ai.metadata_writer import (
    AI_METADATA_KEYS,
    clear_metadata,
    read_metadata,
    write_metadata,
)
from resolve_ai.models import (
    ClipAnalysis,
    ColoristFlags,
    SceneDescription,
    ShotDescription,
)


def test_write_metadata(mock_clip: MagicMock, mock_media_pool_item: MagicMock) -> None:
    analysis = ClipAnalysis(
        clip_name="Test",
        clip_index=0,
        scene=SceneDescription(scene="A dark room", lighting="Low key"),
        shot=ShotDescription(shot_size="MCU", camera_angle="Eye Level"),
        flags=ColoristFlags(dark_scene=True, face_cu=True),
        model="gemini-2.5-flash",
    )

    result = write_metadata(mock_clip, analysis)

    assert result is True
    # Check individual SetMetadata calls were made
    calls = mock_media_pool_item.SetMetadata.call_args_list
    call_dict = {c.args[0]: c.args[1] for c in calls}

    assert call_dict["Description"] == "A dark room"
    assert call_dict["Tone"] == "Low key"
    assert call_dict["Shot Type"] == "MCU"
    assert call_dict["Angle"] == "Eye Level"
    assert "Dark Scene" in call_dict["Comments"]
    assert "Face CU" in call_dict["Comments"]
    assert "gemini-2.5-flash" in call_dict["Colorist"]


def test_write_metadata_no_media_pool_item() -> None:
    clip = MagicMock()
    clip.GetMediaPoolItem.return_value = None

    analysis = ClipAnalysis(clip_name="Gen", clip_index=0, model="test")
    assert write_metadata(clip, analysis) is False


def test_clear_metadata(mock_clip: MagicMock, mock_media_pool_item: MagicMock) -> None:
    result = clear_metadata(mock_clip)

    assert result is True
    for key in AI_METADATA_KEYS:
        mock_media_pool_item.SetMetadata.assert_any_call(key, "")


def test_read_metadata_empty(mock_clip: MagicMock) -> None:
    result = read_metadata(mock_clip)
    assert result == {}


def test_read_metadata_with_data(mock_clip: MagicMock, mock_media_pool_item: MagicMock) -> None:
    mock_media_pool_item.GetMetadata.return_value = {
        "Description": "A sunny beach",
        "Shot Type": "Wide Shot",
        "Unrelated Key": "ignored",
    }

    result = read_metadata(mock_clip)
    assert result["Description"] == "A sunny beach"
    assert result["Shot Type"] == "Wide Shot"
    assert "Unrelated Key" not in result
