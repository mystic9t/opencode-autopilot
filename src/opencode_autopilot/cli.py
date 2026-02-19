from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from . import __version__, config, detector
from .opencode import check_tool_availability
from .runner import RunOptions, run, run_gg_mode

console = Console(stderr=True, force_terminal=True, no_color=False)


def log(msg: str) -> None:
    try:
        console.print(msg)
    except Exception:
        print(msg)


app = typer.Typer(
    name="opencode-autopilot",
    help="Autonomous overnight engineer for OpenCode projects.",
    add_completion=False,
)


def get_project_dir(dir_arg: Optional[str]) -> Path:
    if dir_arg:
        return Path(dir_arg).resolve()
    return Path.cwd()


def check_prerequisites() -> bool:
    installed, message = check_tool_availability()
    if not installed:
        console.print(f"[red]Error:[/red] {message}")
        return False
    return True


def ask_yes(prompt: str, default: bool = True) -> bool:
    suffix = "[Y/n]: " if default else "[y/N]: "
    try:
        response = input(prompt + suffix).strip().lower()
        if not response:
            return default
        return response in ("y", "yes")
    except Exception:
        return default


def version_callback(value: bool) -> None:
    if value:
        console.print(f"opencode-autopilot {__version__}")
        raise typer.Exit()


@app.command(name="run")
def run_cmd(
    topic: Optional[str] = typer.Argument(None, help="Topic/nudge for --gg mode"),
    project: Optional[str] = typer.Option(None, "-p", "--project", help="Project directory"),
    sessions: Optional[int] = typer.Option(None, "-s", "--sessions", help="Number of sessions"),
    interval: Optional[int] = typer.Option(None, "-i", "--interval", help="Minutes between sessions"),
    resume: int = typer.Option(1, "-r", "--resume", help="Resume from session"),
    model: Optional[str] = typer.Option(None, "-m", "--model", help="Model to use"),
    yes: bool = typer.Option(False, "-y", "--yes", help="Skip confirmation"),
    gg: bool = typer.Option(False, "--gg", help="Full trust mode: research and build from scratch"),
) -> int:
    """Run autonomous improvement sessions.
    
    Default: Improve existing project. Creates BLUEPRINT.md/HEARTBEAT/ if missing.
    
    Use --gg for full trust mode: research online and build from scratch.
    """
    if not check_prerequisites():
        return 1
    
    project_dir = get_project_dir(project)
    cfg = config.load_config(project_dir)
    state = detector.detect_project_state(project_dir)
    
    options = RunOptions(
        sessions=sessions if sessions is not None else (cfg.sessions or 10),
        interval=interval if interval is not None else (cfg.interval or 30),
        resume=resume,
        model=model or cfg.model or "opencode/big-pickle",
        agent="autonomous",
    )
    
    if gg:
        if state.state in (detector.ProjectState.ACTIVE, detector.ProjectState.COMPLETED):
            console.print("[yellow]Warning: Existing project found.[/yellow]")
            if not yes:
                if not ask_yes("Start fresh and overwrite?", default=False):
                    console.print("[yellow]Cancelled.[/yellow]")
                    return 0
        
        return 0 if run_gg_mode(project_dir, topic, options, log_callback=log) else 1
    
    else:
        if state.state == detector.ProjectState.EMPTY:
            console.print("[red]No project found.[/red]")
            console.print("")
            console.print("Options:")
            console.print("  1. Add a README.md or source files for guidance, then run again")
            console.print("  2. Run with --gg to let the agent research and build from scratch")
            console.print("")
            console.print("Example: opencode-autopilot run --gg \"build a todo app\"")
            return 1
        
        return 0 if run(project_dir, options, log_callback=log) else 1


@app.command(name="config")
def config_cmd(
    project: Optional[str] = typer.Option(None, "-p", "--project", help="Project directory"),
    model: Optional[str] = typer.Option(None, "-m", "--model", help="Default model"),
    sessions: Optional[int] = typer.Option(None, "-s", "--sessions", help="Default sessions"),
    interval: Optional[int] = typer.Option(None, "-i", "--interval", help="Default interval"),
    global_scope: bool = typer.Option(False, "-g", "--global", help="Global config"),
    show: bool = typer.Option(False, "--show", help="Show current config"),
) -> int:
    """Set persistent defaults."""
    project_dir = get_project_dir(project)
    
    if show:
        cfg = config.show_config(project_dir)
        console.print("[cyan]Config:[/cyan]")
        console.print(f"  Global: {cfg['global'] or '(none)'}")
        console.print(f"  Project: {cfg['local'] or '(none)'}")
        console.print(f"  Effective: {cfg['effective'] or '(defaults)'}")
        return 0
    
    updates = config.AutopilotConfig(model=model, sessions=sessions, interval=interval)
    
    if not (updates.model or updates.sessions or updates.interval):
        console.print("[yellow]Nothing to update. Use --show or set an option.[/yellow]")
        return 0
    
    config.save_config(project_dir, updates, global_scope)
    scope = "global" if global_scope else "project"
    console.print(f"[green]Saved to {scope} config.[/green]")
    return 0


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "-v", "--version", callback=version_callback, is_eager=True, help="Show version"),
) -> None:
    """Autonomous overnight engineer for OpenCode projects."""
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())


if __name__ == "__main__":
    app()
