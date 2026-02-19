from __future__ import annotations

from pathlib import Path
from jinja2 import Template


def get_prompts_dir() -> Path:
    return Path(__file__).parent / "prompts"


def render_prompt(name: str, **kwargs) -> str:
    """Load and render a prompt template with variables."""
    prompt_path = get_prompts_dir() / f"{name}.j2"
    template = Template(prompt_path.read_text())
    return template.render(**kwargs)


def gg_research_prompt(topic: str | None, date: str) -> str:
    topic_line = (
        f'The user has offered this loose idea: "{topic}". Treat it as a nudge, not a specification. '
        "If your research reveals a more interesting angle, take it."
        if topic
        else "The user has given you no direction. You have complete creative freedom. Surprise them."
    )
    return render_prompt("gg_research", topic_line=topic_line, date=date)


def gg_blueprint_prompt(run: int, total: int, date: str) -> str:
    return render_prompt(
        "gg_blueprint",
        run=run,
        total=total,
        date=date,
    )


def blueprint_prompt(run: int, total: int, date: str) -> str:
    return render_prompt(
        "blueprint",
        run=run,
        total=total,
        date=date,
    )


def session_prompt(run: int, total: int) -> str:
    return render_prompt(
        "session",
        run=run,
        total=total,
        remaining=total - run,
    )


def final_session_prompt(run: int, total: int) -> str:
    return render_prompt(
        "final_session",
        run=run,
        total=total,
    )
