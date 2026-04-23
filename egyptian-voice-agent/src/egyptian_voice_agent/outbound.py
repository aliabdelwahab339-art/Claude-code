"""Outbound calling: place Twilio calls that connect to our Media Streams pipeline.

The flow:
  1. `place_call(to, lead_name, context)` creates a Twilio call via REST.
  2. Twilio calls us back at `/twilio/outbound-twiml?lead_name=...&context=...`.
  3. Our TwiML returns `<Connect><Stream>` with custom parameters marking the
     call outbound and carrying the lead context.
  4. The pipeline picks up those parameters on the WS `start` event and
     greets the lead accordingly.

A CSV batch dialer (`scripts/outbound_call.py`) wraps this with DNC checks,
Egypt-hours guard, and simple pacing.
"""

from __future__ import annotations

import asyncio
import logging
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

from twilio.rest import Client

from egyptian_voice_agent.config import settings

logger = logging.getLogger(__name__)

# Local calling etiquette: 9 AM – 9 PM Cairo, Saturday–Thursday.
_CAIRO = ZoneInfo("Africa/Cairo")
_CALL_WINDOW_START = time(9, 0)
_CALL_WINDOW_END = time(21, 0)


def _client() -> Client:
    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        raise RuntimeError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set")
    return Client(settings.twilio_account_sid, settings.twilio_auth_token)


def within_calling_hours(now: datetime | None = None) -> bool:
    now = now or datetime.now(_CAIRO)
    if now.tzinfo is None:
        now = now.replace(tzinfo=_CAIRO)
    local = now.astimezone(_CAIRO)
    # Friday is the Egyptian weekend rest day for most consumers.
    if local.weekday() == 4:  # Friday
        return False
    return _CALL_WINDOW_START <= local.time() <= _CALL_WINDOW_END


@dataclass(frozen=True)
class DNC:
    numbers: frozenset[str]

    def __contains__(self, e164: str) -> bool:
        return e164.strip() in self.numbers

    @classmethod
    def load(cls, path: Path | str | None) -> "DNC":
        if not path:
            return cls(numbers=frozenset())
        p = Path(path)
        if not p.exists():
            return cls(numbers=frozenset())
        nums: set[str] = set()
        for line in p.read_text(encoding="utf-8").splitlines():
            n = line.split(",", 1)[0].strip()
            if n and not n.startswith("#"):
                nums.add(n)
        return cls(numbers=frozenset(nums))


def outbound_twiml_url(base: str, *, lead_name: str | None, context: str | None) -> str:
    qs = urllib.parse.urlencode(
        {k: v for k, v in {"lead_name": lead_name, "context": context}.items() if v}
    )
    sep = "&" if "?" in base else "?"
    url = f"{base.rstrip('/')}/twilio/outbound-twiml"
    return f"{url}{sep}{qs}" if qs else url


async def place_call(
    to: str,
    *,
    lead_name: str | None = None,
    context: str | None = None,
    force: bool = False,
) -> str:
    """Place an outbound call. Returns the Twilio call SID.

    - `to` must be E.164 (e.g. +20101...).
    - Respects calling hours unless `force=True`.
    - Caller rejects numbers on the DNC list.
    """
    if not to.startswith("+"):
        raise ValueError(f"phone must be E.164, got: {to!r}")

    dnc = DNC.load(getattr(settings, "dnc_path", None))
    if to in dnc:
        raise PermissionError(f"{to} is on DNC; refusing to dial")

    if not force and not within_calling_hours():
        raise PermissionError(
            "Outside Egyptian calling hours (09:00–21:00 Cairo, Sat–Thu). "
            "Pass force=True to override."
        )

    twiml_url = outbound_twiml_url(
        settings.public_base_url, lead_name=lead_name, context=context
    )
    logger.info("outbound_dial to=%s url=%s", to, twiml_url)

    call = await asyncio.to_thread(
        _client().calls.create,
        to=to,
        from_=settings.twilio_phone_number,
        url=twiml_url,
        # Machine detection so we don't talk to voicemail for 3 minutes.
        machine_detection="DetectMessageEnd",
        machine_detection_timeout=10,
    )
    return call.sid
