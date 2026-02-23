# Development Notes

## Package Managers

### Python (Backend)
Use **uv** for all Python package management:
```bash
# Install dependencies
uv pip install -r requirements.txt

# Install in editable mode
uv pip install -e .

# Create virtual environment
uv venv

# Build wheel
uv pip build
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
# Build and install Python package
uv pip install -e . --force-reinstall

# Run CLI
opencode-autopilot -v
opencode-autopilot --help
opencode-autopilot run "build a calculator"
```

## Notes
- Python venv is at `.venv/`
- Use `uv pip` instead of `pip` directly
- Windows: Executable is at `.venv/Scripts/opencode-autopilot.exe`
