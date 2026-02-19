from __future__ import annotations

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape


_env: Environment | None = None


def get_env() -> Environment:
    """Get or create the Jinja2 environment with autoescape enabled."""
    global _env
    if _env is None:
        prompts_dir = Path(__file__).parent / "prompts"
        _env = Environment(
            loader=FileSystemLoader(prompts_dir),
            autoescape=select_autoescape(),
        )
    return _env


def get_prompts_dir() -> Path:
    return Path(__file__).parent / "prompts"


def render_prompt(name: str, **kwargs) -> str:
    """Load and render a prompt template with variables."""
    env = get_env()
    template = env.get_template(f"{name}.j2")
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


def build_session_prompt(run: int, total: int, date: str) -> str:
    return render_prompt(
        "build_session",
        run=run,
        total=total,
        date=date,
        remaining=total - run,
    )


def run_session_prompt(run: int, total: int, date: str) -> str:
    return render_prompt(
        "run_session",
        run=run,
        total=total,
        date=date,
        remaining=total - run,
    )


def final_session_prompt(run: int, total: int, date: str) -> str:
    return render_prompt(
        "final_session",
        run=run,
        total=total,
        date=date,
    )
