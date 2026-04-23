"""Prompt loader with brand-placeholder substitution + Anthropic prompt caching."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from egyptian_voice_agent.config import settings


def _substitute(text: str) -> str:
    return (
        text.replace("{{brand}}", settings.brand_name)
        .replace("{{agent_name}}", settings.agent_name)
    )


@lru_cache(maxsize=4)
def load(name: str) -> str:
    """Load a prompt file by name (e.g. 'system_prompt_ar_eg') with placeholders filled."""
    path: Path = settings.prompts_dir / f"{name}.md"
    return _substitute(path.read_text(encoding="utf-8"))


def system_prompt_blocks() -> list[dict]:
    """System prompt as cache-marked blocks for the Anthropic Messages API.

    The whole system prompt is static across turns inside a call, so we mark
    it `cache_control: ephemeral` — the second turn onward pays ~10% of the
    input-token cost for these blocks.
    """
    return [
        {
            "type": "text",
            "text": load("system_prompt_ar_eg"),
            "cache_control": {"type": "ephemeral"},
        }
    ]


def greeting() -> str:
    return load("greeting_ar_eg")
