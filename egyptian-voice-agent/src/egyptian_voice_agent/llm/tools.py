"""Tool schemas + dispatcher.

Each tool has:
- a pydantic model for strict argument validation
- an Anthropic tool schema (for the Messages API `tools` field)
- an async handler that performs the side effect and returns a short ar-EG
  confirmation string the LLM can read back to the caller.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from egyptian_voice_agent.config import settings
from egyptian_voice_agent.integrations import crm as crm_pkg
from egyptian_voice_agent.integrations.telemetry import record_tool_call


# ── Schemas ──────────────────────────────────────────────────────────────────


class LogLead(BaseModel):
    full_name: str
    phone_e164: str = Field(pattern=r"^\+[1-9]\d{6,14}$")
    budget_egp: int | None = None
    authority: Literal["decision_maker", "influencer", "gatekeeper", "unknown"] = "unknown"
    need_summary_ar: str
    timeline: Literal["immediate", "1_month", "3_months", "exploring"] = "exploring"
    notes: str | None = None


class BookCallback(BaseModel):
    requested_at_iso_africa_cairo: str
    channel: Literal["phone", "whatsapp"] = "phone"


class TransferToHuman(BaseModel):
    reason: str
    queue: Literal["sales", "support"] = "sales"


class EndCall(BaseModel):
    outcome: Literal["qualified", "not_qualified", "callback", "transferred", "no_answer"]
    summary_ar: str


# ── Anthropic tool definitions ───────────────────────────────────────────────

TOOLS: list[dict[str, Any]] = [
    {
        "name": "log_lead",
        "description": (
            "Log a qualified lead to the CRM. Call this after collecting BANT "
            "(need, budget, authority, timeline) from the caller."
        ),
        "input_schema": LogLead.model_json_schema(),
    },
    {
        "name": "book_callback",
        "description": (
            "Book a follow-up call with the lead. Use when caller prefers to be called back."
        ),
        "input_schema": BookCallback.model_json_schema(),
    },
    {
        "name": "transfer_to_human",
        "description": (
            "Transfer the active call to a human agent. Use when caller explicitly asks "
            "for a human or when the conversation exceeds the agent's ability."
        ),
        "input_schema": TransferToHuman.model_json_schema(),
    },
    {
        "name": "end_call",
        "description": (
            "End the call gracefully with a brief Egyptian-Arabic farewell. "
            "Use when the caller is done or not qualified."
        ),
        "input_schema": EndCall.model_json_schema(),
    },
]


# ── Dispatch ─────────────────────────────────────────────────────────────────


async def dispatch(
    name: str,
    arguments: dict[str, Any],
    *,
    call_sid: str,
    caller_phone: str | None = None,
) -> dict[str, Any]:
    """Validate + execute a tool call. Returns a dict with status + ar-EG reply."""
    try:
        if name == "log_lead":
            args = LogLead(**arguments)
            await crm_pkg.get_sink().append_lead(args, call_sid=call_sid)
            reply = "تمام، سجّلت بياناتك وهيتواصل معاك فريق المبيعات قريب."
        elif name == "book_callback":
            args = BookCallback(**arguments)
            await crm_pkg.get_sink().append_callback(
                args, call_sid=call_sid, caller_phone=caller_phone
            )
            reply = "اتفقنا، هنتصل بحضرتك في الميعاد ده."
        elif name == "transfer_to_human":
            args = TransferToHuman(**arguments)
            reply = "لحظة واحدة، بحوّلك لزميلي دلوقتي."
        elif name == "end_call":
            args = EndCall(**arguments)
            reply = "شكراً لوقتك، يوم سعيد."
        else:
            return {"ok": False, "reply_ar": "", "error": f"unknown tool: {name}"}

        record_tool_call(call_sid=call_sid, tool=name, arguments=args.model_dump())
        return {"ok": True, "reply_ar": reply, "tool": name, "arguments": args.model_dump()}

    except ValidationError as e:
        return {
            "ok": False,
            "reply_ar": "معلش، فيه معلومة ناقصة، ممكن تعيد تاني؟",
            "error": str(e),
        }


__all__ = [
    "TOOLS",
    "LogLead",
    "BookCallback",
    "TransferToHuman",
    "EndCall",
    "dispatch",
]
