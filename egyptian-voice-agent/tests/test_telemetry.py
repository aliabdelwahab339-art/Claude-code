"""Telemetry lifecycle + cost estimation."""

from __future__ import annotations

import json

from egyptian_voice_agent.config import settings
from egyptian_voice_agent.integrations import telemetry


def test_cost_estimate_matches_plan(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "telemetry_path", tmp_path / "calls.jsonl")
    stats = telemetry.start_call("CA_1", caller_phone="+201012345678")
    stats.duration_s = 180.0   # 3 min
    stats.stt_seconds = 90.0
    stats.tts_chars = 900
    stats.input_tokens = 3000
    stats.cached_input_tokens = 1500
    stats.output_tokens = 800
    cost = stats.est_cost_usd()
    # Plan target: ~$0.096 per 3-min call. Allow ±25% for rate drift.
    assert 0.07 <= cost <= 0.13


def test_finalize_writes_jsonl(tmp_path, monkeypatch) -> None:
    path = tmp_path / "calls.jsonl"
    monkeypatch.setattr(settings, "telemetry_path", path)
    telemetry.start_call("CA_2", caller_phone="+2010")
    telemetry.record_tool_call("CA_2", "log_lead", {"full_name": "X"})
    record = telemetry.finalize("CA_2", outcome="qualified")
    assert record is not None
    assert record["outcome"] == "qualified"
    assert len(record["tools_fired"]) == 1
    line = path.read_text(encoding="utf-8").strip()
    parsed = json.loads(line)
    assert parsed["call_sid"] == "CA_2"
