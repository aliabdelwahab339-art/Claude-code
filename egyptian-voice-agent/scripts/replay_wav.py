"""Replay a prerecorded caller WAV through the STT+LLM layer, no Twilio.

Usage:
    python scripts/replay_wav.py tests/fixtures/ar_eg_greeting.wav

Writes the agent's text reply to stdout and an SSML preview to `out.ssml`.
Useful for debugging prompt/tool behaviour without burning phone minutes.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import httpx

from egyptian_voice_agent.config import settings
from egyptian_voice_agent.dialect.fallbacks import normalize_egyptian
from egyptian_voice_agent.dialect.ssml import build as build_ssml
from egyptian_voice_agent.llm import prompts
from egyptian_voice_agent.llm.client import create_message
from egyptian_voice_agent.llm.tools import TOOLS, dispatch


async def transcribe(wav: Path) -> str:
    url = (
        "https://api.deepgram.com/v1/listen?model=nova-3&language=ar"
        "&punctuate=true&smart_format=true"
    )
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(
            url,
            content=wav.read_bytes(),
            headers={
                "Authorization": f"Token {settings.deepgram_api_key}",
                "Content-Type": "audio/wav",
            },
        )
        r.raise_for_status()
        return r.json()["results"]["channels"][0]["alternatives"][0]["transcript"]


async def reply(user_ar: str) -> dict:
    msg = await create_message(
        model=settings.llm_model,
        max_tokens=400,
        system=prompts.system_prompt_blocks(),
        tools=TOOLS,
        messages=[{"role": "user", "content": user_ar}],
    )
    text_parts = []
    tool_results = []
    for block in msg.content:
        if getattr(block, "type", None) == "text":
            text_parts.append(block.text)
        elif getattr(block, "type", None) == "tool_use":
            tool_results.append(
                await dispatch(
                    block.name, dict(block.input), call_sid="REPLAY", caller_phone=None
                )
            )
    return {
        "text": "".join(text_parts).strip(),
        "tools": tool_results,
        "usage": dict(msg.usage) if msg.usage else None,
    }


async def main(wav_path: Path) -> None:
    raw = await transcribe(wav_path)
    user = normalize_egyptian(raw)
    print(f"[caller] {user}")
    out = await reply(user)
    print(f"[agent]  {out['text']}")
    for t in out["tools"]:
        print(f"[tool]   {t.get('tool')}  ok={t.get('ok')}  reply={t.get('reply_ar')}")
    Path("out.ssml").write_text(build_ssml(out["text"]), encoding="utf-8")
    print("SSML written to out.ssml")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python scripts/replay_wav.py <path/to/caller.wav>")
        sys.exit(2)
    asyncio.run(main(Path(sys.argv[1])))
