from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from . import prompts, scaffold
from .opencode import run_agent


def ist_now() -> str:
    """Get current time in IST timezone."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ist_now_dt() -> datetime:
    """Get current datetime in IST timezone."""
    return datetime.now()


def format_duration(seconds: float) -> str:
    """Format duration in a human-readable way."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m"


@dataclass
class RunOptions:
    sessions: int = 10
    interval: int = 30  # minutes
    resume: int = 1
    model: str = "opencode/big-pickle"
    agent: str = "autonomous"


@dataclass
class RunResult:
    """Result of a single run/session."""
    success: bool
    summary: str
    duration_seconds: float
    tool_used: str = ""


def sleep_seconds(seconds: int) -> None:
    """Sleep for the given number of seconds."""
    time.sleep(seconds)


def extract_summary_from_stderr(stderr: str) -> str:
    """Extract a 1-2 line summary from stderr output."""
    if not stderr:
        return "No output"
    
    lines = stderr.strip().split("\n")
    
    # Look for common summary patterns
    for line in lines:
        # Skip very long lines or empty lines
        if len(line) > 200 or not line.strip():
            continue
        # Look for commit-like patterns
        if "commit" in line.lower() or "created" in line.lower() or "fixed" in line.lower():
            return line.strip()[:150]
    
    # Otherwise return the last non-empty line or first line
    for line in reversed(lines):
        if line.strip() and len(line.strip()) < 200:
            return line.strip()[:150]
    
    return lines[0].strip()[:150] if lines else "Run complete"


def run_session(
    prompt: str,
    project_dir: Path,
    model: str,
    agent: str,
    log_callback: Callable[[str], None] | None = None,
) -> RunResult:
    """Run a single session and return the result with timing."""
    log = log_callback or (lambda x: None)
    
    start_time = ist_now_dt()
    
    log(f"Starting at {ist_now()}...")
    
    success = run_agent(
        prompt=prompt,
        project_dir=project_dir,
        model=model,
        agent=agent,
        log_callback=log_callback,
    )
    
    end_time = ist_now_dt()
    duration = (end_time - start_time).total_seconds()
    
    # Get the summary from the last log (we need to capture this differently)
    # For now, we'll extract from what we can observe
    summary = "Session complete"  # This would need to be captured from the agent output
    
    return RunResult(
        success=success,
        summary=summary,
        duration_seconds=duration,
    )


def run_with_timeout_check(
    prompt: str,
    project_dir: Path,
    model: str,
    agent: str,
    max_runtime_seconds: int = 600,  # 10 minutes default
    log_callback: Callable[[str], None] | None = None,
) -> tuple[RunResult, bool]:
    """Run a session with timeout check for stuck detection.
    
    Returns (result, was_timeout) - was_timeout=True if session appeared stuck.
    """
    import threading
    
    log = log_callback or (lambda x: None)
    
    # Track if we hit timeout
    timeout_hit = threading.Event()
    
    def run_with_timeout():
        nonlocal result
        result = RunResult(success=False, summary="", duration_seconds=0)
        
        start_time = time.time()
        log(f"Starting at {ist_now()}...")
        
        success = run_agent(
            prompt=prompt,
            project_dir=project_dir,
            model=model,
            agent=agent,
            log_callback=log_callback,
        )
        
        duration = time.time() - start_time
        
        result = RunResult(
            success=success,
            summary="Session complete",
            duration_seconds=duration,
        )
    
    result = RunResult(success=False, summary="", duration_seconds=0)
    
    thread = threading.Thread(target=run_with_timeout)
    thread.daemon = True
    thread.start()
    
    # Wait for thread with timeout
    thread.join(timeout=max_runtime_seconds)
    
    if thread.is_alive():
        # Thread is still running - likely stuck waiting for input
        timeout_hit.set()
        log(f"WARNING: Session timed out after {max_runtime_seconds}s - appears stuck")
        log("Session will be marked as complete and next session will continue")
    
    return result, timeout_hit.is_set()


def calculate_wait_time(run_duration_seconds: float, interval_minutes: int) -> int:
    """Calculate wait time based on run duration.
    
    If run took < interval minutes, wait (interval - run_time).
    If run took >= interval minutes, wait full interval.
    """
    interval_seconds = interval_minutes * 60
    
    if run_duration_seconds < interval_seconds:
        wait_seconds = int(interval_seconds - run_duration_seconds)
    else:
        wait_seconds = interval_seconds
    
    # Return in seconds for sleep function
    return wait_seconds


def run_gg_mode(
    project_dir: str | Path,
    topic: str | None,
    options: RunOptions,
    log_callback: Callable[[str], None] | None = None,
) -> bool:
    """Run gg command - full trust mode.
    
    Session structure:
    - Session 0: Research + write README
    - Session 1: Blueprint + Start building
    - Sessions 2-(N): Continue building
    - Session N+1: Security/final
    """
    project_dir = Path(project_dir).resolve()
    
    log = log_callback or (lambda x: None)
    
    # Calculate total runs: 1 research + 1 blueprint-build + (N-1) builds + 1 security
    total_runs = options.sessions + 2
    
    log("=" * 56)
    log("opencode-autopilot run --gg -- full trust mode")
    if topic:
        log(f"Nudge    : {topic}")
    else:
        log("Nudge    : none -- agent decides everything")
    log(f"Sessions : 1 research + 1 blueprint+build + {options.sessions - 1} build + 1 security")
    log(f"Interval : {options.interval} minutes")
    log(f"Model    : {options.model}")
    log("=" * 56)
    
    scaffold.ensure_scaffolded(project_dir, silent=True)
    
    # Session 0: Research
    log("=" * 56)
    log(f"SESSION 0 -- Research | {ist_now()}")
    log("Agent is going online to pick something to build...")
    log("=" * 56)
    
    research_prompt = prompts.gg_research_prompt(topic, ist_now())
    readme_path = project_dir / "README.md"
    
    if readme_path.exists():
        readme_path.unlink()
    
    readme_done = False
    retry_count = 0
    max_retries = 3
    
    while not readme_done and retry_count < max_retries:
        run_agent(
            prompt=research_prompt,
            project_dir=project_dir,
            model=options.model,
            agent=options.agent,
        )
        
        if readme_path.exists():
            readme_done = True
            log("README.md confirmed.")
        else:
            retry_count += 1
            log(f"README.md not found after research. Retrying in 60 seconds... (attempt {retry_count}/{max_retries})")
            sleep_seconds(60)
    
    if not readme_done:
        log("ERROR: Failed to create README.md after multiple attempts.")
        return False
    
    try:
        readme_content = readme_path.read_text(encoding="utf-8")
        preview = "\n".join(readme_content.split("\n")[:12])
        log("=" * 56)
        log("The agent has decided to build:")
        log("")
        log(preview)
        log("")
        log("=" * 56)
    except Exception:
        pass
    
    log(f"Waiting {options.interval} minutes before blueprint session...")
    sleep_seconds(options.interval * 60)
    
    # Sessions 1-total_runs: Blueprint+Build (run 1) + Build (runs 2 to N-1) + Security (run N)
    for run in range(1, total_runs + 1):
        run_start_time = ist_now_dt()
        log("=" * 56)
        log(f"SESSION {run} / {total_runs} | {ist_now()}")
        log("=" * 56)
        
        blueprint_path = project_dir / "BLUEPRINT.md"
        
        if run == 1:
            # Blueprint session - generates blueprint and starts building
            prompt = prompts.gg_blueprint_prompt(run, total_runs, ist_now())
            
            blueprint_done = False
            retry_count = 0
            
            while not blueprint_done and retry_count < max_retries:
                run_agent(
                    prompt=prompt,
                    project_dir=project_dir,
                    model=options.model,
                    agent=options.agent,
                )
                
                if blueprint_path.exists():
                    blueprint_done = True
                    log("BLUEPRINT.md confirmed.")
                else:
                    retry_count += 1
                    log(f"BLUEPRINT.md not found. Retrying in 60 seconds... (attempt {retry_count}/{max_retries})")
                    sleep_seconds(60)
            
            if not blueprint_done:
                log("ERROR: Failed to create BLUEPRINT.md after multiple attempts.")
                return False
            
            # After blueprint, we continue to build in this same session
            # The prompt includes instructions to start building
            
        elif run == total_runs:
            # Security/final session
            prompt = prompts.final_session_prompt(run, total_runs)
            
            run_agent(
                prompt=prompt,
                project_dir=project_dir,
                model=options.model,
                agent=options.agent,
            )
            
        else:
            # Regular build session
            prompt = prompts.session_prompt(run, total_runs)
            
            run_agent(
                prompt=prompt,
                project_dir=project_dir,
                model=options.model,
                agent=options.agent,
            )
        
        # Calculate run duration and end time
        run_end_time = ist_now_dt()
        run_duration = (run_end_time - run_start_time).total_seconds()
        run_end_str = run_end_time.strftime("%Y-%m-%d %H:%M:%S")
        
        log(f"Session {run} complete at {run_end_str} ({format_duration(run_duration)})")
        
        # Wait before next session (except after final session)
        if run < total_runs:
            wait_seconds = calculate_wait_time(run_duration, options.interval)
            wait_minutes = wait_seconds // 60
            
            if run_duration < options.interval * 60:
                log(f"Run took {format_duration(run_duration)}, waiting {wait_minutes}m...")
            else:
                log(f"Waiting {options.interval} minutes...")
            
            sleep_seconds(wait_seconds)
    
    log("=" * 56)
    log("gg cycle complete. Check .opencode-autopilot/HEARTBEAT/ and see what was built.")
    log("=" * 56)
    return True


def run(
    project_dir: str | Path,
    options: RunOptions,
    log_callback: Callable[[str], None] | None = None,
) -> bool:
    """Run improvement/build loop for existing projects.
    
    Session structure:
    - Session 1: Blueprint (if not exists) + Start building
    - Sessions 2-(N): Continue building
    - Session N+1: Security/final
    """
    project_dir = Path(project_dir).resolve()
    
    log = log_callback or (lambda x: None)
    
    blueprint_path = project_dir / "BLUEPRINT.md"
    has_blueprint = blueprint_path.exists()
    
    # If blueprint exists: N build sessions + 1 security
    # If no blueprint: 1 blueprint+build + (N-1) builds + 1 security
    if has_blueprint:
        total_runs = options.sessions + 1  # build + security
    else:
        total_runs = options.sessions + 1  # blueprint+build + (N-1) builds + security
    
    log("=" * 56)
    log("opencode-autopilot run")
    log(f"Project  : {project_dir}")
    if has_blueprint:
        log(f"Sessions : {options.sessions} improvement + 1 security = {total_runs} total")
    else:
        log(f"Sessions : 1 blueprint+build + {options.sessions - 1} build + 1 security = {total_runs} total")
    log(f"Interval : {options.interval} minutes")
    log(f"Model    : {options.model}")
    log("=" * 56)
    
    scaffold.ensure_scaffolded(project_dir, silent=True)
    
    run_num = 1
    max_retries = 3
    
    while run_num <= total_runs:
        run_start_time = ist_now_dt()
        
        log("=" * 56)
        log(f"RUN {run_num} / {total_runs} | {ist_now()}")
        log("=" * 56)
        
        # Session 1 -- Blueprint+Build (if no blueprint exists)
        if run_num == 1 and not has_blueprint:
            if blueprint_path.exists():
                log("BLUEPRINT.md exists. Skipping to run 2.")
                run_num = 2
                continue
            
            prompt = prompts.blueprint_prompt(run_num, total_runs, ist_now())
            
            blueprint_done = False
            retry_count = 0
            
            while not blueprint_done and retry_count < max_retries:
                run_agent(
                    prompt=prompt,
                    project_dir=project_dir,
                    model=options.model,
                    agent=options.agent,
                )
                
                if blueprint_path.exists():
                    blueprint_done = True
                    log("BLUEPRINT.md confirmed.")
                else:
                    retry_count += 1
                    log(f"BLUEPRINT.md not found. Retrying in 60 seconds... (attempt {retry_count}/{max_retries})")
                    sleep_seconds(60)
            
            if not blueprint_done:
                log("ERROR: Failed to create BLUEPRINT.md after multiple attempts.")
                return False
            
            # After blueprint, continue to build in this same session
            # The prompt includes building instructions
            
        elif run_num == total_runs:
            # Security/final session
            prompt = prompts.final_session_prompt(run_num, total_runs)
            
            run_agent(
                prompt=prompt,
                project_dir=project_dir,
                model=options.model,
                agent=options.agent,
            )
            
        else:
            # Build session
            prompt = prompts.session_prompt(run_num, total_runs)
            
            run_agent(
                prompt=prompt,
                project_dir=project_dir,
                model=options.model,
                agent=options.agent,
            )
        
        # Calculate run duration and end time
        run_end_time = ist_now_dt()
        run_duration = (run_end_time - run_start_time).total_seconds()
        run_end_str = run_end_time.strftime("%Y-%m-%d %H:%M:%S")
        
        log(f"Run {run_num} complete at {run_end_str} ({format_duration(run_duration)})")
        
        # Wait before next session (except after final session)
        if run_num < total_runs:
            wait_seconds = calculate_wait_time(run_duration, options.interval)
            wait_minutes = wait_seconds // 60
            
            if run_duration < options.interval * 60:
                log(f"Run took {format_duration(run_duration)}, waiting {wait_minutes}m...")
            else:
                log(f"Waiting {options.interval} minutes...")
            
            sleep_seconds(wait_seconds)
        
        run_num += 1
    
    log("=" * 56)
    log("Run cycle complete. Review .opencode-autopilot/HEARTBEAT/ and BLUEPRINT.md.")
    log("=" * 56)
    return True
