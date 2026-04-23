"""Prompt loader with brand-placeholder substitution + Anthropic prompt caching."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from egyptian_voice_agent.config import settings


def _substitute(text: str, extra: dict[str, str] | None = None) -> str:
    out = text.replace("{{brand}}", settings.brand_name).replace(
        "{{agent_name}}", settings.agent_name
    )
    for k, v in (extra or {}).items():
        out = out.replace("{{" + k + "}}", v)
    return out


@lru_cache(maxsize=8)
def _load_raw(name: str) -> str:
    path: Path = settings.prompts_dir / f"{name}.md"
    return path.read_text(encoding="utf-8")


def load(name: str, **placeholders: str) -> str:
    """Load a prompt file by name with brand + extra placeholders filled."""
    return _substitute(_load_raw(name), placeholders)


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


def greeting(
    *,
    direction: str = "inbound",
    lead_name: str | None = None,
    context: str | None = None,
) -> str:
    """Return the first-turn greeting text, tailored to call direction."""
    if direction == "outbound":
        return load(
            "greeting_outbound_ar_eg",
            lead_name=lead_name or "",
            context=context or "",
        )
    return load("greeting_ar_eg")
