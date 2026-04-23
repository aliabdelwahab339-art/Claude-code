"""FastAPI server: Twilio Voice webhook + Media Streams WebSocket.

Endpoints:
  GET  /health                    — liveness probe
  POST /twilio/voice              — Twilio hits this on inbound call; returns TwiML
                                     that connects the call to /twilio/media
  WS   /twilio/media              — Twilio bidirectional audio stream; runs the pipeline
"""

from __future__ import annotations

import json
import logging

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse, Response

from egyptian_voice_agent.config import settings
from egyptian_voice_agent.integrations.twilio_handler import (
    build_stream_twiml,
    validate_twilio_signature,
)
from egyptian_voice_agent.outbound import place_call
from egyptian_voice_agent.pipeline import run_call

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger(__name__)

app = FastAPI(title="Egyptian Voice Agent", version="0.1.0")


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "brand": settings.brand_name,
        "agent": settings.agent_name,
        "voice": settings.agent_voice,
        "stt": settings.stt_provider,
        "tts": settings.tts_provider,
    }


def _ws_stream_url() -> str:
    base = (
        settings.public_base_url.rstrip("/")
        .replace("https://", "wss://")
        .replace("http://", "ws://")
    )
    return f"{base}/twilio/media"


@app.post("/twilio/voice", response_class=PlainTextResponse)
async def twilio_voice(request: Request) -> Response:
    """Twilio webhook for inbound calls. Returns TwiML to start Media Streams."""
    await validate_twilio_signature(request)
    twiml = build_stream_twiml(_ws_stream_url(), direction="inbound")
    return Response(content=twiml, media_type="application/xml")


@app.api_route(
    "/twilio/outbound-twiml",
    methods=["GET", "POST"],
    response_class=PlainTextResponse,
)
async def twilio_outbound_twiml(request: Request) -> Response:
    """TwiML fetched by Twilio when our outbound REST call connects.

    Lead context is passed through as query params by `outbound.place_call`.
    POST requests from Twilio are signed; we validate. GETs (for manual
    testing) skip validation.
    """
    if request.method == "POST":
        await validate_twilio_signature(request)
    params = dict(request.query_params)
    lead_name = params.get("lead_name") or None
    context = params.get("context") or None
    twiml = build_stream_twiml(
        _ws_stream_url(),
        direction="outbound",
        lead_name=lead_name,
        context=context,
    )
    return Response(content=twiml, media_type="application/xml")


@app.post("/outbound/call")
async def outbound_call(request: Request) -> dict:
    """Place an outbound call. JSON body: {to, lead_name?, context?, force?}.

    Protected by a simple shared secret in the `X-API-Key` header when
    `OUTBOUND_API_KEY` is set. Useful for triggering dials from a CRM,
    a cron, or a dashboard.
    """
    api_key = settings.outbound_api_key
    if api_key and request.headers.get("X-API-Key") != api_key:
        return Response(status_code=401, content="unauthorized")  # type: ignore[return-value]
    payload = await request.json()
    sid = await place_call(
        to=payload["to"],
        lead_name=payload.get("lead_name"),
        context=payload.get("context"),
        force=bool(payload.get("force", False)),
    )
    return {"call_sid": sid}


@app.websocket("/twilio/media")
async def twilio_media(websocket: WebSocket) -> None:
    """Handle Twilio Media Streams connection for a single call."""
    await websocket.accept()
    call_sid: str | None = None
    caller_phone: str | None = None
    stream_sid: str | None = None
    direction = "inbound"
    lead_name: str | None = None
    context: str | None = None

    try:
        # Twilio sends a `connected` frame, then a `start` frame with metadata.
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            event = msg.get("event")
            if event == "start":
                start = msg.get("start", {})
                call_sid = start.get("callSid")
                stream_sid = start.get("streamSid")
                cp = start.get("customParameters", {}) or {}
                caller_phone = cp.get("from") or start.get("from")
                direction = cp.get("direction", "inbound")
                lead_name = cp.get("lead_name") or None
                context = cp.get("context") or None
                logger.info(
                    "call_start sid=%s dir=%s from=%s lead=%s stream=%s",
                    call_sid,
                    direction,
                    caller_phone,
                    lead_name,
                    stream_sid,
                )
                break
            if event == "connected":
                continue
            if event == "stop":
                return
    except WebSocketDisconnect:
        return

    if not call_sid or not stream_sid:
        await websocket.close(code=1008)
        return

    try:
        await run_call(
            websocket,
            call_sid=call_sid,
            caller_phone=caller_phone,
            stream_sid=stream_sid,
            direction=direction,
            lead_name=lead_name,
            context=context,
        )
    except WebSocketDisconnect:
        logger.info("call_end sid=%s (disconnect)", call_sid)
    except Exception:
        logger.exception("pipeline error sid=%s", call_sid)
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
