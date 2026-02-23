from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


GLOBAL_CONFIG = Path.home() / ".autopilot.json"


@dataclass
class AutopilotConfig:
    model: str | None = None
    agent: str | None = None
    sessions: int | None = None
    interval: int | None = None
    tool: str | None = None  # "opencode", "kilo", or None for auto


def project_config_path(project_dir: str | Path) -> Path:
    return Path(project_dir) / ".autopilot.json"


def load_config(project_dir: str | Path) -> AutopilotConfig:
    project_dir = Path(project_dir)
    global_cfg: dict = {}
    local_cfg: dict = {}

    if GLOBAL_CONFIG.exists():
        try:
            global_cfg = json.loads(GLOBAL_CONFIG.read_text())
        except (json.JSONDecodeError, OSError):
            pass

    local_path = project_config_path(project_dir)
    if local_path.exists():
        try:
            local_cfg = json.loads(local_path.read_text())
        except (json.JSONDecodeError, OSError):
            pass

    merged = {**global_cfg, **local_cfg}
    return AutopilotConfig(
        model=merged.get("model"),
        agent=merged.get("agent"),
        sessions=merged.get("sessions"),
        interval=merged.get("interval"),
        tool=merged.get("tool"),
    )


def save_config(
    project_dir: str | Path,
    updates: AutopilotConfig,
    global_scope: bool = False,
) -> None:
    project_dir = Path(project_dir)
    config_path = GLOBAL_CONFIG if global_scope else project_config_path(project_dir)

    existing: dict = {}
    if config_path.exists():
        try:
            existing = json.loads(config_path.read_text())
        except (json.JSONDecodeError, OSError):
            pass

    if updates.model is not None:
        existing["model"] = updates.model
    if updates.agent is not None:
        existing["agent"] = updates.agent
    if updates.sessions is not None:
        existing["sessions"] = updates.sessions
    if updates.interval is not None:
        existing["interval"] = updates.interval
    if updates.tool is not None:
        existing["tool"] = updates.tool

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(existing, indent=2))


def show_config(project_dir: str | Path) -> dict[str, Any]:
    project_dir = Path(project_dir)

    global_cfg: dict = {}
    if GLOBAL_CONFIG.exists():
        try:
            global_cfg = json.loads(GLOBAL_CONFIG.read_text())
        except (json.JSONDecodeError, OSError):
            pass

    local_cfg: dict = {}
    local_path = project_config_path(project_dir)
    if local_path.exists():
        try:
            local_cfg = json.loads(local_path.read_text())
        except (json.JSONDecodeError, OSError):
            pass

    merged = {**global_cfg, **local_cfg}

    return {
        "global": global_cfg,
        "local": local_cfg,
        "effective": merged,
    }
