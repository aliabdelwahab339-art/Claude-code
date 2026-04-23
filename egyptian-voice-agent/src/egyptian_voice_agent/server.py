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


@app.post("/twilio/voice", response_class=PlainTextResponse)
async def twilio_voice(request: Request) -> Response:
    """Twilio webhook for inbound calls. Returns TwiML to start Media Streams."""
    await validate_twilio_signature(request)
    # wss:// URL Twilio will open immediately after accepting this TwiML.
    base = settings.public_base_url.rstrip("/").replace("https://", "wss://").replace(
        "http://", "ws://"
    )
    stream_url = f"{base}/twilio/media"
    twiml = build_stream_twiml(stream_url)
    return Response(content=twiml, media_type="application/xml")


@app.websocket("/twilio/media")
async def twilio_media(websocket: WebSocket) -> None:
    """Handle Twilio Media Streams connection for a single call."""
    await websocket.accept()
    call_sid: str | None = None
    caller_phone: str | None = None
    stream_sid: str | None = None

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
                caller_phone = start.get("customParameters", {}).get("from") or start.get(
                    "from"
                )
                logger.info(
                    "call_start sid=%s from=%s stream=%s", call_sid, caller_phone, stream_sid
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
