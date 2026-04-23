"""Tool schema + dispatch validation. No network needed."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from pydantic import ValidationError

from egyptian_voice_agent.llm.tools import (
    BookCallback,
    EndCall,
    LogLead,
    TransferToHuman,
    dispatch,
)


def test_log_lead_requires_e164_phone() -> None:
    with pytest.raises(ValidationError):
        LogLead(
            full_name="Ahmed",
            phone_e164="01012345678",  # missing +
            need_summary_ar="عايز استفسار",
        )


def test_log_lead_minimal() -> None:
    lead = LogLead(
        full_name="Ahmed",
        phone_e164="+201012345678",
        need_summary_ar="عايز استفسار عن الخدمة",
    )
    assert lead.authority == "unknown"
    assert lead.timeline == "exploring"


def test_transfer_to_human_queue_enum() -> None:
    with pytest.raises(ValidationError):
        TransferToHuman(reason="angry caller", queue="billing")  # type: ignore[arg-type]


def test_end_call_outcome_enum() -> None:
    with pytest.raises(ValidationError):
        EndCall(outcome="completed", summary_ar="")  # type: ignore[arg-type]


def test_book_callback_basic() -> None:
    cb = BookCallback(requested_at_iso_africa_cairo="2026-04-24T11:00:00+02:00")
    assert cb.channel == "phone"


@pytest.mark.asyncio
async def test_dispatch_unknown_tool_returns_error() -> None:
    result = await dispatch("nonsense", {}, call_sid="CA_TEST")
    assert result["ok"] is False


@pytest.mark.asyncio
async def test_dispatch_log_lead_writes_crm_and_records_tool() -> None:
    sink = AsyncMock()
    with patch(
        "egyptian_voice_agent.integrations.crm.get_sink", return_value=sink
    ):
        result = await dispatch(
            "log_lead",
            {
                "full_name": "Mona",
                "phone_e164": "+201012345678",
                "need_summary_ar": "عايزة استشارة",
            },
            call_sid="CA_TEST",
        )
    assert result["ok"] is True
    assert "تمام" in result["reply_ar"]
    sink.append_lead.assert_awaited()
