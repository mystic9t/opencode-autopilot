from __future__ import annotations

import shutil
from pathlib import Path


def ensure_autopilot_dirs(project_dir: Path) -> None:
    """Ensure .opencode-autopilot directory structure exists."""
    autopilot_dir = project_dir / ".opencode-autopilot"
    heartbeat_dir = autopilot_dir / "HEARTBEAT"
    heartbeat_dir.mkdir(parents=True, exist_ok=True)


def ensure_scaffolded(
    project_dir: str | Path,
    include_readme: bool = False,
) -> bool:
    """Idempotent scaffold: creates .opencode/, .opencode-autopilot/, skills, HEARTBEAT if missing.
    
    Returns True if this is the first time scaffolding (files were created),
    False if already scaffolded.
    """
    from . import get_autopilot_dir, get_templates_dir
    project_dir = Path(project_dir)
    templates_dir = get_templates_dir()
    autopilot_dir = get_autopilot_dir(project_dir)
    
    created_something = False

    # Ensure .opencode-autopilot directory structure exists
    ensure_autopilot_dirs(project_dir)

    # .opencode/agents/
    agents_to_copy = [
        "autonomous.md",
        "security-review.md",
        "code-review.md",  # Added code review agent
    ]
    
    agents_dir = project_dir / ".opencode" / "agents"
    for agent in agents_to_copy:
        src = templates_dir / "agents" / agent
        dst = agents_dir / agent
        if src.exists() and not dst.exists():
            shutil.copy(src, dst)
            created_something = True

    # .opencode/skills/
    skills_to_copy = [
        "research.md",
        "security-review.md",
        "blueprint.md",
        "refactor.md",
        "self-review.md",
        "verify.md",
        "commit.md",
        "code-review.md",  # Added code review skill
    ]
    
    skills_dir = project_dir / ".opencode" / "skills"
    for skill in skills_to_copy:
        src = templates_dir / "skills" / skill
        dst = skills_dir / skill
        if src.exists() and not dst.exists():
            shutil.copy(src, dst)
            created_something = True

    # .opencode-autopilot/HEARTBEAT/ - this is now handled by ensure_autopilot_dirs()

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
            created_something = True
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