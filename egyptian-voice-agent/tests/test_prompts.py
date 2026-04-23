"""System prompt loads with brand placeholders substituted."""

from __future__ import annotations

from egyptian_voice_agent.config import settings
from egyptian_voice_agent.llm import prompts


def test_system_prompt_substitutes_brand() -> None:
    prompts.load.cache_clear()
    settings.brand_name = "شركة النور"
    settings.agent_name = "مروة"
    text = prompts.load("system_prompt_ar_eg")
    assert "شركة النور" in text
    assert "مروة" in text
    assert "{{brand}}" not in text
    assert "{{agent_name}}" not in text


def test_system_prompt_is_cache_controlled() -> None:
    prompts.load.cache_clear()
    blocks = prompts.system_prompt_blocks()
    assert blocks[0]["cache_control"] == {"type": "ephemeral"}
    assert blocks[0]["type"] == "text"
    assert len(blocks[0]["text"]) > 500
