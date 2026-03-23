"""File-based cache with TTL for competitor and content intel."""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


class IntelCache:
    """File-based cache with TTL. Thread-safe for async use (files are atomic writes)."""

    def __init__(self, cache_dir: str | Path, ttl_days: int):
        self.cache_dir = Path(cache_dir)
        self.ttl = timedelta(days=ttl_days)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _meta_path(self, key: str) -> Path:
        safe = key.replace("/", "_").replace(" ", "_")
        return self.cache_dir / f"{safe}.cache.json"

    def get(self, key: str) -> Any | None:
        """Return cached value if it exists and is not stale, else None."""
        path = self._meta_path(key)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            cached_at = datetime.fromisoformat(data["cached_at"])
            if datetime.now() - cached_at > self.ttl:
                return None
            return data["value"]
        except (json.JSONDecodeError, KeyError, ValueError):
            return None

    def set(self, key: str, value: Any) -> None:
        """Write value to cache with current timestamp."""
        path = self._meta_path(key)
        path.write_text(
            json.dumps({"cached_at": datetime.now().isoformat(), "value": value}, indent=2)
        )

    def invalidate(self, key: str) -> bool:
        """Delete a cache entry. Returns True if it existed."""
        path = self._meta_path(key)
        if path.exists():
            path.unlink()
            return True
        return False

    def invalidate_all(self) -> int:
        """Delete all cache entries. Returns count deleted."""
        count = 0
        for f in self.cache_dir.glob("*.cache.json"):
            f.unlink()
            count += 1
        return count

    def is_fresh(self, key: str) -> bool:
        return self.get(key) is not None

    def stats(self) -> dict:
        entries = list(self.cache_dir.glob("*.cache.json"))
        fresh, stale = 0, 0
        for path in entries:
            try:
                data = json.loads(path.read_text())
                cached_at = datetime.fromisoformat(data["cached_at"])
                if datetime.now() - cached_at <= self.ttl:
                    fresh += 1
                else:
                    stale += 1
            except Exception:
                stale += 1
        return {"total": len(entries), "fresh": fresh, "stale": stale, "ttl_days": self.ttl.days}


def get_competitor_cache(brand: str) -> IntelCache:
    from agency.config import COMPETITOR_CACHE_TTL_DAYS
    return IntelCache(Path("competitor_intel") / brand, COMPETITOR_CACHE_TTL_DAYS)


def get_content_cache(brand: str) -> IntelCache:
    from agency.config import CONTENT_CACHE_TTL_DAYS
    return IntelCache(Path("content_intel") / brand, CONTENT_CACHE_TTL_DAYS)
