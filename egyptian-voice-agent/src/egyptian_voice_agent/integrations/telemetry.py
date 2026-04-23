"""Per-call telemetry: writes one JSONL record per call.

Used by `scripts/cost_rollup.py` to compute actual $/call and compare to estimates.
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from egyptian_voice_agent.config import settings

_lock = threading.Lock()


# ── Cost rates (USD). Update as pricing changes. ─────────────────────────────
RATES = {
    "twilio_voice_per_min": 0.013,
    "twilio_stream_per_min": 0.004,
    "deepgram_per_min": 0.0077,
    "azure_stt_per_min": 0.0167,
    "claude_haiku_in_per_mtok": 1.0,
    "claude_haiku_out_per_mtok": 5.0,
    "claude_haiku_cached_in_per_mtok": 0.10,
    "azure_tts_per_mchar": 16.0,
    "elevenlabs_flash_per_mchar": 30.0,
}


@dataclass
class CallStats:
    call_sid: str
    started_at: float = field(default_factory=time.time)
    caller_phone: str | None = None
    duration_s: float = 0.0
    stt_provider: str = "deepgram"
    stt_seconds: float = 0.0
    tts_provider: str = "azure"
    tts_chars: int = 0
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    tools_fired: list[dict] = field(default_factory=list)
    outcome: str | None = None

    def est_cost_usd(self) -> float:
        mins = max(self.duration_s, 1.0) / 60.0
        stt_rate = (
            RATES["deepgram_per_min"]
            if self.stt_provider == "deepgram"
            else RATES["azure_stt_per_min"]
        )
        tts_rate = (
            RATES["azure_tts_per_mchar"]
            if self.tts_provider == "azure"
            else RATES["elevenlabs_flash_per_mchar"]
        )
        cost = (
            mins * RATES["twilio_voice_per_min"]
            + mins * RATES["twilio_stream_per_min"]
            + mins * stt_rate
            + (self.input_tokens - self.cached_input_tokens) / 1e6 * RATES["claude_haiku_in_per_mtok"]
            + self.cached_input_tokens / 1e6 * RATES["claude_haiku_cached_in_per_mtok"]
            + self.output_tokens / 1e6 * RATES["claude_haiku_out_per_mtok"]
            + self.tts_chars / 1e6 * tts_rate
        )
        return round(cost, 4)

    def to_record(self) -> dict:
        return {
            "call_sid": self.call_sid,
            "started_at": self.started_at,
            "caller_phone": self.caller_phone,
            "duration_s": round(self.duration_s, 2),
            "stt_provider": self.stt_provider,
            "stt_seconds": round(self.stt_seconds, 2),
            "tts_provider": self.tts_provider,
            "tts_chars": self.tts_chars,
            "input_tokens": self.input_tokens,
            "cached_input_tokens": self.cached_input_tokens,
            "output_tokens": self.output_tokens,
            "tools_fired": self.tools_fired,
            "outcome": self.outcome,
            "est_cost_usd": self.est_cost_usd(),
        }


# ── Live registry of in-flight calls (keyed by call_sid) ────────────────────

_live: dict[str, CallStats] = {}


def start_call(call_sid: str, caller_phone: str | None = None) -> CallStats:
    stats = CallStats(
        call_sid=call_sid,
        caller_phone=caller_phone,
        stt_provider=settings.stt_provider,
        tts_provider=settings.tts_provider,
    )
    _live[call_sid] = stats
    return stats


def get(call_sid: str) -> CallStats | None:
    return _live.get(call_sid)


def record_tool_call(call_sid: str, tool: str, arguments: dict) -> None:
    stats = _live.get(call_sid)
    if stats is None:
        return
    stats.tools_fired.append({"tool": tool, "at": time.time(), "args": arguments})


def finalize(call_sid: str, outcome: str | None = None) -> dict | None:
    stats = _live.pop(call_sid, None)
    if stats is None:
        return None
    stats.duration_s = time.time() - stats.started_at
    if outcome:
        stats.outcome = outcome
    _write(stats.to_record())
    return stats.to_record()


def _write(record: dict) -> None:
    path: Path = settings.telemetry_path
    path.parent.mkdir(parents=True, exist_ok=True)
    with _lock, path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
