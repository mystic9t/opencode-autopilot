---
description: Run tests and linting to verify code quality
---

# Verify Skill

Run this before committing, or when you're unsure if your changes work.

## Python Projects

```bash
# Run linter
ruff check src/

# Run tests
pytest

# Or with uv
uv run pytest

# Check types (if mypy configured)
mypy src/
```

## Node.js Projects

```bash
# Run linter
npm run lint

# Run tests
npm test

# Type check
npm run typecheck
```

## Go Projects

```bash
# Format
go fmt ./...

# Vet
go vet ./...

# Test
go test ./...
```

## Rust Projects

```bash
# Format
cargo fmt

# Lint
cargo clippy

# Test
cargo test
```

## Generic Checks

1. **Build succeeds** - Does the project compile/build?
2. **Tests pass** - Do existing tests still pass?
3. **No regressions** - Did you break anything that was working?

## If Checks Fail

1. Read the error messages carefully
2. Fix the issues before continuing
3. Don't add new code on top of broken code
4. If stuck, document in `.opencode-autopilot/HEARTBEAT/STATE.md` and move to a different task

## Output

After running checks, update `.opencode-autopilot/HEARTBEAT/STATE.md` with the result:
- All checks pass: Note "verified" with timestamp
- Checks fail: Note what's failing and priority to fix
