"""Shared fixtures for mocking DaVinci Resolve objects."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_media_pool_item() -> MagicMock:
    """A mock MediaPoolItem that accepts metadata."""
    item = MagicMock()
    item.SetMetadata.return_value = True
    item.GetMetadata.return_value = {}
    return item


@pytest.fixture
def mock_clip(mock_media_pool_item: MagicMock) -> MagicMock:
    """A mock TimelineItem (clip)."""
    clip = MagicMock()
    clip.GetName.return_value = "Test Clip"
    clip.GetStart.return_value = 86400
    clip.GetDuration.return_value = 48
    clip.GetEnd.return_value = 86448
    clip.GetMediaPoolItem.return_value = mock_media_pool_item
    return clip


@pytest.fixture
def mock_timeline(mock_clip: MagicMock) -> MagicMock:
    """A mock Timeline."""
    tl = MagicMock()
    tl.GetName.return_value = "Test Timeline"
    tl.GetTrackCount.return_value = 1
    tl.GetItemListInTrack.return_value = [mock_clip]
    tl.GetStartTimecode.return_value = "01:00:00:00"
    tl.GetSetting.return_value = "24"
    tl.GrabAllStills.return_value = [MagicMock()]
    return tl


@pytest.fixture
def mock_gallery() -> MagicMock:
    """A mock Gallery with album."""
    album = MagicMock()
    album.ExportStills.return_value = True
    album.DeleteStills.return_value = True

    gallery = MagicMock()
    gallery.GetCurrentStillAlbum.return_value = album
    return gallery


@pytest.fixture
def mock_project(mock_timeline: MagicMock, mock_gallery: MagicMock) -> MagicMock:
    """A mock Project."""
    project = MagicMock()
    project.GetName.return_value = "Test Project"
    project.GetCurrentTimeline.return_value = mock_timeline
    project.GetGallery.return_value = mock_gallery
    return project
