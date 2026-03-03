"""Tests for CLI commands."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from resolve_ai.cli import cli


@patch("resolve_ai.cli.connect")
def test_status_command(mock_connect: MagicMock) -> None:
    mock_ctx = MagicMock()
    mock_ctx.timeline.GetName.return_value = "My Timeline"
    mock_ctx.timeline.GetTrackCount.return_value = 2
    mock_ctx.timeline.GetItemListInTrack.side_effect = [
        [MagicMock()] * 5,
        [MagicMock()] * 3,
    ]
    mock_ctx.timeline.GetStartTimecode.return_value = "01:00:00:00"
    mock_ctx.project.GetName.return_value = "My Project"
    mock_connect.return_value = mock_ctx

    runner = CliRunner()
    result = runner.invoke(cli, ["status"])

    assert result.exit_code == 0
    assert "My Project" in result.output
    assert "My Timeline" in result.output


@patch("resolve_ai.cli.connect")
def test_clear_command(mock_connect: MagicMock) -> None:
    mock_clip = MagicMock()
    mock_clip.GetMediaPoolItem.return_value = MagicMock()
    mock_clip.GetMediaPoolItem().SetMetadata.return_value = True
    mock_clip.GetStart.return_value = 0

    mock_ctx = MagicMock()
    mock_ctx.timeline.GetTrackCount.return_value = 1
    mock_ctx.timeline.GetItemListInTrack.return_value = [mock_clip]
    mock_connect.return_value = mock_ctx

    runner = CliRunner()
    result = runner.invoke(cli, ["clear", "--yes"])

    assert result.exit_code == 0
    assert "Cleared" in result.output
