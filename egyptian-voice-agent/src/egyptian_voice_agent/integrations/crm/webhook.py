"""Generic webhook CRM sink. POSTs JSON payloads to `CRM_WEBHOOK_URL`."""

from __future__ import annotations

import httpx

from egyptian_voice_agent.config import settings


class WebhookSink:
    async def append_lead(self, lead, *, call_sid: str) -> None:
        payload = {"type": "lead", "call_sid": call_sid, **lead.model_dump()}
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(settings.crm_webhook_url, json=payload)
            r.raise_for_status()

    async def append_callback(self, callback, *, call_sid: str, caller_phone: str | None) -> None:
        payload = {
            "type": "callback",
            "call_sid": call_sid,
            "caller_phone": caller_phone,
            **callback.model_dump(),
        }
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(settings.crm_webhook_url, json=payload)
            r.raise_for_status()
