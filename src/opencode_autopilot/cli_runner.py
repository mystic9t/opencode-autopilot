from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ToolResult(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"


@dataclass
class ToolConfig:
    command: str
    run_args: list[str]
    default_model: str
    rate_limit_patterns: list[str]


TOOL_CONFIG = {
    "opencode": ToolConfig(
        command="opencode",
        run_args=["run", "--agent", "{agent}", "--model", "{model}", "{prompt}"],
        default_model="opencode/big-pickle",
        rate_limit_patterns=[
            r"insufficient balance",
            r"quota exceeded",
            r"rate limit",
        ],
    ),
    "kilocode": ToolConfig(
        command="kilo",
        run_args=["run", "{prompt}"],
        default_model="minimax/minimax-m2",
        rate_limit_patterns=[
            r"rate limit exceeded",
            r"free tier rate limit",
            r"429",
        ],
    ),
}


def is_tool_installed(tool_name: str) -> bool:
    """Check if a CLI tool is available in PATH."""
    config = TOOL_CONFIG.get(tool_name)
    if not config:
        return False
    return shutil.which(config.command) is not None


def detect_available_tools() -> list[str]:
    """Detect which tools are installed, returns in priority order."""
    available = []
    for tool_name in TOOL_CONFIG:
        if is_tool_installed(tool_name):
            available.append(tool_name)
    return available


def check_rate_limit(stderr: str, tool_name: str) -> bool:
    """Check if stderr indicates a rate limit error."""
    config = TOOL_CONFIG.get(tool_name)
    if not config:
        return False

    for pattern in config.rate_limit_patterns:
        if re.search(pattern, stderr, re.IGNORECASE):
            return True
    return False


def run_tool(
    tool_name: str,
    prompt: str,
    project_dir: str | Path,
    model: str | None = None,
    agent: str = "autonomous",
) -> tuple[ToolResult, str]:
    """Run a CLI tool with the given prompt.

    Returns (result, stderr) where result indicates success/failure/rate_limit.
    """
    config = TOOL_CONFIG.get(tool_name)
    if not config:
        return ToolResult.FAILED, f"Unknown tool: {tool_name}"

    project_dir = Path(project_dir).resolve()
    effective_model = model or config.default_model

    args = []
    for arg in config.run_args:
        arg = arg.replace("{agent}", agent)
        arg = arg.replace("{model}", effective_model)
        arg = arg.replace("{prompt}", prompt)
        args.append(arg)

    cmd = [config.command] + args

    try:
        result = subprocess.run(
            cmd,
            cwd=project_dir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

        stderr = result.stderr or ""

        if result.returncode == 0:
            return ToolResult.SUCCESS, stderr

        if check_rate_limit(stderr, tool_name):
            return ToolResult.RATE_LIMITED, stderr

        return ToolResult.FAILED, stderr

    except FileNotFoundError:
        return ToolResult.FAILED, f"{config.command} not found in PATH"
    except Exception as e:
        return ToolResult.FAILED, str(e)


def run_with_fallback(
    prompt: str,
    project_dir: str | Path,
    model: str | None = None,
    agent: str = "autonomous",
    excluded_tools: list[str] | None = None,
    log_callback=None,
) -> tuple[ToolResult, str, str]:
    """Run with automatic fallback to alternative tool on rate limit.

    Returns (result, tool_used, stderr).
    """
    log = log_callback or (lambda x: None)
    excluded = excluded_tools or []

    available = [t for t in detect_available_tools() if t not in excluded]

    if not available:
        return ToolResult.FAILED, "", "No CLI tools available"

    for tool_name in available:
        log(f"Running with {tool_name}...")
        result, stderr = run_tool(
            tool_name=tool_name,
            prompt=prompt,
            project_dir=project_dir,
            model=model,
            agent=agent,
        )

        if result == ToolResult.SUCCESS:
            return result, tool_name, stderr

        if result == ToolResult.RATE_LIMITED:
            log(f"{tool_name} hit rate limit, trying next tool...")
            continue

        log(f"{tool_name} failed: {stderr[:200]}")
        continue

    return ToolResult.RATE_LIMITED, "", "All tools hit rate limits"
