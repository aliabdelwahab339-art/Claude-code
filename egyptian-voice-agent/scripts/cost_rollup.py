"""Weekly cost rollup from telemetry JSONL.

Usage:
    python scripts/cost_rollup.py            # last 7 days
    python scripts/cost_rollup.py --days 30
"""

from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from pathlib import Path

from rich.console import Console
from rich.table import Table

from egyptian_voice_agent.config import settings


def rollup(days: int) -> None:
    path: Path = settings.telemetry_path
    if not path.exists():
        Console().print(f"[yellow]No telemetry file at {path}.[/yellow]")
        return
    cutoff = time.time() - days * 86400
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("started_at", 0) >= cutoff:
            records.append(rec)

    console = Console()
    if not records:
        console.print(f"[yellow]No calls in the last {days} days.[/yellow]")
        return

    total_cost = sum(r.get("est_cost_usd", 0) for r in records)
    total_minutes = sum(r.get("duration_s", 0) for r in records) / 60
    outcomes = Counter(r.get("outcome") or "unknown" for r in records)

    table = Table(title=f"Call rollup — last {days} days")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_row("Calls", str(len(records)))
    table.add_row("Total minutes", f"{total_minutes:.1f}")
    table.add_row("Total est. cost (USD)", f"${total_cost:.2f}")
    table.add_row("Avg cost / call", f"${total_cost / len(records):.4f}")
    table.add_row(
        "Avg cost / minute",
        f"${total_cost / total_minutes:.4f}" if total_minutes else "n/a",
    )
    console.print(table)

    outcomes_table = Table(title="Outcomes")
    outcomes_table.add_column("Outcome")
    outcomes_table.add_column("Count", justify="right")
    outcomes_table.add_column("Share", justify="right")
    for name, n in outcomes.most_common():
        outcomes_table.add_row(name, str(n), f"{n / len(records):.0%}")
    console.print(outcomes_table)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7)
    args = parser.parse_args()
    rollup(args.days)
