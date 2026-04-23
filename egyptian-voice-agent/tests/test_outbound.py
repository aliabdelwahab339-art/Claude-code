"""Outbound call helpers: DNC, hours guard, TwiML builder, greeting variants."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from egyptian_voice_agent.config import settings
from egyptian_voice_agent.integrations.twilio_handler import build_stream_twiml
from egyptian_voice_agent.llm import prompts
from egyptian_voice_agent.outbound import DNC, outbound_twiml_url, within_calling_hours

_CAIRO = ZoneInfo("Africa/Cairo")


def test_dnc_loads_simple_list(tmp_path) -> None:
    p = tmp_path / "dnc.csv"
    p.write_text("+201000000001\n+201000000002,john\n# a comment\n\n", encoding="utf-8")
    dnc = DNC.load(p)
    assert "+201000000001" in dnc
    assert "+201000000002" in dnc
    assert "+201999999999" not in dnc


def test_dnc_empty_when_missing() -> None:
    assert "+201000000001" not in DNC.load(None)
    assert "+201000000001" not in DNC.load("/nonexistent/path.csv")


def test_calling_hours_monday_noon() -> None:
    # Monday 12:00 Cairo
    now = datetime(2026, 4, 20, 12, 0, tzinfo=_CAIRO)
    assert within_calling_hours(now) is True


def test_calling_hours_before_nine() -> None:
    now = datetime(2026, 4, 20, 8, 59, tzinfo=_CAIRO)
    assert within_calling_hours(now) is False


def test_calling_hours_after_nine_pm() -> None:
    now = datetime(2026, 4, 20, 21, 30, tzinfo=_CAIRO)
    assert within_calling_hours(now) is False


def test_calling_hours_friday_is_off() -> None:
    # Friday noon Cairo — rest day.
    now = datetime(2026, 4, 24, 12, 0, tzinfo=_CAIRO)
    assert within_calling_hours(now) is False


def test_outbound_twiml_url_encodes_params() -> None:
    url = outbound_twiml_url(
        "https://app.fly.dev", lead_name="أحمد", context="متابعة"
    )
    assert url.startswith("https://app.fly.dev/twilio/outbound-twiml?")
    assert "lead_name=" in url
    assert "context=" in url


def test_outbound_twiml_url_no_params() -> None:
    url = outbound_twiml_url("https://app.fly.dev", lead_name=None, context=None)
    assert url == "https://app.fly.dev/twilio/outbound-twiml"


def test_build_stream_twiml_inbound_has_direction() -> None:
    xml = build_stream_twiml("wss://a/b", direction="inbound")
    assert "<Stream" in xml
    assert 'name="direction"' in xml
    assert 'value="inbound"' in xml


def test_build_stream_twiml_outbound_includes_lead_name_and_context() -> None:
    xml = build_stream_twiml(
        "wss://a/b", direction="outbound", lead_name="مروة", context="اتصال أول"
    )
    assert 'value="outbound"' in xml
    assert 'name="lead_name"' in xml
    assert 'name="context"' in xml


def test_outbound_greeting_inserts_context() -> None:
    prompts._load_raw.cache_clear()
    settings.brand_name = "Acme"
    settings.agent_name = "سارة"
    text = prompts.greeting(
        direction="outbound", lead_name="أحمد", context="عرض السعر"
    )
    assert "سارة" in text
    assert "Acme" in text
    assert "عرض السعر" in text
    assert "{{" not in text


def test_inbound_greeting_no_context_placeholder() -> None:
    prompts._load_raw.cache_clear()
    text = prompts.greeting(direction="inbound")
    assert "{{" not in text


@pytest.mark.asyncio
async def test_place_call_rejects_dnc(monkeypatch, tmp_path) -> None:
    from egyptian_voice_agent import outbound

    dnc_file = tmp_path / "dnc.csv"
    dnc_file.write_text("+201000000001\n", encoding="utf-8")
    monkeypatch.setattr(settings, "dnc_path", dnc_file)
    with pytest.raises(PermissionError):
        await outbound.place_call("+201000000001", force=True)


@pytest.mark.asyncio
async def test_place_call_rejects_non_e164() -> None:
    from egyptian_voice_agent import outbound

    with pytest.raises(ValueError):
        await outbound.place_call("01012345678", force=True)
