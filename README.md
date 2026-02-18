# opencode-autopilot

> Autonomous overnight engineer for OpenCode projects.

## Why I built this

I'm **mystic9t** — I work a day job and build hobby projects in whatever time I have at night. One of those is [Vibes](https://vibes.mystic9t.fyi), an astrology and wellness web app I genuinely enjoy but rarely have time to iterate on.

I kept seeing people talk about OpenClaw — an autonomous agent loop built on top of Claude Code. It looked powerful, but every time I tried to make sense of it, I hit a wall. The setup was confusing, the derivatives didn't click for me either, and I wanted something that worked without a steep learning curve.

So I did what any developer does: I went down a rabbit hole. I read what other people were doing — the loops, the session triggers, the heartbeat memory patterns — and I stitched together my own version built specifically for OpenCode and its default model, Big Pickle.

The first night I ran it on Vibes, I woke up to **two fully functional new features**, committed and working. They weren't perfect — I ran a dedicated cleanup session — but the core work was done while I slept. That felt like something worth packaging up.

**opencode-autopilot** is the result. A structured way to give OpenCode a persistent memory, a blueprint system, and a session loop so it keeps working instead of stopping after 10 minutes waiting for you.

---

## Roadmap

### Coming in v0.1.0

- **Kilocode support** — Auto-detect and use Kilocode as an alternative to OpenCode
- **Smart tool switching** — Automatically fallback to the other tool when one hits rate limits
- **Rate limit resume** — Pause overnight runs when both tools are rate-limited, auto-resume when limits reset

---

## Commands

| Command | What it does |
| --- | --- |
| `opencode-autopilot` | Smart detect — auto-detects project state and runs appropriate command |
| `opencode-autopilot gg [topic]` | Full trust mode — agent researches, decides what to build, and builds it |
| `opencode-autopilot build` | Build from README — agent builds based on your README |
| `opencode-autopilot run` | Improvement loop — agent improves existing project |
| `opencode-autopilot config` | Set persistent defaults for model/agent |

---

## Requirements

- [OpenCode](https://opencode.ai) installed and in PATH
- Python 3.12+

---

## Installation

```bash
pip install opencode-autopilot
```

Or run directly with uvx:

```bash
uvx opencode-autopilot gg
```

---

## Default model

Defaults to **`opencode/big-pickle`** — OpenCode's built-in free model, available to every OpenCode user with no setup.

Switch models per-run or permanently:

```bash
# Per-run
opencode-autopilot run --model anthropic/claude-sonnet-4-5

# Set project default
opencode-autopilot config --model anthropic/claude-sonnet-4-5

# Set global default (all projects)
opencode-autopilot config --model anthropic/claude-sonnet-4-5 --global

# Check what's active
opencode-autopilot config --show
```

---

## Usage

```bash
# New project — you write the brief, agent builds
opencode-autopilot build

# Existing project — agent improves what's there
opencode-autopilot run

# Full trust — agent researches, decides, and builds with no input from you
opencode-autopilot gg

# Full trust with a loose nudge
opencode-autopilot gg "something for people who read too much"

# Resume an interrupted cycle from session 6
opencode-autopilot build --resume 6

# Fewer sessions, shorter intervals
opencode-autopilot build --sessions 6 --interval 15

# Smart auto-detect (no command)
opencode-autopilot
```

---

## How the memory system works

The agent writes to `HEARTBEAT/` — never committed to git, always local. It tracks:

- What was done each session and the build status
- **Settled Decisions** — things tried and abandoned so it never repeats them
- Paid feature ideas logged separately for you to review
- Plans written during exploration sessions

---

## License

MIT © [mystic9t](https://github.com/mystic9t/opencode-autopilot)
