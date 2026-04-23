"""Pipecat pipeline: Twilio audio <-> VAD <-> STT <-> Claude <-> TTS.

The pipeline is assembled per-call by `server.py` when a new Media Streams
WebSocket connects. Each call gets its own state (telemetry, tool dispatch,
context). The Pipecat framework handles VAD, turn detection, and interruption
semantics for us.
"""

from __future__ import annotations

import logging
from typing import Any

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import EndFrame, LLMMessagesFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_response import (
    LLMAssistantResponseAggregator,
    LLMUserResponseAggregator,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.serializers.twilio import TwilioFrameSerializer
from pipecat.services.anthropic import AnthropicLLMService
from pipecat.services.azure import AzureSTTService, AzureTTSService
from pipecat.services.deepgram import DeepgramSTTService
from pipecat.transports.network.fastapi_websocket import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)
from starlette.websockets import WebSocket

from egyptian_voice_agent.config import settings
from egyptian_voice_agent.dialect.fallbacks import normalize_egyptian
from egyptian_voice_agent.integrations import telemetry
from egyptian_voice_agent.llm import prompts
from egyptian_voice_agent.llm.tools import TOOLS, dispatch

logger = logging.getLogger(__name__)


def _build_stt():
    if settings.stt_provider == "azure":
        return AzureSTTService(
            api_key=settings.azure_speech_key,
            region=settings.azure_speech_region,
            language="ar-EG",
        )
    # Deepgram Nova-3 Arabic streaming (default)
    keywords_path = (
        __file__.rsplit("/", 1)[0] + "/dialect/keywords_ar_eg.txt"
    )
    try:
        with open(keywords_path, encoding="utf-8") as f:
            keywords = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        keywords = []
    return DeepgramSTTService(
        api_key=settings.deepgram_api_key,
        language="ar",
        model="nova-3",
        punctuate=True,
        smart_format=True,
        keywords=keywords[:200],  # Deepgram caps keyword list size
    )


def _build_tts():
    if settings.tts_provider == "elevenlabs":
        from pipecat.services.elevenlabs import ElevenLabsTTSService

        return ElevenLabsTTSService(
            api_key=settings.elevenlabs_api_key,
            voice_id=settings.elevenlabs_voice_id,
            model="eleven_flash_v2_5",
        )
    return AzureTTSService(
        api_key=settings.azure_speech_key,
        region=settings.azure_speech_region,
        voice=settings.agent_voice,
        language="ar-EG",
    )


class _EgyptianNormalizer(FrameProcessor):
    """Applies Egyptian slang post-processing to STT transcriptions in flight."""

    async def process_frame(self, frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        text = getattr(frame, "text", None)
        if text and isinstance(text, str):
            frame.text = normalize_egyptian(text)
        await self.push_frame(frame, direction)


class _ToolDispatcher(FrameProcessor):
    """Executes Anthropic tool calls emitted by the LLM service.

    Pipecat's AnthropicLLMService surfaces tool-use blocks as frames. We
    intercept, run our pydantic-validated handlers, and push the ar-EG
    confirmation back into the conversation so the LLM can speak it.
    """

    def __init__(self, call_sid: str, caller_phone: str | None):
        super().__init__()
        self.call_sid = call_sid
        self.caller_phone = caller_phone

    async def process_frame(self, frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        tool_name = getattr(frame, "function_name", None) or getattr(frame, "tool_name", None)
        if tool_name:
            arguments: dict[str, Any] = (
                getattr(frame, "arguments", None) or getattr(frame, "tool_input", {}) or {}
            )
            logger.info("tool_call call_sid=%s tool=%s", self.call_sid, tool_name)
            result = await dispatch(
                tool_name,
                arguments,
                call_sid=self.call_sid,
                caller_phone=self.caller_phone,
            )
            # Push the ar-EG confirmation back as an assistant message frame
            await self.push_frame(
                LLMMessagesFrame(
                    messages=[{"role": "assistant", "content": result.get("reply_ar", "")}]
                ),
                FrameDirection.DOWNSTREAM,
            )
            if tool_name == "end_call":
                telemetry.finalize(self.call_sid, outcome=arguments.get("outcome"))
                await self.push_frame(EndFrame(), FrameDirection.DOWNSTREAM)
            return
        await self.push_frame(frame, direction)


async def run_call(
    websocket: WebSocket,
    *,
    call_sid: str,
    caller_phone: str | None,
    stream_sid: str,
) -> None:
    """Drive a single call end-to-end over the given Twilio Media Streams WS."""
    telemetry.start_call(call_sid, caller_phone=caller_phone)

    transport = FastAPIWebsocketTransport(
        websocket=websocket,
        params=FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            add_wav_header=False,
            vad_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
            vad_audio_passthrough=True,
            serializer=TwilioFrameSerializer(stream_sid=stream_sid),
        ),
    )

    stt = _build_stt()
    llm = AnthropicLLMService(
        api_key=settings.anthropic_api_key,
        model=settings.llm_model,
    )
    # Attach tools + system prompt (with cache-control) to the LLM service.
    llm.set_tools(TOOLS)
    llm.set_system_prompt(prompts.system_prompt_blocks())

    tts = _build_tts()
    normalizer = _EgyptianNormalizer()
    dispatcher = _ToolDispatcher(call_sid=call_sid, caller_phone=caller_phone)
    user_agg = LLMUserResponseAggregator()
    asst_agg = LLMAssistantResponseAggregator()

    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            normalizer,
            user_agg,
            llm,
            dispatcher,
            tts,
            transport.output(),
            asst_agg,
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True,
            enable_metrics=True,
            report_only_initial_ttfb=False,
        ),
    )

    # Speak the greeting as the very first turn so the caller doesn't hear silence.
    @transport.event_handler("on_client_connected")
    async def _on_connected(transport, client):
        await task.queue_frame(
            LLMMessagesFrame(messages=[{"role": "assistant", "content": prompts.greeting()}])
        )

    @transport.event_handler("on_client_disconnected")
    async def _on_disconnected(transport, client):
        telemetry.finalize(call_sid, outcome="no_answer")
        await task.queue_frame(EndFrame())

    try:
        await PipelineRunner().run(task)
    finally:
        # Ensure we always flush telemetry even on exception paths.
        if telemetry.get(call_sid) is not None:
            telemetry.finalize(call_sid)
