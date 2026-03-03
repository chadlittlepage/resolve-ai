"""Tests for metadata writer module."""

from __future__ import annotations

from unittest.mock import MagicMock

from resolve_ai.metadata_writer import (
    AI_METADATA_KEYS,
    clear_metadata,
    read_metadata,
    write_metadata,
)
from resolve_ai.models import ClipAnalysis, ColoristFlags, SceneDescription


def test_write_metadata(mock_clip: MagicMock, mock_media_pool_item: MagicMock) -> None:
    analysis = ClipAnalysis(
        clip_name="Test",
        clip_index=0,
        scene=SceneDescription(scene="A dark room", lighting="Low key"),
        flags=ColoristFlags(dark_scene=True, face_cu=True),
        model="claude-haiku-4-5-20251001",
    )

    result = write_metadata(mock_clip, analysis)

    assert result is True
    mock_media_pool_item.SetMetadata.assert_called_once()

    meta = mock_media_pool_item.SetMetadata.call_args[0][0]
    assert meta["Scene Description"] == "A dark room"
    assert meta["Dark Scene"] == "Yes"
    assert meta["Face CU"] == "Yes"
    assert meta["Water"] == "No"
    assert meta["AI Model"] == "claude-haiku-4-5-20251001"


def test_write_metadata_no_media_pool_item() -> None:
    clip = MagicMock()
    clip.GetMediaPoolItem.return_value = None

    analysis = ClipAnalysis(clip_name="Gen", clip_index=0, model="test")
    assert write_metadata(clip, analysis) is False


def test_clear_metadata(mock_clip: MagicMock, mock_media_pool_item: MagicMock) -> None:
    result = clear_metadata(mock_clip)

    assert result is True
    meta = mock_media_pool_item.SetMetadata.call_args[0][0]
    for key in AI_METADATA_KEYS:
        assert meta[key] == ""


def test_read_metadata_empty(mock_clip: MagicMock) -> None:
    result = read_metadata(mock_clip)
    assert result == {}


def test_read_metadata_with_data(mock_clip: MagicMock, mock_media_pool_item: MagicMock) -> None:
    mock_media_pool_item.GetMetadata.return_value = {
        "Scene Description": "A sunny beach",
        "Water": "Yes",
        "Unrelated Key": "ignored",
    }

    result = read_metadata(mock_clip)
    assert result["Scene Description"] == "A sunny beach"
    assert result["Water"] == "Yes"
    assert "Unrelated Key" not in result
