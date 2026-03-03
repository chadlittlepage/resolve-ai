"""Click CLI for ResolveAI."""

from __future__ import annotations

import shutil

import click
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table

from resolve_ai.ai_analyzer import analyze_frame
from resolve_ai.config import load_config
from resolve_ai.frame_capture import capture_frames_gallery, load_frame_as_base64
from resolve_ai.metadata_writer import (
    clear_metadata,
    write_metadata,
)
from resolve_ai.resolve_connection import (
    connect,
    get_timeline_clips,
    get_timeline_info,
    run_scene_detect,
)

console = Console()


@click.group()
def cli() -> None:
    """ResolveAI - AI scene analysis for DaVinci Resolve."""


@cli.command()
@click.option("--track", default=1, help="Video track number to analyze.")
@click.option("--dry-run", is_flag=True, help="Analyze without writing metadata.")
@click.option(
    "--scene-detect",
    is_flag=True,
    help="Run scene detection before analysis to split timeline into clips.",
)
def analyze(track: int, dry_run: bool, scene_detect: bool) -> None:
    """Analyze all clips on the current timeline."""
    config = load_config()
    ctx = connect()

    if scene_detect:
        console.print("[bold]Running scene detection...[/bold]")
        if run_scene_detect(ctx.timeline):
            console.print("[green]Scene detection complete.[/green]")
        else:
            console.print("[red]Scene detection failed. Continuing with existing clips.[/red]")

    clips = get_timeline_clips(ctx.timeline, track)

    if not clips:
        console.print("[yellow]No clips found on video track {track}.[/yellow]")
        return

    console.print(
        f"[bold]Timeline:[/bold] {ctx.timeline.GetName()}  "
        f"[bold]Track:[/bold] V{track}  "
        f"[bold]Clips:[/bold] {len(clips)}"
    )

    if dry_run:
        console.print("[yellow]Dry run mode - no metadata will be written.[/yellow]")

    # Capture frames via gallery
    console.print("\n[bold]Capturing frames...[/bold]")
    try:
        frame_paths = capture_frames_gallery(ctx, config.temp_dir)
    except RuntimeError as e:
        console.print(f"[red]Frame capture failed: {e}[/red]")
        return

    if len(frame_paths) != len(clips):
        console.print(
            f"[yellow]Warning: {len(frame_paths)} frames captured "
            f"for {len(clips)} clips. Matching by position.[/yellow]"
        )

    count = min(len(frame_paths), len(clips))
    succeeded = 0
    failed = 0
    skipped = 0

    # Get FPS from timeline settings
    fps = float(ctx.timeline.GetSetting("timelineFrameRate") or 24)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing clips", total=count)

        for i in range(count):
            clip = clips[i]
            frame_path = frame_paths[i]

            clip_name = clip.GetName() or f"Clip {i + 1}"
            media_pool_item = clip.GetMediaPoolItem()

            if not media_pool_item:
                progress.update(task, advance=1, description=f"Skipped: {clip_name} (no media)")
                skipped += 1
                continue

            progress.update(task, advance=0, description=f"Analyzing: {clip_name}")

            try:
                image_b64 = load_frame_as_base64(frame_path)
                duration = clip.GetDuration()

                analysis = analyze_frame(
                    config=config,
                    image_b64=image_b64,
                    clip_name=clip_name,
                    clip_index=i,
                    duration_frames=duration,
                    fps=fps,
                )

                if analysis.error:
                    console.print(f"  [red]Error on {clip_name}: {analysis.error}[/red]")
                    failed += 1
                elif dry_run:
                    console.print(f"  [cyan]{clip_name}:[/cyan] {analysis.scene.scene}")
                    succeeded += 1
                else:
                    if write_metadata(clip, analysis):
                        succeeded += 1
                    else:
                        console.print(f"  [red]Failed to write metadata for {clip_name}[/red]")
                        failed += 1

            except Exception as e:
                console.print(f"  [red]Error on {clip_name}: {e}[/red]")
                failed += 1

            progress.update(task, advance=1)

    # Cleanup temp files
    if config.temp_dir.exists():
        shutil.rmtree(config.temp_dir, ignore_errors=True)

    # Summary
    console.print()
    table = Table(title="Analysis Summary")
    table.add_column("Status", style="bold")
    table.add_column("Count", justify="right")
    table.add_row("[green]Succeeded[/green]", str(succeeded))
    table.add_row("[red]Failed[/red]", str(failed))
    table.add_row("[yellow]Skipped[/yellow]", str(skipped))
    table.add_row("Total", str(count))
    console.print(table)

    if not dry_run and succeeded > 0:
        console.print(
            f"\n[green]Wrote metadata to {succeeded} clip(s). "
            f"Check the Metadata panel in Resolve.[/green]"
        )


@cli.command()
def status() -> None:
    """Check Resolve connection and show timeline info."""
    ctx = connect()
    info = get_timeline_info(ctx)

    table = Table(title="Resolve Status")
    table.add_column("Property", style="bold")
    table.add_column("Value")

    table.add_row("Project", info["project"])
    table.add_row("Timeline", info["timeline"])
    table.add_row("Start TC", info["start_tc"])
    table.add_row("Video Tracks", str(info["video_tracks"]))

    for track_num, clip_count in info["clip_counts"].items():
        table.add_row(f"  V{track_num} clips", str(clip_count))

    console.print(table)


@cli.command()
@click.option("--track", default=1, help="Video track number.")
@click.confirmation_option(prompt="This will remove all AI metadata. Continue?")
def clear(track: int) -> None:
    """Remove AI metadata from all clips on a track."""
    ctx = connect()
    clips = get_timeline_clips(ctx.timeline, track)

    if not clips:
        console.print("[yellow]No clips found.[/yellow]")
        return

    cleared = 0
    for clip in clips:
        if clear_metadata(clip):
            cleared += 1

    console.print(f"[green]Cleared AI metadata from {cleared}/{len(clips)} clip(s).[/green]")
