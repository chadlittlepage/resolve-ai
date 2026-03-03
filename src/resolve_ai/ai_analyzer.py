"""Gemini Vision analysis of captured frames."""

from __future__ import annotations

import base64
import time

from google import genai
from google.genai import types

from resolve_ai.config import Config
from resolve_ai.models import ClipAnalysis, ColoristFlags, SceneDescription

SYSTEM_PROMPT = """\
You are a professional colorist's assistant analyzing video frames for DaVinci Resolve. \
Provide precise, technical descriptions useful for color grading workflows."""

ANALYSIS_PROMPT_TEMPLATE = """\
Analyze this video frame for a colorist. The clip is {duration_sec:.1f} seconds long.

Respond in EXACTLY this format with no extra text:

SCENE: [1-2 sentence scene description]
LIGHTING: [lighting type and quality]
KEYWORDS: [comma-separated descriptive keywords]
PALETTE: [dominant colors in the frame]
LOCATION: [Interior/Exterior/Mixed]
TIME: [Day/Night/Golden Hour/Blue Hour/Dusk/Dawn/Artificial/Unknown]

FLAGS:
Animation Cut: [Yes/No]
Backs: [Yes/No]
Non-Fade Transitions: [Yes/No]
Flashes: [Yes/No]
Quick Cuts: [Yes/No - Yes if clip is under 2 seconds]
1-Shots Long: [Yes/No - Yes if clip is over 10 seconds]
Bright Scene: [Yes/No]
Dark Scene: [Yes/No]
Mixed Textures: [Yes/No]
Yellows: [Yes/No]
Landscape: [Yes/No]
Large Flat Surface: [Yes/No]
Face CU: [Yes/No]
No Face Then Face: [Yes/No - if unsure from single frame, No]
Skin Tones: [Yes/No]
Moving Trees: [Yes/No]
Water: [Yes/No]"""


def analyze_frame(
    config: Config,
    image_b64: str,
    clip_name: str,
    clip_index: int,
    duration_frames: int,
    fps: float = 24.0,
) -> ClipAnalysis:
    """Send a frame to Gemini Flash for scene analysis.

    Retries up to config.max_retries times on transient failures.
    """
    duration_sec = duration_frames / fps
    prompt = ANALYSIS_PROMPT_TEMPLATE.format(duration_sec=duration_sec)

    client = genai.Client(api_key=config.google_api_key)

    image_bytes = base64.b64decode(image_b64)
    image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")

    last_error: Exception | None = None
    for attempt in range(config.max_retries):
        try:
            response = client.models.generate_content(
                model=config.model,
                contents=[image_part, prompt],  # type: ignore[arg-type]
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    max_output_tokens=1024,
                ),
            )

            text = response.text or ""
            return _parse_response(text, clip_name, clip_index, config.model)

        except Exception as e:
            last_error = e
            if attempt < config.max_retries - 1:
                time.sleep(2 ** (attempt + 1))

    return ClipAnalysis(
        clip_name=clip_name,
        clip_index=clip_index,
        model=config.model,
        error=f"API failed after {config.max_retries} attempts: {last_error}",
    )


def _parse_response(
    text: str,
    clip_name: str,
    clip_index: int,
    model: str,
) -> ClipAnalysis:
    """Parse the structured text response into a ClipAnalysis."""
    lines = text.strip().split("\n")
    data: dict[str, str] = {}

    for line in lines:
        line = line.strip()
        if not line or line == "FLAGS:":
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            data[key.strip()] = value.strip()

    scene = SceneDescription(
        scene=data.get("SCENE", ""),
        lighting=data.get("LIGHTING", ""),
        keywords=data.get("KEYWORDS", ""),
        palette=data.get("PALETTE", ""),
        location=data.get("LOCATION", ""),
        time_of_day=data.get("TIME", ""),
    )

    def flag(key: str) -> bool:
        return data.get(key, "No").lower().startswith("yes")

    flags = ColoristFlags(
        animation_cut=flag("Animation Cut"),
        backs=flag("Backs"),
        non_fade_transitions=flag("Non-Fade Transitions"),
        flashes=flag("Flashes"),
        quick_cuts=flag("Quick Cuts"),
        one_shots_long=flag("1-Shots Long"),
        bright_scene=flag("Bright Scene"),
        dark_scene=flag("Dark Scene"),
        mixed_textures=flag("Mixed Textures"),
        yellows=flag("Yellows"),
        landscape=flag("Landscape"),
        large_flat_surface=flag("Large Flat Surface"),
        face_cu=flag("Face CU"),
        no_face_then_face=flag("No Face Then Face"),
        skin_tones=flag("Skin Tones"),
        moving_trees=flag("Moving Trees"),
        water=flag("Water"),
    )

    return ClipAnalysis(
        clip_name=clip_name,
        clip_index=clip_index,
        scene=scene,
        flags=flags,
        model=model,
    )
