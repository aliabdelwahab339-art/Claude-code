"""Google Sheets CRM sink (default).

Uses a service-account JSON for auth. Appends one row per lead or callback to the
configured sheet tab.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from functools import lru_cache

import gspread
from google.oauth2.service_account import Credentials

from egyptian_voice_agent.config import settings

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


@lru_cache(maxsize=1)
def _worksheet():
    creds = Credentials.from_service_account_file(
        settings.google_service_account_json, scopes=_SCOPES
    )
    gc = gspread.authorize(creds)
    return gc.open_by_key(settings.google_sheet_id).worksheet(settings.google_sheet_tab)


class SheetsSink:
    async def append_lead(self, lead, *, call_sid: str) -> None:
        row = [
            datetime.now(UTC).isoformat(),
            call_sid,
            "lead",
            lead.full_name,
            lead.phone_e164,
            lead.budget_egp or "",
            lead.authority,
            lead.timeline,
            lead.need_summary_ar,
            lead.notes or "",
        ]
        await asyncio.to_thread(_worksheet().append_row, row, value_input_option="USER_ENTERED")

    async def append_callback(self, callback, *, call_sid: str, caller_phone: str | None) -> None:
        row = [
            datetime.now(UTC).isoformat(),
            call_sid,
            "callback",
            "",
            caller_phone or "",
            "",
            "",
            callback.requested_at_iso_africa_cairo,
            f"channel={callback.channel}",
            "",
        ]
        await asyncio.to_thread(_worksheet().append_row, row, value_input_option="USER_ENTERED")
