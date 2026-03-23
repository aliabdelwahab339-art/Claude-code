"""Shared Anthropic client singleton + call_claude() helper.

Every API call in the system goes through call_claude().
This enforces:
  1. Single shared AsyncAnthropic connection pool (not one client per agent call)
  2. Per-client semaphore (MAX_CONCURRENT_PER_CLIENT = 10)
  3. System-wide semaphore (MAX_CONCURRENT_API_CALLS = 50)
  4. Automatic exponential backoff on 429 / 5xx

Usage in every agent:
    from agency.api_client import call_claude

    result = await call_claude(
        client_name="brand_x",
        model=MODELS["specialists"],
        system="...",
        prompt="...",
        max_tokens=4096,
    )
"""

import asyncio
import logging

import anthropic
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from agency.config import (
    ANTHROPIC_API_KEY,
    RETRY_MAX_ATTEMPTS,
    RETRY_MIN_WAIT,
    RETRY_MAX_WAIT,
)
from agency.rate_limiter import rate_limited

logger = logging.getLogger(__name__)

# ── Single shared client — one connection pool for the entire process ─────────
_shared_client: anthropic.AsyncAnthropic | None = None


def get_client() -> anthropic.AsyncAnthropic:
    global _shared_client
    if _shared_client is None:
        _shared_client = anthropic.AsyncAnthropic(
            api_key=ANTHROPIC_API_KEY,
            # httpx connection pool limits — enough for MAX_CONCURRENT_API_CALLS
            # anthropic SDK uses httpx internally; default limits are fine but explicit is better
            max_retries=0,  # we handle retries ourselves with tenacity
        )
    return _shared_client


async def call_claude(
    client_name: str,
    model: str,
    system: str,
    prompt: str,
    max_tokens: int = 4096,
    thinking: dict | None = None,
) -> str:
    """Make a Claude API call gated through per-client + system-wide semaphores.

    Automatically retries on 429 / 5xx with exponential backoff.
    Returns the text content of the first message block.
    """
    @retry(
        retry=retry_if_exception_type((anthropic.RateLimitError, anthropic.APIStatusError)),
        stop=stop_after_attempt(RETRY_MAX_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def _call() -> str:
        async with rate_limited(client_name):
            client = get_client()
            kwargs: dict = {
                "model": model,
                "max_tokens": max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": prompt}],
            }
            if thinking:
                kwargs["thinking"] = thinking

            message = await client.messages.create(**kwargs)
            return "".join(
                block.text for block in message.content if hasattr(block, "text")
            )

    return await _call()
