"""CRM sink factory. Selects implementation from `settings.crm_sink`."""

from __future__ import annotations

from functools import lru_cache
from typing import Protocol

from egyptian_voice_agent.config import settings


class CRMSink(Protocol):
    async def append_lead(self, lead, *, call_sid: str) -> None: ...
    async def append_callback(self, callback, *, call_sid: str, caller_phone: str | None) -> None: ...


@lru_cache(maxsize=1)
def get_sink() -> CRMSink:
    if settings.crm_sink == "sheets":
        from egyptian_voice_agent.integrations.crm.sheets import SheetsSink

        return SheetsSink()
    if settings.crm_sink == "hubspot":
        from egyptian_voice_agent.integrations.crm.hubspot import HubSpotSink

        return HubSpotSink()
    if settings.crm_sink == "webhook":
        from egyptian_voice_agent.integrations.crm.webhook import WebhookSink

        return WebhookSink()
    raise ValueError(f"unknown CRM_SINK: {settings.crm_sink}")
