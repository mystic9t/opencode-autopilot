---
description: Safe refactoring checklist
---

# Refactor Skill

Before starting, confirm:

- Is there a concrete problem being solved? If this is purely aesthetic preference, stop.

Checklist:

1. Read every file in scope before touching anything.
2. Make one logical change at a time.
3. After each change, verify every call site of any modified function or type.
4. Run build and type-check after each logical change.
5. Never change behaviour while refactoring structure - one concern at a time.
6. If a refactor cannot be done without changing behaviour, log it as a Settled Decision and stop.

Invalid targets: import ordering, variable renaming without semantic gain, whitespace, comment rewording.
