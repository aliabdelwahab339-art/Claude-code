"""Interactive text-only dev loop — type as the caller, watch the agent reply.

No audio, no Twilio. Good for iterating on the system prompt fast.

Usage:
    python scripts/local_call.py
"""

from __future__ import annotations

import asyncio

from egyptian_voice_agent.config import settings
from egyptian_voice_agent.dialect.fallbacks import normalize_egyptian
from egyptian_voice_agent.llm import prompts
from egyptian_voice_agent.llm.client import create_message
from egyptian_voice_agent.llm.tools import TOOLS, dispatch


async def main() -> None:
    history: list[dict] = []
    print(f"محاكي محادثة محلية — {settings.agent_name} ({settings.brand_name})")
    print("اكتب 'خروج' لإنهاء الجلسة.\n")

    while True:
        try:
            user = input("انت: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user or user in {"خروج", "exit", "quit"}:
            break
        history.append({"role": "user", "content": normalize_egyptian(user)})

        msg = await create_message(
            model=settings.llm_model,
            max_tokens=400,
            system=prompts.system_prompt_blocks(),
            tools=TOOLS,
            messages=history,
        )
        agent_text_parts: list[str] = []
        for block in msg.content:
            if getattr(block, "type", None) == "text":
                agent_text_parts.append(block.text)
            elif getattr(block, "type", None) == "tool_use":
                result = await dispatch(
                    block.name, dict(block.input), call_sid="LOCAL", caller_phone=None
                )
                agent_text_parts.append(f"[{block.name}] → {result.get('reply_ar', '')}")
        agent = "\n".join(p for p in agent_text_parts if p).strip()
        print(f"{settings.agent_name}: {agent}\n")
        history.append({"role": "assistant", "content": agent})


if __name__ == "__main__":
    asyncio.run(main())
