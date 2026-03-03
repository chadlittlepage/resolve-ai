"""Configuration and environment loading."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    """Application configuration loaded from environment."""

    google_api_key: str
    model: str = "gemini-2.5-flash"
    max_retries: int = 3
    temp_dir: Path = field(default_factory=lambda: Path("/tmp/resolve-ai-stills"))

    def __post_init__(self) -> None:
        self.temp_dir.mkdir(parents=True, exist_ok=True)


def load_config() -> Config:
    """Load configuration from environment variables."""
    load_dotenv()

    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        raise SystemExit(
            "GOOGLE_API_KEY not set. Export it or add it to a .env file in the project root.\n"
            "Get a free key at https://aistudio.google.com"
        )

    return Config(
        google_api_key=api_key,
        model=os.environ.get("RESOLVE_AI_MODEL", "gemini-2.5-flash"),
    )
