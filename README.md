# ResolveAI

AI-powered scene analysis for DaVinci Resolve using Claude Vision.

Captures a frame from each timeline clip, sends it to Claude Haiku 4.5 for analysis, and writes scene descriptions and colorist flags back to clip metadata inside Resolve.

## Requirements

- DaVinci Resolve Studio (scripting API requires Studio)
- Python 3.10+
- Anthropic API key

## Install

```bash
pip install -e .
```

## Setup

```bash
# Set your Anthropic API key
export ANTHROPIC_API_KEY=sk-ant-...

# Or create a .env file
cp .env.example .env
```

Make sure DaVinci Resolve is running with external scripting enabled:
**Preferences > System > General > External scripting using > Local**

## Usage

### Check connection

```bash
resolve-ai status
```

### Analyze all clips

```bash
resolve-ai analyze
```

### Preview without writing metadata

```bash
resolve-ai analyze --dry-run
```

### Analyze a specific video track

```bash
resolve-ai analyze --track 2
```

### Remove AI metadata

```bash
resolve-ai clear
```

## What it writes

### Scene Description Fields
- **Scene Description** - AI scene description
- **Lighting** - Lighting analysis
- **Scene Keywords** - Comma-separated keywords
- **Color Palette** - Dominant colors
- **Location** - Interior/exterior
- **Time of Day** - Day/night/etc

### Colorist Flags (Yes/No)
- **Animation Cut** - Contains animation or VFX cuts
- **Backs** - Back-of-head shots
- **Non-Fade Transitions** - Hard cuts, wipes, dissolves
- **Flashes** - Flash frames or bright flashes
- **Quick Cuts** - Rapid editing (under 2 seconds)
- **1-Shots Long** - Long single takes (over 10 seconds)
- **Bright Scene** - High APL scenes
- **Dark Scene** - Low-key, underexposed, night scenes
- **Mixed Textures** - Multiple texture types in frame
- **Yellows** - Yellow/red shift risk areas
- **Landscape** - Wide landscape compositions
- **Large Flat Surface** - Big flat areas (sky, walls)
- **Face CU** - Close-up face
- **No Face Then Face** - Face enters frame mid-shot
- **Skin Tones** - Prominent skin tones with colored lighting
- **Moving Trees** - Swaying foliage
- **Water** - Water present in frame

## Cost

- Claude Haiku 4.5: ~$0.002 per clip
- 100-clip timeline: ~$0.20
- 1000-clip timeline: ~$2.00

## Development

```bash
pip install -e ".[dev]"
pytest -v
ruff check src/ tests/
mypy src/resolve_ai
```
