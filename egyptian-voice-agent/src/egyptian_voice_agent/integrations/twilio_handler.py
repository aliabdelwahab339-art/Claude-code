"""Twilio helpers: TwiML generation + request signature validation."""

from __future__ import annotations

from fastapi import HTTPException, Request
from twilio.request_validator import RequestValidator
from twilio.twiml.voice_response import Connect, VoiceResponse

from egyptian_voice_agent.config import settings


def build_stream_twiml(
    stream_url: str,
    *,
    direction: str = "inbound",
    lead_name: str | None = None,
    context: str | None = None,
) -> str:
    """TwiML that connects the call to our Media Streams WebSocket.

    Extra parameters are attached via <Parameter> children; Twilio surfaces
    them on the WS `start` event as `start.customParameters`.
    """
    response = VoiceResponse()
    connect = Connect()
    stream = connect.stream(url=stream_url)
    stream.parameter(name="direction", value=direction)
    if lead_name:
        stream.parameter(name="lead_name", value=lead_name)
    if context:
        stream.parameter(name="context", value=context)
    response.append(connect)
    return str(response)


def build_dial_twiml(to_number: str) -> str:
    """TwiML to transfer the call to a human."""
    response = VoiceResponse()
    response.dial(to_number)
    return str(response)


def build_hangup_twiml() -> str:
    response = VoiceResponse()
    response.hangup()
    return str(response)


async def validate_twilio_signature(request: Request) -> None:
    """Reject requests that aren't signed by Twilio. Skipped if auth token unset (dev)."""
    if not settings.twilio_auth_token:
        return
    validator = RequestValidator(settings.twilio_auth_token)
    signature = request.headers.get("X-Twilio-Signature", "")
    url = str(request.url)
    form = await request.form()
    params = dict(form)
    if not validator.validate(url, params, signature):
        raise HTTPException(status_code=403, detail="invalid twilio signature")
