"""HubSpot CRM sink. Creates a contact + a note per lead."""

from __future__ import annotations

import httpx

from egyptian_voice_agent.config import settings


class HubSpotSink:
    _base = "https://api.hubapi.com"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {settings.hubspot_access_token}",
            "Content-Type": "application/json",
        }

    async def append_lead(self, lead, *, call_sid: str) -> None:
        properties = {
            "firstname": lead.full_name.split(" ", 1)[0],
            "lastname": lead.full_name.split(" ", 1)[1] if " " in lead.full_name else "",
            "phone": lead.phone_e164,
            "lifecyclestage": "lead",
            "hs_lead_status": "NEW",
            "notes_last_contacted": lead.need_summary_ar,
        }
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(
                f"{self._base}/crm/v3/objects/contacts",
                headers=self._headers(),
                json={"properties": properties},
            )
            r.raise_for_status()

    async def append_callback(self, callback, *, call_sid: str, caller_phone: str | None) -> None:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(
                f"{self._base}/crm/v3/objects/tasks",
                headers=self._headers(),
                json={
                    "properties": {
                        "hs_task_subject": f"Callback requested — {caller_phone or 'unknown'}",
                        "hs_task_body": f"Requested at {callback.requested_at_iso_africa_cairo} "
                        f"via {callback.channel} (call {call_sid})",
                        "hs_task_status": "NOT_STARTED",
                        "hs_task_type": "CALL",
                    }
                },
            )
            r.raise_for_status()
