from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from . import config, detector
from .opencode import check_opencode_installation
from .runner import GgOptions, RunOptions, run_gg, run_build, run_run

# Configure Rich console for Windows compatibility
# Use stderr for output and handle encoding issues
console = Console(stderr=True, force_terminal=True, no_color=False)


def log(msg: str) -> None:
    """Print a log message using Rich."""
    try:
        console.print(msg)
    except Exception:
        # Fallback to plain print if Rich fails
        import re
        plain = re.sub(r'\[/?[a-z]+\]', '', str(msg))
        print(plain)


app = typer.Typer(
    name="opencode-autopilot",
    help="Autonomous overnight engineer for OpenCode projects.",
    add_completion=False,
)


def get_project_dir(dir_arg: Optional[str]) -> Path:
    """Get the project directory, defaulting to current directory."""
    if dir_arg:
        return Path(dir_arg).resolve()
    return Path.cwd()


def check_prerequisites() -> bool:
    """Check if opencode is installed. Returns True if all good."""
    installed, message = check_opencode_installation()
    if not installed:
        console.print(f"[red]Error:[/red] {message}")
        return False
    return True


def ask_yes(prompt: str, default: bool = True) -> bool:
    """Ask yes/no question using Rich."""
    suffix = "[Y/n]: " if default else "[y/N]: "
    while True:
        try:
            response = typer.prompt.Prompt(prompt + suffix, default="y" if default else "n")
            response = response.strip().lower()
            if not response:
                return default
            if response in ("y", "yes"):
                return True
            if response in ("n", "no"):
                return False
            console.print("[yellow]Please enter y or n[/yellow]")
        except Exception:
            # Fallback to simple input
            response = input(prompt + suffix).strip().lower()
            if not response:
                return default
            if response in ("y", "yes"):
                return True
            if response in ("n", "no"):
                return False


def ask_choice(prompt: str, choices: list[str], default: str) -> str:
    """Ask user to choose from a list using Rich."""
    choices_str = "/".join(choices)
    suffix = f" [{choices_str}]: "
    while True:
        try:
            response = typer.prompt.Prompt(prompt + suffix, default=default)
            response = response.strip()
            if not response:
                return default
            if response in choices:
                return response
            console.print(f"[yellow]Please enter one of: {choices_str}[/yellow]")
        except Exception:
            response = input(prompt + suffix).strip()
            if not response:
                return default
            if response in choices:
                return response


def handle_auto_detect(project_dir: Path, yes: bool = False) -> int:
    """Handle the auto-detect mode when no command is given."""
    state = detector.detect_project_state(project_dir)
    
    # Load config for defaults
    cfg = config.load_config(project_dir)
    default_sessions = cfg.sessions or 10
    default_interval = cfg.interval or 30
    
    if state.state == detector.ProjectState.EMPTY:
        console.print("[cyan]Empty directory detected. Planning to auto-build from scratch.[/cyan]")
        if not yes:
            confirm = ask_yes("Continue with gg (full trust mode)?", default=True)
            if not confirm:
                console.print("[yellow]Cancelled. Run 'opencode-autopilot init' to scaffold.[/yellow]")
                return 0
        options = GgOptions(
            sessions=default_sessions,
            interval=default_interval,
            model=cfg.model or "opencode/big-pickle",
            agent="autonomous",
        )
        return run_gg(project_dir, None, options, log_callback=log)
    
    elif state.state == detector.ProjectState.HAS_CODE_NO_BLUEPRINT:
        console.print("[cyan]Detected existing project with no blueprint.[/cyan]")
        
        if state.has_text_only:
            console.print("[cyan]Found text files. Planning to scaffold and build.[/cyan]")
            if not yes:
                confirm = ask_yes("Continue with build (read text files as brief)?", default=True)
                if not confirm:
                    console.print("[yellow]Cancelled.[/yellow]")
                    return 0
            options = RunOptions(
                sessions=default_sessions,
                interval=default_interval,
                model=cfg.model or "opencode/big-pickle",
                agent="autonomous",
            )
            return run_build(project_dir, options, log_callback=log)
        
        console.print("[cyan]Found existing project with source code but no blueprint.[/cyan]")
        
        if not yes:
            choice = ask_choice("What would you like to do? (1=improve, 2=fresh)", ["1", "2"], "1")
        else:
            choice = "1"
        
        if choice == "1":
            options = RunOptions(
                sessions=default_sessions,
                interval=default_interval,
                model=cfg.model or "opencode/big-pickle",
                agent="autonomous",
            )
            return run_run(project_dir, options, log_callback=log)
        else:
            options = GgOptions(
                sessions=default_sessions,
                interval=default_interval,
                model=cfg.model or "opencode/big-pickle",
                agent="autonomous",
            )
            return run_gg(project_dir, None, options, log_callback=log)
    
    elif state.state == detector.ProjectState.BLUEPRINT_ONLY:
        console.print("[cyan]Found BLUEPRINT.md but no HEARTBEAT/. Planning to build.[/cyan]")
        if not yes:
            confirm = ask_yes("Continue with build?", default=True)
            if not confirm:
                console.print("[yellow]Cancelled.[/yellow]")
                return 0
        options = RunOptions(
            sessions=default_sessions,
            interval=default_interval,
            model=cfg.model or "opencode/big-pickle",
            agent="autonomous",
        )
        return run_build(project_dir, options, log_callback=log)
    
    elif state.state == detector.ProjectState.ACTIVE:
        console.print("[cyan]Detected an active autopilot project. Planning to run improvement loop.[/cyan]")
        if not yes:
            confirm = ask_yes("Continue with run (improvement loop)?", default=True)
            if not confirm:
                console.print("[yellow]Cancelled.[/yellow]")
                return 0
        options = RunOptions(
            sessions=default_sessions,
            interval=default_interval,
            model=cfg.model or "opencode/big-pickle",
            agent="autonomous",
        )
        return run_run(project_dir, options, log_callback=log)
    
    elif state.state == detector.ProjectState.COMPLETED:
        console.print("[green]Found completed project with DEPLOY_GUIDE.md.[/green]")
        console.print("You can start a new cycle with 'opencode-autopilot gg' or 'opencode-autopilot build'.")
        return 0
    
    return 0


@app.command()
def gg(
    topic: Optional[str] = typer.Argument(None, help="Optional topic/nudge for the agent"),
    project: Optional[str] = typer.Option(None, "--project", help="Project directory"),
    sessions: Optional[int] = typer.Option(None, "-s", "--sessions", help="Number of build sessions"),
    interval: Optional[int] = typer.Option(None, "-i", "--interval", help="Minutes between sessions"),
    model: Optional[str] = typer.Option(None, "-m", "--model", help="OpenCode model"),
    yes: bool = typer.Option(False, "-y", "--yes", help="Skip confirmation prompts"),
) -> int:
    """Full trust mode - agent researches, decides what to build, and builds it."""
    if not check_prerequisites():
        return 1
    
    project_dir = get_project_dir(project)
    
    # Load config for defaults
    cfg = config.load_config(project_dir)
    
    state = detector.detect_project_state(project_dir)
    if state.state in (detector.ProjectState.ACTIVE, detector.ProjectState.COMPLETED):
        console.print("[yellow]Warning: Active/completed project found.[/yellow]")
        if not yes:
            confirm = ask_yes("This will start fresh and ignore existing work. Continue?", default=False)
            if not confirm:
                console.print("[yellow]Cancelled.[/yellow]")
                return 0
    
    options = GgOptions(
        sessions=sessions if sessions is not None else (cfg.sessions or 10),
        interval=interval if interval is not None else (cfg.interval or 30),
        model=model or cfg.model or "opencode/big-pickle",
        agent="autonomous",
    )
    
    return 0 if run_gg(project_dir, topic, options, log_callback=log) else 1


@app.command()
def build(
    project: Optional[str] = typer.Option(None, "--project", help="Project directory"),
    sessions: Optional[int] = typer.Option(None, "-s", "--sessions", help="Number of build sessions"),
    interval: Optional[int] = typer.Option(None, "-i", "--interval", help="Minutes between sessions"),
    resume: int = typer.Option(1, "-r", "--resume", help="Resume from this run number"),
    model: Optional[str] = typer.Option(None, "-m", "--model", help="OpenCode model"),
    yes: bool = typer.Option(False, "-y", "--yes", help="Skip confirmation prompts"),
) -> int:
    """Bootstrap a new project: blueprint -> build sessions -> security review."""
    if not check_prerequisites():
        return 1
    
    project_dir = get_project_dir(project)
    
    # Load config for defaults
    cfg = config.load_config(project_dir)
    
    state = detector.detect_project_state(project_dir)
    
    if state.state == detector.ProjectState.EMPTY:
        console.print("[yellow]Empty directory. Use 'gg' to build from scratch.[/yellow]")
        return 1
    
    if state.state == detector.ProjectState.ACTIVE and resume == 1:
        console.print("[cyan]Active project found. Resuming improvement loop...[/cyan]")
    
    options = RunOptions(
        sessions=sessions if sessions is not None else (cfg.sessions or 10),
        interval=interval if interval is not None else (cfg.interval or 30),
        resume=resume,
        model=model or cfg.model or "opencode/big-pickle",
        agent="autonomous",
    )
    
    return 0 if run_build(project_dir, options, log_callback=log) else 1


@app.command()
def run_cmd(
    project: Optional[str] = typer.Option(None, "--project", help="Project directory"),
    sessions: Optional[int] = typer.Option(None, "-s", "--sessions", help="Number of improvement sessions"),
    interval: Optional[int] = typer.Option(None, "-i", "--interval", help="Minutes between sessions"),
    resume: int = typer.Option(1, "-r", "--resume", help="Resume from this run number"),
    model: Optional[str] = typer.Option(None, "-m", "--model", help="OpenCode model"),
    yes: bool = typer.Option(False, "-y", "--yes", help="Skip confirmation prompts"),
) -> int:
    """Improvement loop for existing projects: improvement sessions -> security review."""
    if not check_prerequisites():
        return 1
    
    project_dir = get_project_dir(project)
    
    # Load config for defaults
    cfg = config.load_config(project_dir)
    
    state = detector.detect_project_state(project_dir)
    
    if state.state == detector.ProjectState.EMPTY:
        console.print("[red]Error:[/red] No project found. Run 'gg' to build something.")
        return 1
    
    if state.state not in (
        detector.ProjectState.ACTIVE,
        detector.ProjectState.BLUEPRINT_ONLY,
        detector.ProjectState.HAS_CODE_NO_BLUEPRINT,
    ):
        console.print(f"[yellow]Project state: {state.state.value}. Running improvement loop.[/yellow]")
    
    options = RunOptions(
        sessions=sessions if sessions is not None else (cfg.sessions or 10),
        interval=interval if interval is not None else (cfg.interval or 30),
        resume=resume,
        model=model or cfg.model or "opencode/big-pickle",
        agent="autonomous",
    )
    
    return 0 if run_run(project_dir, options, log_callback=log) else 1


@app.command(name="config")
def config_cmd(
    project: Optional[str] = typer.Option(None, "--project", help="Project directory"),
    model: Optional[str] = typer.Option(None, "-m", "--model", help="Set default model"),
    agent: Optional[str] = typer.Option(None, "-a", "--agent", help="Set default agent"),
    sessions: Optional[int] = typer.Option(None, "-s", "--sessions", help="Default number of sessions"),
    interval: Optional[int] = typer.Option(None, "-i", "--interval", help="Default interval in minutes"),
    global_scope: bool = typer.Option(False, "-g", "--global", help="Use global config"),
    show: bool = typer.Option(False, "--show", help="Show current config"),
) -> int:
    """Set persistent defaults for model, sessions, and interval."""
    project_dir = get_project_dir(project)
    
    if show:
        cfg = config.show_config(project_dir)
        console.print("\n[cyan]Global config (~/.autopilot.json):[/cyan]")
        console.print(f"  {cfg['global']}" if cfg['global'] else "  (none)")
        
        console.print("\n[cyan]Project config (.autopilot.json):[/cyan]")
        console.print(f"  {cfg['local']}" if cfg['local'] else "  (none)")
        
        console.print("\n[cyan]Effective config (project overrides global):[/cyan]")
        console.print(f"  {cfg['effective']}" if cfg['effective'] else "  (none - using defaults)")
        
        console.print("\n[cyan]Defaults:[/cyan]")
        console.print("  model = opencode/big-pickle")
        console.print("  sessions = 10")
        console.print("  interval = 30")
        console.print("  agent = autonomous")
        console.print()
        return 0
    
    updates = config.AutopilotConfig(model=model, agent=agent, sessions=sessions, interval=interval)
    
    if updates.model is None and updates.agent is None and updates.sessions is None and updates.interval is None:
        console.print("[yellow]Nothing to update. Use --model, --agent, --sessions, --interval, or --show.[/yellow]")
        return 0
    
    config.save_config(project_dir, updates, global_scope)
    
    scope = "global (~/.autopilot.json)" if global_scope else "project (.autopilot.json)"
    console.print(f"[green]Config saved to {scope}:[/green]")
    if updates.model:
        console.print(f"  model = {updates.model}")
    if updates.agent:
        console.print(f"  agent = {updates.agent}")
    if updates.sessions is not None:
        console.print(f"  sessions = {updates.sessions}")
    if updates.interval is not None:
        console.print(f"  interval = {updates.interval}")
    
    effective = config.load_config(project_dir)
    console.print("\nEffective settings:")
    console.print(f"  model: {effective.model or 'opencode/big-pickle (default)'}")
    console.print(f"  sessions: {effective.sessions or 10}")
    console.print(f"  interval: {effective.interval or 30} minutes")
    console.print(f"  agent: {effective.agent or 'autonomous (default)'}")
    
    return 0


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    project: Optional[str] = typer.Option(None, "--project", help="Project directory"),
    yes: bool = typer.Option(False, "-y", "--yes", help="Skip confirmation prompts"),
) -> int:
    """Auto-detect project state and run the appropriate command."""
    if ctx.invoked_subcommand is not None:
        return
    
    if not check_prerequisites():
        return 1
    
    project_dir = get_project_dir(project)
    
    console.print("[cyan]Detecting project state...[/cyan]")
    return handle_auto_detect(project_dir, yes=yes)


if __name__ == "__main__":
    app()
