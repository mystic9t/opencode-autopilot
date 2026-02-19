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


@dataclass
class RunOptions:
    sessions: int = 10
    interval: int = 30  # minutes
    resume: int = 1
    model: str = "opencode/big-pickle"
    agent: str = "autonomous"


def sleep_seconds(seconds: int) -> None:
    """Sleep for the given number of seconds."""
    time.sleep(seconds)


def run_gg_mode(
    project_dir: str | Path,
    topic: str | None,
    options: RunOptions,
    log_callback: Callable[[str], None] | None = None,
) -> bool:
    """Run gg command - full trust mode.
    
    Session structure:
    - Session 0: Research + write README
    - Session 1: Blueprint
    - Sessions 2-(N+1): Build
    - Session N+2: Security/final
    """
    project_dir = Path(project_dir).resolve()
    
    log = log_callback or (lambda x: None)
    
    total_build_runs = options.sessions + 2  # blueprint + build + security
    
    log("=" * 56)
    log("opencode-autopilot run --gg -- full trust mode")
    if topic:
        log(f"Nudge    : {topic}")
    else:
        log("Nudge    : none -- agent decides everything")
    log(f"Sessions : 1 research + 1 blueprint + {options.sessions} build + 1 security")
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
    
    # Sessions 1-total_build_runs: Blueprint + Build + Security
    for run in range(1, total_build_runs + 1):
        log("=" * 56)
        log(f"SESSION {run} / {total_build_runs} | {ist_now()}")
        log("=" * 56)
        
        blueprint_path = project_dir / "BLUEPRINT.md"
        
        if run == 1:
            prompt = prompts.gg_blueprint_prompt(run, total_build_runs, ist_now())
            
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
        else:
            if run == total_build_runs:
                prompt = prompts.final_session_prompt(run, total_build_runs)
            else:
                prompt = prompts.session_prompt(run, total_build_runs)
            
            run_agent(
                prompt=prompt,
                project_dir=project_dir,
                model=options.model,
                agent=options.agent,
            )
            log(f"Session {run} complete.")
        
        if run < total_build_runs:
            log(f"Waiting {options.interval} minutes...")
            sleep_seconds(options.interval * 60)
    
    log("=" * 56)
    log("gg cycle complete. Check HEARTBEAT/ and see what was built.")
    log("=" * 56)
    return True


def run(
    project_dir: str | Path,
    options: RunOptions,
    log_callback: Callable[[str], None] | None = None,
) -> bool:
    """Run improvement/build loop for existing projects.
    
    Session structure:
    - Session 1: Blueprint (if not exists)
    - Sessions 2-(N+1): Build/Improvement
    - Session N+2: Security/final
    """
    project_dir = Path(project_dir).resolve()
    
    log = log_callback or (lambda x: None)
    
    blueprint_path = project_dir / "BLUEPRINT.md"
    has_blueprint = blueprint_path.exists()
    
    total_runs = options.sessions + 2 if not has_blueprint else options.sessions + 1
    
    log("=" * 56)
    log("opencode-autopilot run")
    log(f"Project  : {project_dir}")
    if has_blueprint:
        log(f"Sessions : {options.sessions} improvement + 1 security = {total_runs} total")
    else:
        log(f"Sessions : 1 blueprint + {options.sessions} build + 1 security = {total_runs} total")
    log(f"Interval : {options.interval} minutes")
    log(f"Model    : {options.model}")
    log("=" * 56)
    
    scaffold.ensure_scaffolded(project_dir, silent=True)
    
    run_num = max(1, options.resume)
    max_retries = 3
    
    while run_num <= total_runs:
        log("=" * 56)
        log(f"RUN {run_num} / {total_runs} | {ist_now()}")
        log("=" * 56)
        
        # Session 1 -- Blueprint (if needed)
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
            
            if run_num < total_runs:
                log(f"Waiting {options.interval} minutes...")
                sleep_seconds(options.interval * 60)
            
            run_num += 1
            continue
        
        # Build or final session
        if run_num == total_runs:
            prompt = prompts.final_session_prompt(run_num, total_runs)
        else:
            prompt = prompts.session_prompt(run_num, total_runs)
        
        run_agent(
            prompt=prompt,
            project_dir=project_dir,
            model=options.model,
            agent=options.agent,
        )
        log(f"Run {run_num} complete.")
        
        if run_num < total_runs:
            log(f"Waiting {options.interval} minutes...")
            sleep_seconds(options.interval * 60)
        
        run_num += 1
    
    log("=" * 56)
    log("Run cycle complete. Review HEARTBEAT/ and BLUEPRINT.md.")
    log("=" * 56)
    return True