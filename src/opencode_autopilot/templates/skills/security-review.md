---
description: OWASP-focused security audit
---

# Security Review Skill

Audit the codebase for:

1. **Injection** - SQL, command, template injection in any user input path.
2. **Authentication** - Missing or weak auth on protected routes.
3. **Secrets** - Hardcoded API keys, tokens, or credentials in source or git history.
4. **Dependencies** - Run the package manager audit command. Flag high/critical CVEs.
5. **Data exposure** - API responses returning more than necessary.
6. **CORS and headers** - Misconfigured CORS, missing security headers.
7. **Error handling** - Stack traces or internals leaking to the client.

For each issue:
- Record file, line, severity (critical / high / medium / low).
- Fix critical and high immediately.
- Log medium and low in the heartbeat for future sessions.

Absence of obvious issues means dig deeper, not stop early.
