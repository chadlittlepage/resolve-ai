"""Tests for AI analyzer module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from resolve_ai.ai_analyzer import _parse_response, analyze_frame
from resolve_ai.config import Config

SAMPLE_RESPONSE = """\
SCENE: A man walks through a dimly lit warehouse, industrial shelving visible in background.
LIGHTING: Low-key industrial fluorescent with warm practicals
KEYWORDS: warehouse, industrial, man, walking, shelving, concrete
PALETTE: Desaturated blues, warm amber practicals, grey concrete
LOCATION: Interior
TIME: Artificial

FLAGS:
Animation Cut: No
Backs: Yes
Non-Fade Transitions: No
Flashes: No
Quick Cuts: No
1-Shots Long: Yes
Bright Scene: No
Dark Scene: Yes
Mixed Textures: Yes
Yellows: Yes
Landscape: No
Large Flat Surface: Yes
Face CU: No
No Face Then Face: No
Skin Tones: No
Moving Trees: No
Water: No"""


def test_parse_response() -> None:
    result = _parse_response(SAMPLE_RESPONSE, "Clip 1", 0, "claude-haiku-4-5-20251001")

    assert result.clip_name == "Clip 1"
    assert result.clip_index == 0
    assert result.error is None

    assert "warehouse" in result.scene.scene.lower()
    assert result.scene.location == "Interior"
    assert result.scene.time_of_day == "Artificial"

    assert result.flags.backs is True
    assert result.flags.dark_scene is True
    assert result.flags.one_shots_long is True
    assert result.flags.yellows is True
    assert result.flags.large_flat_surface is True

    assert result.flags.animation_cut is False
    assert result.flags.bright_scene is False
    assert result.flags.face_cu is False
    assert result.flags.water is False


def test_parse_response_to_metadata() -> None:
    result = _parse_response(SAMPLE_RESPONSE, "Clip 1", 0, "claude-haiku-4-5-20251001")
    meta = result.to_metadata_dict()

    assert meta["Backs"] == "Yes"
    assert meta["Dark Scene"] == "Yes"
    assert meta["Water"] == "No"
    assert meta["AI Model"] == "claude-haiku-4-5-20251001"
    assert "Interior" in meta["Location"]


def test_analyze_frame_api_call() -> None:
    config = Config(anthropic_api_key="test-key")

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=SAMPLE_RESPONSE)]

    with patch("resolve_ai.ai_analyzer.anthropic.Anthropic") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_client_cls.return_value = mock_client

        result = analyze_frame(
            config=config,
            image_b64="dGVzdA==",
            clip_name="Test Clip",
            clip_index=0,
            duration_frames=48,
            fps=24.0,
        )

    assert result.error is None
    assert result.clip_name == "Test Clip"
    mock_client.messages.create.assert_called_once()

    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-haiku-4-5-20251001"


def test_analyze_frame_retries_on_error() -> None:
    config = Config(anthropic_api_key="test-key", max_retries=2)

    with patch("resolve_ai.ai_analyzer.anthropic.Anthropic") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API down")
        mock_client_cls.return_value = mock_client

        with patch("resolve_ai.ai_analyzer.time.sleep"):
            result = analyze_frame(
                config=config,
                image_b64="dGVzdA==",
                clip_name="Fail Clip",
                clip_index=0,
                duration_frames=24,
            )

    assert result.error is not None
    assert "2 attempts" in result.error
