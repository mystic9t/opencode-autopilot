from __future__ import annotations

import sys
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


def show_plan(
    project_dir: Path,
    state: detector.DetectionResult,
    options: RunOptions,
    is_gg: bool,
) -> int:
    """Show the execution plan without running."""
    console.print("")
    console.print("[bold cyan]Execution Plan[/bold cyan]")
    console.print("=" * 50)
    console.print(f"Project  : {project_dir}")
    console.print(f"State    : {state.state.value}")
    console.print(f"Tool     : {options.preferred_tool or 'auto (opencode -> kilo)'}")
    console.print(f"Model    : {options.model}")
    console.print(f"Sessions : {options.sessions}")
    console.print(f"Interval : {options.interval} minutes")
    
    if options.directive:
        console.print(f"Directive: {options.directive}")
    
    if is_gg:
        console.print(f"Mode     : GG (full trust, research & build from scratch)")
    
    console.print("-" * 50)
    
    # Analyze project type
    if state.state == detector.ProjectState.EMPTY:
        console.print("[yellow]Project: NEW (empty directory)[/yellow]")
        console.print("")
        console.print("Plan:")
        console.print("  1. Create BLUEPRINT.md based on directive")
        console.print("  2. Initialize .opencode-autopilot/HEARTBEAT/")
        console.print("  3. Run build sessions to create the project")
        console.print("  4. Final security review session")
        console.print("")
        console.print("[green]Recommendation: Use --gg mode to build from scratch[/green]")
        
    elif state.state == detector.ProjectState.HAS_CODE_NO_BLUEPRINT:
        console.print("[yellow]Project: EXISTING (no autopilot)[/yellow]")
        console.print("")
        console.print("Plan:")
        console.print("  1. Analyze existing code")
        console.print("  2. Create BLUEPRINT.md based on directive or existing code")
        console.print("  3. Initialize .opencode-autopilot/HEARTBEAT/")
        console.print("  4. Run improvement sessions")
        console.print("  5. Final security review session")
        
    elif state.state == detector.ProjectState.BLUEPRINT_ONLY:
        console.print("[yellow]Project: BLUEPRINT ONLY (incomplete setup)[/yellow]")
        console.print("")
        console.print("Plan:")
        console.print("  1. Initialize .opencode-autopilot/HEARTBEAT/")
        console.print("  2. Run build/improvement sessions")
        console.print("  3. Final security review session")
        
    elif state.state == detector.ProjectState.ACTIVE:
        console.print("[yellow]Project: ACTIVE (mid-cycle)[/yellow]")
        console.print("")
        console.print("Plan:")
        console.print(f"  1. Resume from session {options.resume}")
        console.print("  2. Continue with remaining sessions")
        console.print("  3. Final security review session")
        
    elif state.state == detector.ProjectState.COMPLETED:
        console.print("[yellow]Project: COMPLETED (has DEPLOY_GUIDE)[/yellow]")
        console.print("")
        console.print("Plan:")
        console.print("  1. Run improvement sessions")
        console.print("  2. Update DEPLOY_GUIDE.md if needed")
        console.print("  3. Final security review session")
    
    console.print("")
    console.print("[bold]To execute this plan, run without --plan:[/bold]")
    if options.directive:
        console.print(f"  opencode-autopilot run \"{options.directive}\"")
    else:
        console.print(f"  opencode-autopilot run")
    
    return 0


# Entry point wrapper for CLI
def cli_main():
    """Main entry point that handles shorthand commands."""
    # Check if first argument looks like a directive (not a flag/command)
    if len(sys.argv) > 1:
        first_arg = sys.argv[1]
        # If it doesn't start with - and is not a known command, treat as directive
        known_commands = {"run", "config", "help", "version", "-v", "--version", "-h", "--help", "--plan"}
        if not first_arg.startswith("-") and first_arg not in known_commands:
            # Prepend "run" to arguments
            sys.argv = [sys.argv[0], "run"] + sys.argv[1:]
    
    app()


# Alias for backward compatibility
main = cli_main


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


@app.command(name="run")
def run_cmd(
    directive: Optional[str] = typer.Argument(None, help="Directive/task for the agent (e.g., 'focus on UI updates only')"),
    project: Optional[str] = typer.Option(None, "-p", "--project", help="Project directory"),
    sessions: Optional[int] = typer.Option(None, "-s", "--sessions", help="Number of sessions"),
    interval: Optional[int] = typer.Option(None, "-i", "--interval", help="Minutes between sessions"),
    resume: int = typer.Option(1, "-r", "--resume", help="Resume from session"),
    model: Optional[str] = typer.Option(None, "-m", "--model", help="Model to use"),
    tool: Optional[str] = typer.Option(None, "-t", "--tool", help="Tool to use: opencode, kilo, or auto (default)"),
    yes: bool = typer.Option(False, "-y", "--yes", help="Skip confirmation"),
    gg: bool = typer.Option(False, "--gg", help="Full trust mode: research and build from scratch"),
    plan: bool = typer.Option(False, "--plan", help="Show plan only, don't execute"),
) -> int:
    """Run autonomous improvement sessions.
    
    Default: Improve existing project. Creates BLUEPRINT.md/.opencode-autopilot/HEARTBEAT/ if missing.
    
    Use --gg for full trust mode: research online and build from scratch.
    
    Examples:
      opencode-autopilot run "focus on UI improvements"
      opencode-autopilot run --gg "build a calculator"
      opencode-autopilot run --plan "add dark mode support"
    """
    if not check_prerequisites():
        return 1
    
    # Validate tool option
    preferred_tool = None
    if tool:
        tool_lower = tool.lower()
        if tool_lower in ("auto", "automatic"):
            preferred_tool = None  # Use default behavior
        elif tool_lower in ("opencode", "kilo", "kilocode"):
            preferred_tool = "kilo" if tool_lower in ("kilo", "kilocode") else "opencode"
        else:
            console.print(f"[red]Error:[/red] Invalid tool '{tool}'. Use: opencode, kilo, or auto")
            return 1
    
    project_dir = get_project_dir(project)
    cfg = config.load_config(project_dir)
    state = detector.detect_project_state(project_dir)
    
    # Use tool from config if not specified on command line
    if preferred_tool is None and cfg.tool:
        preferred_tool = cfg.tool
    
    # Determine mode: gg mode or regular mode
    is_gg = gg or directive
    
    # Build options
    options = RunOptions(
        sessions=sessions if sessions is not None else (cfg.sessions or 10),
        interval=interval if interval is not None else (cfg.interval or 30),
        resume=resume,
        model=model or cfg.model or "opencode/big-pickle",
        agent="autonomous",
        preferred_tool=preferred_tool,
        directive=directive,
    )
    
    # Show plan and exit if --plan is specified
    if plan:
        return show_plan(project_dir, state, options, is_gg)
    
    if is_gg:
        if state.state in (detector.ProjectState.ACTIVE, detector.ProjectState.COMPLETED):
            console.print("[yellow]Warning: Existing project found.[/yellow]")
            if not yes:
                if not ask_yes("Start fresh and overwrite?", default=False):
                    console.print("[yellow]Cancelled.[/yellow]")
                    return 0
        
        return 0 if run_gg_mode(project_dir, directive, options, log_callback=log) else 1
    
    else:
        if state.state == detector.ProjectState.EMPTY:
            console.print("[red]No project found.[/red]")
            console.print("")
            console.print("Options:")
            console.print("  1. Add a README.md or source files for guidance, then run again")
            console.print("  2. Run with --gg to let the agent research and build from scratch")
            console.print("  3. Provide a directive to start building: opencode-autopilot run \"build a calculator\"")
            console.print("")
            console.print("Example: opencode-autopilot run --gg \"build a todo app\"")
            return 1
        
        return 0 if run(project_dir, options, log_callback=log) else 1


@app.command(name="config")
def config_cmd(
    project: Optional[str] = typer.Option(None, "-p", "--project", help="Project directory"),
    model: Optional[str] = typer.Option(None, "-m", "--model", help="Default model"),
    tool: Optional[str] = typer.Option(None, "-t", "--tool", help="Default tool: opencode, kilo, or auto"),
    sessions: Optional[int] = typer.Option(None, "-s", "--sessions", help="Default sessions"),
    interval: Optional[int] = typer.Option(None, "-i", "--interval", help="Default interval"),
    global_scope: bool = typer.Option(False, "-g", "--global", help="Global config"),
    show: bool = typer.Option(False, "--show", help="Show current config"),
) -> int:
    """Set persistent defaults."""
    # Validate tool if provided
    tool_value = None
    if tool:
        tool_lower = tool.lower()
        if tool_lower in ("auto", "automatic"):
            tool_value = None  # Clear tool preference
        elif tool_lower in ("opencode", "kilo", "kilocode"):
            tool_value = "kilo" if tool_lower in ("kilo", "kilocode") else "opencode"
        else:
            console.print(f"[red]Error:[/red] Invalid tool '{tool}'. Use: opencode, kilo, or auto")
            return 1
    
    project_dir = get_project_dir(project)
    
    if show:
        cfg = config.show_config(project_dir)
        console.print("[cyan]Config:[/cyan]")
        console.print(f"  Global: {cfg['global'] or '(none)'}")
        console.print(f"  Project: {cfg['local'] or '(none)'}")
        console.print(f"  Effective: {cfg['effective'] or '(defaults)'}")
        return 0
    
    updates = config.AutopilotConfig(model=model, sessions=sessions, interval=interval, tool=tool_value)
    
    if not (updates.model or updates.sessions or updates.interval or updates.tool is not None):
        console.print("[yellow]Nothing to update. Use --show or set an option.[/yellow]")
        return 0
    
    config.save_config(project_dir, updates, global_scope)
    scope = "global" if global_scope else "project"
    console.print(f"[green]Saved to {scope} config.[/green]")
    return 0


@app.callback(invoke_without_command=True)
def app_main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "-v", "--version", is_eager=True, help="Show version"),
    plan: bool = typer.Option(False, "--plan", is_eager=True, help="Show plan only"),
) -> None:
    """Autonomous overnight engineer for OpenCode projects.
    
    Shortcuts:
      opencode-autopilot "build a calculator"     -> opencode-autopilot run "build a calculator"
      opencode-autopilot --plan                    -> show plan for current project
    """
    if version:
        console.print(f"opencode-autopilot {__version__}")
        raise typer.Exit()
    
    if plan:
        # Invoke run_cmd with plan=True
        from .runner import RunOptions
        project_dir = Path.cwd()
        state = detector.detect_project_state(project_dir)
        options = RunOptions()
        show_plan(project_dir, state, options, False)
        raise typer.Exit()


if __name__ == "__main__":
    cli_main()
