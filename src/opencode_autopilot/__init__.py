from __future__ import annotations

from pathlib import Path


__version__ = "0.1.0-beta.3"
__author__ = "mystic9t"


def get_autopilot_dir(project_dir: Path) -> Path:
    """Get the .opencode-autopilot directory for a project."""
    return project_dir / ".opencode-autopilot"


def get_templates_dir() -> Path:
    """Get the templates directory."""
    return Path(__file__).parent / "templates"
