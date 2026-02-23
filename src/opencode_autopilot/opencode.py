from __future__ import annotations

import shutil
from pathlib import Path

from .cli_runner import (
    ToolResult,
    detect_available_tools,
    run_with_fallback,
)


def is_opencode_installed() -> bool:
    """Check if opencode CLI is available."""
    return shutil.which("opencode") is not None


def is_kilocode_installed() -> bool:
    """Check if kilocode CLI is available."""
    return shutil.which("kilo") is not None


def check_cli_tools() -> tuple[bool, str]:
    """Check if at least one CLI tool is available."""
    available = detect_available_tools()
    
    if not available:
        return False, """No CLI tools found. Install at least one:

OpenCode (recommended):
  curl -fsSL https://opencode.ai/install | bash

Kilocode (alternative):
  See https://kilocode.ai for installation

Both tools work with this autopilot. If both are installed, OpenCode is preferred.
"""
    
    tools_str = " and ".join(available)
    return True, f"CLI tools available: {tools_str}"


def run_agent(
    prompt: str,
    project_dir: str | Path,
    model: str = "opencode/big-pickle",
    agent: str = "autonomous",
    preferred_tool: str | None = None,
    log_callback=None,
) -> bool:
    """Run agent session using the given prompt.
    
    Uses fallback: if opencode is rate limited, tries kilocode.
    Returns True if the command succeeded, False otherwise.
    
    Args:
        preferred_tool: If specified, try this tool first. Use "opencode" or "kilo".
    """
    result, tool_used, stderr = run_with_fallback(
        prompt=prompt,
        project_dir=project_dir,
        model=model,
        agent=agent,
        preferred_tool=preferred_tool,
        log_callback=log_callback,
    )
    
    return result == ToolResult.SUCCESS


def check_tool_availability() -> tuple[bool, str]:
    """Check tool availability and return status and message."""
    if is_opencode_installed():
        return True, "opencode is installed"
    
    # Check if kilocode is available as fallback
    if is_kilocode_installed():
        return True, "opencode not found, but kilocode is available as fallback"
    
    # Provide helpful installation instructions
    return False, """opencode is not installed or not in PATH.

To install:
  curl -fsSL https://opencode.ai/install | bash

Or use a package manager:
  npm i -g opencode-ai
  brew install anomalyco/tap/opencode
  scoop install opencode

See https://opencode.ai for more options.
"""
