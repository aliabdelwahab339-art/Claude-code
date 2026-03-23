"""Brave Search and HTTP fetch with shared connection pools.

Uses module-level httpx.AsyncClient instances — NOT one client per request.
Connection limits prevent file-descriptor exhaustion at 100 concurrent clients.
"""

import asyncio
import logging
import os
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

BRAVE_API_KEY = os.getenv("BRAVE_API_KEY", "")
BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"
FETCH_TIMEOUT = 30  # seconds
MAX_RETRIES = 3

# ── Shared connection pools — created once, reused for all requests ───────────
# Hard cap: 50 total connections, 20 per host
# This prevents FD exhaustion at 100 concurrent clients
_HTTP_LIMITS = httpx.Limits(max_connections=50, max_keepalive_connections=20)

_brave_client: httpx.AsyncClient | None = None
_fetch_client: httpx.AsyncClient | None = None


def get_brave_client() -> httpx.AsyncClient:
    global _brave_client
    if _brave_client is None or _brave_client.is_closed:
        _brave_client = httpx.AsyncClient(
            timeout=FETCH_TIMEOUT,
            limits=_HTTP_LIMITS,
            headers={
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": BRAVE_API_KEY,
            },
        )
    return _brave_client


def get_fetch_client() -> httpx.AsyncClient:
    global _fetch_client
    if _fetch_client is None or _fetch_client.is_closed:
        _fetch_client = httpx.AsyncClient(
            timeout=FETCH_TIMEOUT,
            limits=_HTTP_LIMITS,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; MarketingBot/1.0)",
                "Accept": "text/html,application/xhtml+xml,text/plain",
            },
        )
    return _fetch_client


async def close_pools() -> None:
    """Call at process shutdown to cleanly close connection pools."""
    global _brave_client, _fetch_client
    if _brave_client and not _brave_client.is_closed:
        await _brave_client.aclose()
    if _fetch_client and not _fetch_client.is_closed:
        await _fetch_client.aclose()


@retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(min=1, max=10))
async def brave_search(query: str, count: int = 10) -> list[dict[str, str]]:
    """Search using Brave Search API via shared connection pool."""
    if not BRAVE_API_KEY:
        logger.warning("BRAVE_API_KEY not set — returning empty search results")
        return []

    params = {"q": query, "count": min(count, 20), "search_lang": "en"}
    try:
        resp = await get_brave_client().get(BRAVE_SEARCH_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 429:
            logger.warning("Brave Search rate limited — retrying")
            raise
        logger.warning("Brave Search error %s for query: %s", exc.response.status_code, query)
        return []
    except Exception as exc:
        logger.warning("Brave Search failed for '%s': %s", query, exc)
        return []

    return [
        {
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "description": item.get("description", ""),
        }
        for item in data.get("web", {}).get("results", [])
    ]


@retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(min=1, max=10))
async def fetch_page(url: str, max_chars: int = 8000) -> str:
    """Fetch a web page via shared connection pool."""
    try:
        resp = await get_fetch_client().get(url)
        resp.raise_for_status()
        text = resp.text
        import re
        text = re.sub(r"<[^>]+>", " ", text)   # crude HTML strip
        text = re.sub(r"\s+", " ", text)
        return text[:max_chars]
    except Exception as exc:
        logger.warning("fetch_page failed for %s: %s", url, exc)
        return f"[fetch failed: {exc}]"


async def search_and_fetch(query: str, max_pages: int = 3) -> list[dict[str, str]]:
    """Search Brave and fetch top N pages concurrently."""
    results = await brave_search(query, count=max_pages * 2)
    fetch_tasks = [fetch_page(r["url"]) for r in results[:max_pages]]
    contents = await asyncio.gather(*fetch_tasks, return_exceptions=True)
    return [
        {
            "url": result["url"],
            "title": result["title"],
            "content": content if isinstance(content, str) else f"[error: {content}]",
        }
        for result, content in zip(results[:max_pages], contents)
    ]


def format_search_results(results: list[dict]) -> str:
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. **{r.get('title', 'No title')}**")
        lines.append(f"   URL: {r.get('url', '')}")
        if r.get("description"):
            lines.append(f"   {r['description']}")
        lines.append("")
    return "\n".join(lines)
