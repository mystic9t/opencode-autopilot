from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class RateLimitStatus:
    opencode_limited: bool = False
    kilocode_limited: bool = False
    timestamp: str = ""


RATE_LIMIT_FILE = ".rate_limit_status"
PAUSED_FILE = "PAUSED_RATE_LIMIT.md"


def load_rate_limit_status(project_dir: str | Path) -> RateLimitStatus:
    """Load rate limit status from file."""
    project_dir = Path(project_dir)
    status_file = project_dir / ".opencode-autopilot" / "HEARTBEAT" / RATE_LIMIT_FILE
    
    if not status_file.exists():
        return RateLimitStatus()
    
    try:
        content = status_file.read_text(encoding="utf-8")
        lines = content.strip().split("\n")
        status = RateLimitStatus()
        
        for line in lines:
            if line.startswith("opencode="):
                status.opencode_limited = line.split("=")[1].lower() == "true"
            elif line.startswith("kilocode="):
                status.kilocode_limited = line.split("=")[1].lower() == "true"
            elif line.startswith("timestamp="):
                status.timestamp = line.split("=", 1)[1]
        
        return status
    except Exception:
        return RateLimitStatus()


def save_rate_limit_status(
    project_dir: str | Path,
    opencode_limited: bool = False,
    kilocode_limited: bool = False,
) -> None:
    """Save rate limit status to file."""
    project_dir = Path(project_dir)
    heartbeat_dir = project_dir / ".opencode-autopilot" / "HEARTBEAT"
    heartbeat_dir.mkdir(parents=True, exist_ok=True)
    
    status_file = heartbeat_dir / RATE_LIMIT_FILE
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    content = f"opencode={opencode_limited}\nkilocode={kilocode_limited}\ntimestamp={timestamp}\n"
    status_file.write_text(content, encoding="utf-8")


def mark_tool_limited(project_dir: str | Path, tool_name: str) -> None:
    """Mark a specific tool as rate limited."""
    status = load_rate_limit_status(project_dir)
    
    if tool_name == "opencode":
        status.opencode_limited = True
    elif tool_name == "kilocode":
        status.kilocode_limited = True
    
    save_rate_limit_status(
        project_dir,
        opencode_limited=status.opencode_limited,
        kilocode_limited=status.kilocode_limited,
    )


def clear_rate_limit_status(project_dir: str | Path) -> None:
    """Clear rate limit status."""
    project_dir = Path(project_dir)
    status_file = project_dir / ".opencode-autopilot" / "HEARTBEAT" / RATE_LIMIT_FILE
    paused_file = project_dir / ".opencode-autopilot" / "HEARTBEAT" / PAUSED_FILE
    
    if status_file.exists():
        status_file.unlink()
    if paused_file.exists():
        paused_file.unlink()


def is_paused(project_dir: str | Path) -> bool:
    """Check if the run is paused due to rate limits."""
    project_dir = Path(project_dir)
    paused_file = project_dir / ".opencode-autopilot" / "HEARTBEAT" / PAUSED_FILE
    return paused_file.exists()


def write_paused_file(project_dir: str | Path, reason: str = "") -> None:
    """Write a paused marker file."""
    project_dir = Path(project_dir)
    heartbeat_dir = project_dir / ".opencode-autopilot" / "HEARTBEAT"
    heartbeat_dir.mkdir(parents=True, exist_ok=True)
    
    paused_file = heartbeat_dir / PAUSED_FILE
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    content = f"# Rate Limit Pause\n\n**Timestamp:** {timestamp}\n**Reason:** {reason}\n"
    paused_file.write_text(content, encoding="utf-8")


def all_tools_limited(project_dir: str | Path) -> bool:
    """Check if all available tools are rate limited."""
    from .cli_runner import detect_available_tools
    
    status = load_rate_limit_status(project_dir)
    available = detect_available_tools()
    
    if not available:
        return True
    
    for tool in available:
        if tool == "opencode" and not status.opencode_limited:
            return False
        if tool == "kilocode" and not status.kilocode_limited:
            return False
    
    return True
