from __future__ import annotations

import shutil
from pathlib import Path



def get_templates_dir() -> Path:
    return Path(__file__).parent / "templates"


def get_autopilot_dir(project_dir: Path) -> Path:
    """Get the .opencode-autopilot directory for project metadata."""
    return project_dir / ".opencode-autopilot"


def ensure_scaffolded(
    project_dir: str | Path,
    silent: bool = True,
    include_readme: bool = False,
) -> bool:
    """Idempotent scaffold: creates .opencode/, .opencode-autopilot/, skills, HEARTBEAT if missing.
    
    Returns True if this is the first time scaffolding (files were created),
    False if already scaffolded.
    """
    project_dir = Path(project_dir)
    templates_dir = get_templates_dir()
    autopilot_dir = get_autopilot_dir(project_dir)
    
    created_something = False

    # .opencode/agents/autonomous.md
    agents_dir = project_dir / ".opencode" / "agents"
    if not agents_dir.exists():
        agents_dir.mkdir(parents=True, exist_ok=True)
        created_something = True
    
    autonomous_agent_src = templates_dir / "agents" / "autonomous.md"
    autonomous_agent_dst = agents_dir / "autonomous.md"
    if autonomous_agent_src.exists() and not autonomous_agent_dst.exists():
        shutil.copy(autonomous_agent_src, autonomous_agent_dst)
        created_something = True
    
    # .opencode/agents/security-review.md
    security_agent_src = templates_dir / "agents" / "security-review.md"
    security_agent_dst = agents_dir / "security-review.md"
    if security_agent_src.exists() and not security_agent_dst.exists():
        shutil.copy(security_agent_src, security_agent_dst)
        created_something = True

    # .opencode/skills/
    skills_dir = project_dir / ".opencode" / "skills"
    skills_to_copy = [
        "research.md",
        "security-review.md",
        "blueprint.md",
        "refactor.md",
        "self-review.md",
        "verify.md",
        "commit.md",
    ]
    
    if not skills_dir.exists():
        skills_dir.mkdir(parents=True, exist_ok=True)
        created_something = True
    
    for skill in skills_to_copy:
        src = templates_dir / "skills" / skill
        dst = skills_dir / skill
        if src.exists() and not dst.exists():
            shutil.copy(src, dst)
            created_something = True

    # .opencode-autopilot/HEARTBEAT/
    heartbeat_dir = autopilot_dir / "HEARTBEAT"
    if not heartbeat_dir.exists():
        heartbeat_dir.mkdir(parents=True, exist_ok=True)
        created_something = True

    # .gitignore - add .opencode-autopilot if needed
    gitignore_path = project_dir / ".gitignore"
    ignore_entry = ".opencode-autopilot/"
    if gitignore_path.exists():
        content = gitignore_path.read_text(encoding="utf-8")
        if ignore_entry not in content:
            gitignore_path.write_text(
                content + f"\n# opencode-autopilot\n{ignore_entry}\n",
                encoding="utf-8"
            )
    else:
        gitignore_path.write_text(f"# opencode-autopilot\n{ignore_entry}\n", encoding="utf-8")
        created_something = True

    # README.md template - only if explicitly requested and doesn't exist
    if include_readme:
        readme_path = project_dir / "README.md"
        if not readme_path.exists():
            # We don't have a template in Python version for now
            # Could add one later
            pass

    return created_something
