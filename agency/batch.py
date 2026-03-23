"""Anthropic Batches API wrapper for bulk non-urgent work (50% cheaper)."""

import asyncio
import logging
import time
from typing import Any

import anthropic

from agency.config import ANTHROPIC_API_KEY, MODELS

logger = logging.getLogger(__name__)

# Batch poll interval (seconds)
POLL_INTERVAL = 30
# Max wait time for batch completion (seconds) — 1 hour
MAX_WAIT_SECONDS = 3600


class BatchJob:
    """A single request within a batch."""

    def __init__(self, custom_id: str, prompt: str, system: str = "", max_tokens: int = 4096):
        self.custom_id = custom_id
        self.prompt = prompt
        self.system = system
        self.max_tokens = max_tokens

    def to_request(self) -> anthropic.types.message_create_params.MessageCreateParamsNonStreaming:
        messages = [{"role": "user", "content": self.prompt}]
        params: dict[str, Any] = {
            "model": MODELS["specialists"],
            "max_tokens": self.max_tokens,
            "messages": messages,
        }
        if self.system:
            params["system"] = self.system
        return params  # type: ignore[return-value]


class MarketingBatch:
    """Submit a batch of marketing generation tasks and await results.

    Ideal for:
    - Ad variations (10 Google + 10 Meta per client × 100 clients)
    - SEO keyword list generation
    - Meta description generation
    - Social post variations
    """

    def __init__(self):
        self._client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def submit(self, jobs: list[BatchJob]) -> str:
        """Submit batch synchronously. Returns batch ID."""
        requests = [
            anthropic.types.message_create_params.MessageCreateParamsNonStreaming(
                custom_id=job.custom_id, **job.to_request()
            )
            for job in jobs
        ]
        batch = self._client.messages.batches.create(requests=requests)
        logger.info("Batch submitted: %s (%d requests)", batch.id, len(jobs))
        return batch.id

    async def submit_async(self, jobs: list[BatchJob]) -> str:
        """Submit batch from async context."""
        return await asyncio.get_event_loop().run_in_executor(None, self.submit, jobs)

    def wait_for_results(self, batch_id: str) -> dict[str, str]:
        """Poll until batch completes. Returns {custom_id: text_content}."""
        start = time.time()
        while True:
            batch = self._client.messages.batches.retrieve(batch_id)
            logger.info(
                "Batch %s status: %s (processing=%d, succeeded=%d, errored=%d)",
                batch_id,
                batch.processing_status,
                batch.request_counts.processing,
                batch.request_counts.succeeded,
                batch.request_counts.errored,
            )
            if batch.processing_status == "ended":
                break
            if time.time() - start > MAX_WAIT_SECONDS:
                raise TimeoutError(f"Batch {batch_id} did not complete within {MAX_WAIT_SECONDS}s")
            time.sleep(POLL_INTERVAL)

        results: dict[str, str] = {}
        for result in self._client.messages.batches.results(batch_id):
            if result.result.type == "succeeded":
                content = result.result.message.content
                text = "".join(block.text for block in content if hasattr(block, "text"))
                results[result.custom_id] = text
            else:
                logger.warning("Batch result %s failed: %s", result.custom_id, result.result.type)
                results[result.custom_id] = ""
        return results

    async def wait_for_results_async(self, batch_id: str) -> dict[str, str]:
        """Async wrapper — runs polling in thread pool to avoid blocking event loop."""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.wait_for_results, batch_id
        )

    async def run_batch_async(self, jobs: list[BatchJob]) -> dict[str, str]:
        """Submit + wait in one call."""
        batch_id = await self.submit_async(jobs)
        return await self.wait_for_results_async(batch_id)


def make_ad_batch_jobs(
    brand: str,
    brief: str,
    intel_summary: str,
    n_google: int = 10,
    n_meta: int = 10,
) -> list[BatchJob]:
    """Generate BatchJob list for Google and Meta ad variations."""
    jobs = []
    system = f"""You are an expert ad copywriter for {brand}.
Use this competitive intelligence to write better ads than competitors:
{intel_summary}"""

    for i in range(1, n_google + 1):
        jobs.append(
            BatchJob(
                custom_id=f"{brand}_google_ad_{i}",
                prompt=f"Write Google Search Ad #{i} for: {brief}\n\nVariation angle: {i}",
                system=system,
                max_tokens=300,
            )
        )
    for i in range(1, n_meta + 1):
        jobs.append(
            BatchJob(
                custom_id=f"{brand}_meta_ad_{i}",
                prompt=f"Write Meta/Facebook Ad #{i} for: {brief}\n\nVariation angle: {i}",
                system=system,
                max_tokens=500,
            )
        )
    return jobs
