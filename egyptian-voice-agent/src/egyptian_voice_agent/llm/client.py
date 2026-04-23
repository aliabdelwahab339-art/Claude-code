"""Shared AsyncAnthropic client with retries.

One connection pool per process. Tenacity handles 429/5xx with exponential backoff.
"""

from __future__ import annotations

import logging

import anthropic
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from egyptian_voice_agent.config import settings

logger = logging.getLogger(__name__)

_client: anthropic.AsyncAnthropic | None = None


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key,
            max_retries=0,
        )
    return _client


@retry(
    retry=retry_if_exception_type((anthropic.RateLimitError, anthropic.APIStatusError)),
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=1, max=16),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def create_message(**kwargs):
    """Thin retry-wrapped passthrough to `messages.create`.

    Used by Pipecat's Anthropic LLM service when we need direct calls
    (e.g., eval harness, local scripts). Pipecat's own service wraps streaming.
    """
    client = get_client()
    return await client.messages.create(**kwargs)
