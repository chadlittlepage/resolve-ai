"""Data models for scene analysis results."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class SceneDescription:
    """AI-generated scene description."""

    scene: str = ""
    lighting: str = ""
    keywords: str = ""
    palette: str = ""
    location: str = ""
    time_of_day: str = ""


@dataclass
class ColoristFlags:
    """Boolean flags relevant to colorist workflow."""

    animation_cut: bool = False
    backs: bool = False
    non_fade_transitions: bool = False
    flashes: bool = False
    quick_cuts: bool = False
    one_shots_long: bool = False
    bright_scene: bool = False
    dark_scene: bool = False
    mixed_textures: bool = False
    yellows: bool = False
    landscape: bool = False
    large_flat_surface: bool = False
    face_cu: bool = False
    no_face_then_face: bool = False
    skin_tones: bool = False
    moving_trees: bool = False
    water: bool = False


@dataclass
class ClipAnalysis:
    """Complete analysis result for a single clip."""

    clip_name: str
    clip_index: int
    scene: SceneDescription = field(default_factory=SceneDescription)
    flags: ColoristFlags = field(default_factory=ColoristFlags)
    analysis_date: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    model: str = ""
    error: str | None = None

    def to_metadata_dict(self) -> dict[str, str]:
        """Convert analysis to Resolve metadata key-value pairs."""
        meta: dict[str, str] = {}

        # Scene description fields
        meta["Scene Description"] = self.scene.scene
        meta["Lighting"] = self.scene.lighting
        meta["Scene Keywords"] = self.scene.keywords
        meta["Color Palette"] = self.scene.palette
        meta["Location"] = self.scene.location
        meta["Time of Day"] = self.scene.time_of_day

        # Colorist flag fields
        flag_map = {
            "Animation Cut": self.flags.animation_cut,
            "Backs": self.flags.backs,
            "Non-Fade Transitions": self.flags.non_fade_transitions,
            "Flashes": self.flags.flashes,
            "Quick Cuts": self.flags.quick_cuts,
            "1-Shots Long": self.flags.one_shots_long,
            "Bright Scene": self.flags.bright_scene,
            "Dark Scene": self.flags.dark_scene,
            "Mixed Textures": self.flags.mixed_textures,
            "Yellows": self.flags.yellows,
            "Landscape": self.flags.landscape,
            "Large Flat Surface": self.flags.large_flat_surface,
            "Face CU": self.flags.face_cu,
            "No Face Then Face": self.flags.no_face_then_face,
            "Skin Tones": self.flags.skin_tones,
            "Moving Trees": self.flags.moving_trees,
            "Water": self.flags.water,
        }
        for key, value in flag_map.items():
            meta[key] = "Yes" if value else "No"

        # System fields
        meta["AI Analysis Date"] = self.analysis_date
        meta["AI Model"] = self.model

        return meta
