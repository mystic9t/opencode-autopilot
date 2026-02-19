---
description: Audit your own changes for quality and simplicity
---

# Self-Review Skill

Use this skill when:
- You've made many changes across multiple sessions
- You're uncertain if your work is valuable
- Before a final or security session
- HEARTBEAT is getting cluttered
- Project feels "done" but you keep adding things

## Process

### 1. List Recent Changes

```bash
# See what commits you've made
git log --oneline -10

# See what's different from main
git diff --stat main

# Count changes
git diff --shortstat main
```

### 2. Evaluate Each Change

For each significant file or commit, ask:
- Does it serve the project's core purpose?
- Is it simpler or more complex than before?
- Would you merge it if you were reviewing someone else's PR?

### 3. Identify Bloat Signals

Watch for:
- Files over 300 lines that could be smaller
- Features not mentioned in README/BLUEPRINT/NEXT.md
- Duplicate or overlapping code
- Unused dependencies
- Comments explaining "why" instead of self-documenting code

### 4. Categorize

**KEEP** - Core features, working code, good tests
**SIMPLIFY** - Over-engineered but valuable
**REMOVE** - Bloat, failed experiments, dead code

### 5. Update HEARTBEAT/STATE.md

```markdown
# Project State

Status: [active / mature / needs-cleanup / blocked]
Last Session: [brief summary]
Next Priority: [what to focus on]
Recent Wins: [what went well]
Concerns: [what to watch]
Needs User Input: [yes/no - if yes, write PLAN_*.md]
```

### 6. Act

If cleanup is needed, do it now rather than adding more.
- Simplify complex files
- Remove dead code
- Consolidate duplicates

## Rules

- Better to simplify now than accumulate debt
- Deleting code is progress
- If you wouldn't merge it, don't keep it
- Quality > Quantity
- A mature project that's stable is success, not failure
