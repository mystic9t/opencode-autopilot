# Development Notes

## Package Managers

### Python (Backend)
Use **uv** for all Python package management:
```bash
# Sync environment with pyproject.toml (install/remove packages as needed)
uv sync

# Add a dependency
uv add <package>

# Remove a dependency
uv remove <package>

# Run CLI/app directly
uv run opencode-autopilot --help
uv run opencode-autopilot -v

# Build wheel
uv build

# Install in editable mode (for development)
uv pip install -e .
```

### JavaScript/TypeScript (Frontend)
Use **bun** for all JS/TS package management:
```bash
# Install dependencies
bun install

# Run scripts
bun run <script>

# Build
bun run build
```

## Common Commands

```bash
# Sync environment (recommended - matches pyproject.toml)
uv sync

# Run CLI
uv run opencode-autopilot -v
uv run opencode-autopilot --help
uv run opencode-autopilot run "build a calculator"

# Build and install wheel
uv pip install -e . --force-reinstall
```

## Notes
- Python venv is at `.venv/` (managed by uv)
- Use `uv sync` to keep environment in sync with `pyproject.toml`
- Use `uv add` / `uv remove` instead of `uv pip install/uninstall`
- Use `uv run` instead of activating venv and running python/commands
- Windows: Executable is at `.venv/Scripts/opencode-autopilot.exe` after install
