---
description: Safe commit workflow with verification
---

# Commit Skill

A disciplined approach to committing changes.

## Before Committing

1. **Run the verify skill** - Ensure tests pass and code is clean
2. **Review your changes** - `git diff` to see what you're committing
3. **Stage carefully** - Don't blindly `git add .`

## Commit Process

### 1. Check What Changed

```bash
# See changed files
git status

# See the actual changes
git diff
```

### 2. Stage Thoughtfully

```bash
# Stage specific files (preferred)
git add src/specific_file.py

# Or stage interactively
git add -p
```

### 3. Write a Good Commit Message

Format:
```
<type>: <brief description>

<optional longer explanation>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code change without behavior change
- `docs`: Documentation only
- `test`: Adding/updating tests
- `chore`: Maintenance, dependencies

Examples:
```
feat: add user preference persistence
fix: resolve login redirect loop
refactor: simplify config loading logic
docs: update README with new CLI flags
```

### 4. Commit

```bash
git commit -m "type: description"
```

### 5. Verify the Commit

```bash
# See what you just committed
git show --stat HEAD

# Make sure tests still pass
# (run verify skill again if unsure)
```

## Rules

- Never commit broken code
- One logical change per commit
- Write clear, descriptive messages
- If tests fail, fix before committing
- Don't commit secrets, credentials, or .env files

## If Something Goes Wrong

```bash
# Undo last commit (keep changes)
git reset HEAD~1

# Amend last commit message (before pushing)
git commit --amend

# Discard uncommitted changes to a file
git checkout -- <file>
```
