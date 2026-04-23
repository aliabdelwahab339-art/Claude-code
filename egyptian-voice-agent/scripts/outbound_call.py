"""Outbound call CLI.

Two modes:

  1. Dial one lead:
        python scripts/outbound_call.py \
            --to +201012345678 \
            --name "أحمد" \
            --context "متابعة طلب عرض السعر"

  2. Batch-dial from CSV (columns: to,name,context):
        python scripts/outbound_call.py --csv leads.csv
        python scripts/outbound_call.py --csv leads.csv --pace 30 --max 50

Pacing defaults to one call every 20 seconds so Twilio concurrency doesn't
spike and so a human operator can monitor quality in real time. Respects the
DNC list (`DNC_PATH`) and Egyptian calling hours (09:00–21:00 Cairo, Sat–Thu)
unless `--force` is passed.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from egyptian_voice_agent.outbound import DNC, place_call, within_calling_hours
from egyptian_voice_agent.config import settings

console = Console()


async def dial_one(to: str, name: str | None, context: str | None, force: bool) -> dict:
    try:
        sid = await place_call(to, lead_name=name, context=context, force=force)
        return {"to": to, "name": name, "status": "dialed", "sid": sid}
    except PermissionError as e:
        return {"to": to, "name": name, "status": "skipped", "reason": str(e)}
    except Exception as e:  # noqa: BLE001
        return {"to": to, "name": name, "status": "error", "reason": str(e)}


async def dial_batch(
    rows: list[dict], *, pace_s: float, max_calls: int | None, force: bool
) -> list[dict]:
    results: list[dict] = []
    dnc = DNC.load(settings.dnc_path)
    for i, row in enumerate(rows):
        if max_calls is not None and i >= max_calls:
            break
        to = row["to"].strip()
        if to in dnc:
            results.append({"to": to, "name": row.get("name"), "status": "dnc"})
            continue
        if not force and not within_calling_hours():
            results.append({"to": to, "name": row.get("name"), "status": "out_of_hours"})
            continue
        results.append(
            await dial_one(to, row.get("name"), row.get("context"), force=force)
        )
        if i < len(rows) - 1:
            await asyncio.sleep(pace_s)
    return results


def load_csv(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        required = {"to"}
        if not required.issubset(reader.fieldnames or set()):
            raise SystemExit(f"CSV must have columns: to, name, context (got {reader.fieldnames})")
        for r in reader:
            if r.get("to"):
                rows.append(r)
    return rows


def render(results: list[dict]) -> None:
    table = Table(title="Outbound dial results")
    table.add_column("to")
    table.add_column("name")
    table.add_column("status")
    table.add_column("detail")
    for r in results:
        detail = r.get("sid") or r.get("reason") or ""
        table.add_row(r["to"], r.get("name") or "", r["status"], str(detail))
    console.print(table)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--to", help="E.164 number to dial (single-shot mode)")
    parser.add_argument("--name", help="Lead name (single-shot mode)")
    parser.add_argument("--context", help="Call reason / context (single-shot mode)")
    parser.add_argument("--csv", type=Path, help="CSV with columns: to,name,context")
    parser.add_argument(
        "--pace", type=float, default=20.0, help="Seconds between calls (batch mode)"
    )
    parser.add_argument(
        "--max", type=int, default=None, help="Cap on number of calls in this run"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass Egypt calling-hours guard"
    )
    args = parser.parse_args()

    if not args.to and not args.csv:
        parser.print_help()
        sys.exit(2)

    if args.to:
        result = await dial_one(args.to, args.name, args.context, force=args.force)
        render([result])
    else:
        rows = load_csv(args.csv)
        console.print(f"[bold]Loaded {len(rows)} leads from {args.csv}[/bold]")
        results = await dial_batch(rows, pace_s=args.pace, max_calls=args.max, force=args.force)
        render(results)


if __name__ == "__main__":
    asyncio.run(main())
