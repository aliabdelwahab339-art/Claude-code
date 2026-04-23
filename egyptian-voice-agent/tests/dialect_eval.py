"""Dialect eval harness — measure STT WER on a curated set of ar-EG clips.

Usage:
    python -m tests.dialect_eval

Drops WER + per-clip diff table to stdout via rich. Requires:
  - tests/fixtures/ar_eg_*.wav
  - tests/fixtures/ground_truth.json  (mapping of filename -> reference transcript)
  - DEEPGRAM_API_KEY or AZURE_SPEECH_KEY in .env
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx
from rich.console import Console
from rich.table import Table

from egyptian_voice_agent.config import settings
from egyptian_voice_agent.dialect.fallbacks import normalize_egyptian

try:
    from jiwer import wer
except ImportError:  # pragma: no cover
    wer = None

FIXTURES = Path(__file__).parent / "fixtures"
console = Console()


async def transcribe_deepgram(wav: Path) -> str:
    url = "https://api.deepgram.com/v1/listen?model=nova-3&language=ar&punctuate=true&smart_format=true"
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(
            url,
            content=wav.read_bytes(),
            headers={
                "Authorization": f"Token {settings.deepgram_api_key}",
                "Content-Type": "audio/wav",
            },
        )
        r.raise_for_status()
        return r.json()["results"]["channels"][0]["alternatives"][0]["transcript"]


async def transcribe_azure(wav: Path) -> str:
    url = (
        f"https://{settings.azure_speech_region}.stt.speech.microsoft.com"
        "/speech/recognition/conversation/cognitiveservices/v1?language=ar-EG&format=detailed"
    )
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(
            url,
            content=wav.read_bytes(),
            headers={
                "Ocp-Apim-Subscription-Key": settings.azure_speech_key,
                "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
                "Accept": "application/json",
            },
        )
        r.raise_for_status()
        data = r.json()
        return data.get("DisplayText", "")


async def evaluate(provider: str = "deepgram") -> None:
    if wer is None:
        console.print("[red]Install dev deps: pip install -e '.[dev]'[/red]")
        return

    gt_path = FIXTURES / "ground_truth.json"
    if not gt_path.exists():
        console.print(f"[yellow]No ground truth at {gt_path}. Add WAVs + transcripts.[/yellow]")
        return

    ground_truth: dict[str, str] = json.loads(gt_path.read_text(encoding="utf-8"))
    transcribe = transcribe_deepgram if provider == "deepgram" else transcribe_azure

    table = Table(title=f"ar-EG WER — {provider}")
    table.add_column("clip")
    table.add_column("ref")
    table.add_column("hyp")
    table.add_column("WER", justify="right")

    wers: list[float] = []
    for name, ref in ground_truth.items():
        wav = FIXTURES / name
        if not wav.exists():
            continue
        raw = await transcribe(wav)
        hyp = normalize_egyptian(raw)
        score = wer(ref, hyp)
        wers.append(score)
        table.add_row(name, ref, hyp, f"{score:.2%}")

    console.print(table)
    if wers:
        mean = sum(wers) / len(wers)
        console.print(f"[bold]Mean WER: {mean:.2%}[/bold]")
        gate = 0.18 if provider == "deepgram" else 0.12
        status = "PASS" if mean < gate else "FAIL"
        console.print(f"Gate: < {gate:.0%}  →  {status}")


if __name__ == "__main__":
    asyncio.run(evaluate(settings.stt_provider))
