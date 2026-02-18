from __future__ import annotations

import subprocess
import shutil
from pathlib import Path


def is_opencode_installed() -> bool:
    """Check if opencode CLI is available."""
    return shutil.which("opencode") is not None


def run_opencode(
    prompt: str,
    project_dir: str | Path,
    model: str = "opencode/big-pickle",
    agent: str = "autonomous",
) -> bool:
    """Run opencode with the given prompt.
    
    Returns True if the command succeeded (exit code 0), False otherwise.
    """
    project_dir = Path(project_dir).resolve()
    
    # Build the command
    cmd = [
        "opencode",
        "run",
        "--agent", agent,
        "--model", model,
        prompt,
    ]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=project_dir,
            check=False,  # Don't raise on non-zero exit
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False
    except Exception:
        return False


def check_opencode_installation() -> tuple[bool, str]:
    """Check opencode installation and return status and message."""
    if is_opencode_installed():
        return True, "opencode is installed"
    
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
