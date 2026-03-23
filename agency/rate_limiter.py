"""Async rate limiting with per-client and system-wide semaphores + tenacity retry."""

import asyncio
import logging
from contextlib import asynccontextmanager
from functools import wraps
from typing import Callable

import anthropic
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from agency.config import (
    MAX_CONCURRENT_API_CALLS,
    MAX_CONCURRENT_PER_CLIENT,
    RETRY_MAX_ATTEMPTS,
    RETRY_MIN_WAIT,
    RETRY_MAX_WAIT,
)

logger = logging.getLogger(__name__)

# ── Global semaphore — system-wide cap ────────────────────────────────────────
_system_semaphore: asyncio.Semaphore | None = None


def get_system_semaphore() -> asyncio.Semaphore:
    global _system_semaphore
    if _system_semaphore is None:
        _system_semaphore = asyncio.Semaphore(MAX_CONCURRENT_API_CALLS)
    return _system_semaphore


# ── Per-client semaphores ─────────────────────────────────────────────────────
_client_semaphores: dict[str, asyncio.Semaphore] = {}


def get_client_semaphore(client_name: str) -> asyncio.Semaphore:
    if client_name not in _client_semaphores:
        _client_semaphores[client_name] = asyncio.Semaphore(MAX_CONCURRENT_PER_CLIENT)
    return _client_semaphores[client_name]


@asynccontextmanager
async def rate_limited(client_name: str):
    """Context manager: acquire both per-client and system semaphores."""
    client_sem = get_client_semaphore(client_name)
    system_sem = get_system_semaphore()
    async with client_sem:
        async with system_sem:
            yield


# ── Retry decorator for Anthropic API calls ───────────────────────────────────
def with_retry(func: Callable) -> Callable:
    """Wrap an async function with exponential backoff retry on 429/5xx."""

    @retry(
        retry=retry_if_exception_type((anthropic.RateLimitError, anthropic.APIStatusError)),
        stop=stop_after_attempt(RETRY_MAX_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)

    return wrapper


def is_retryable_error(exc: Exception) -> bool:
    if isinstance(exc, anthropic.RateLimitError):
        return True
    if isinstance(exc, anthropic.APIStatusError) and exc.status_code >= 500:
        return True
    return False
