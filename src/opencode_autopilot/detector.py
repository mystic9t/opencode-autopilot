from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ProjectState(Enum):
    EMPTY = "empty"  # No files, fresh start
    HAS_CODE_NO_BLUEPRINT = "has_code_no_blueprint"  # Existing project, no autopilot
    BLUEPRINT_ONLY = "blueprint_only"  # Blueprint written manually or orphaned
    ACTIVE = "active"  # Blueprint + HEARTBEAT exists, mid-cycle
    COMPLETED = "completed"  # DEPLOY_GUIDE.md exists


# Extensions that indicate source code (not text files)
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".rb", ".php", ".swift",
    ".kt", ".scala", ".vue", ".svelte", ".html", ".css", ".scss",
    ".sass", ".less", ".json", ".yaml", ".yml", ".toml", ".xml",
    ".sql", ".sh", ".bash", ".zsh", ".ps1", ".psm1",
}

# Directories/files to ignore when scanning
IGNORED_PATHS = {
    ".git",
    ".gitignore",
    ".autopilot.json",
    ".opencode",
    ".opencode-autopilot",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".next",
    ".nuxt",
}


@dataclass
class DetectionResult:
    state: ProjectState
    has_blueprint: bool
    has_heartbeat: bool
    has_deploy_guide: bool
    has_source_code: bool
    has_text_only: bool


def is_source_file(path: Path) -> bool:
    """Check if a file is a source code file (not just text)."""
    if path.is_dir():
        return False
    suffix = path.suffix.lower()
    return suffix in CODE_EXTENSIONS


def scan_directory(project_dir: Path) -> dict:
    """Scan directory and return basic info about what's there."""
    project_dir = Path(project_dir)
    
    has_blueprint = (project_dir / "BLUEPRINT.md").exists()
    
    # Check both old HEARTBEAT and new .opencode-autopilot/HEARTBEAT locations
    old_heartbeat = project_dir / "HEARTBEAT"
    new_heartbeat = project_dir / ".opencode-autopilot" / "HEARTBEAT"
    has_heartbeat_dir = old_heartbeat.is_dir() or new_heartbeat.is_dir()
    
    # Prefer new location, fall back to old
    active_heartbeat = new_heartbeat if new_heartbeat.is_dir() else old_heartbeat
    has_deploy_guide = (active_heartbeat / "DEPLOY_GUIDE.md").exists()
    
    files = []
    for item in project_dir.iterdir():
        name = item.name
        # Skip hidden files and ignored directories
        if name.startswith("."):
            if name not in (".gitignore", ".autopilot.json"):
                continue
        if name in IGNORED_PATHS:
            continue
        
        if item.is_file():
            files.append(item)
    
    # Check if any source code files exist
    has_source_code = any(is_source_file(f) for f in files)
    
    # Check if only text files exist (.md, .txt)
    text_extensions = {".md", ".txt"}
    has_text_only = (
        all(f.suffix.lower() in text_extensions for f in files) 
        if files else False
    )
    
    return {
        "has_blueprint": has_blueprint,
        "has_heartbeat": has_heartbeat_dir,
        "has_deploy_guide": has_deploy_guide,
        "has_source_code": has_source_code,
        "has_text_only": has_text_only,
        "file_count": len(files),
    }


def detect_project_state(project_dir: str | Path) -> DetectionResult:
    """Detect the current state of the project.
    
    Returns a DetectionResult with the state and details.
    """
    project_dir = Path(project_dir).resolve()
    
    info = scan_directory(project_dir)
    
    # Determine state based on what we found
    if info["has_blueprint"] and info["has_heartbeat"]:
        if info["has_deploy_guide"]:
            state = ProjectState.COMPLETED
        else:
            state = ProjectState.ACTIVE
    elif info["has_blueprint"] and not info["has_heartbeat"]:
        state = ProjectState.BLUEPRINT_ONLY
    elif info["has_source_code"]:
        state = ProjectState.HAS_CODE_NO_BLUEPRINT
    elif info["file_count"] == 0:
        state = ProjectState.EMPTY
    else:
        # Has files but no source code (text files only)
        state = ProjectState.HAS_CODE_NO_BLUEPRINT
    
    return DetectionResult(
        state=state,
        has_blueprint=info["has_blueprint"],
        has_heartbeat=info["has_heartbeat"],
        has_deploy_guide=info["has_deploy_guide"],
        has_source_code=info["has_source_code"],
        has_text_only=info["has_text_only"],
    )


def get_session_count(heartbeat_dir: Path) -> int:
    """Get the number of completed sessions from HEARTBEAT/."""
    if not heartbeat_dir.is_dir():
        return 0
    
    # Count session files (001.md, 002.md, etc.)
    sessions = list(heartbeat_dir.glob("[0-9][0-9][0-9].md"))
    return len([s for s in sessions if s.stem.isdigit()])
