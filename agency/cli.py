"""CLI entry point — agency run, status, cache commands."""

import asyncio
import json
import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()
logger = logging.getLogger(__name__)


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def load_brief(client_name: str) -> dict:
    """Load client brief from clients/<name>/brief.md and adjacent files."""
    client_dir = Path("clients") / client_name
    if not client_dir.exists():
        console.print(f"[red]Client '{client_name}' not found in clients/[/red]")
        sys.exit(1)

    brief: dict = {"client_name": client_name}
    for fname in ["brief.md", "personas.md", "pain_points.md", "case_studies.md", "brand_guidelines.md"]:
        fpath = client_dir / fname
        if fpath.exists():
            brief[fname.replace(".md", "")] = fpath.read_text()
    return brief


async def run_single(client_name: str) -> None:
    from agency.orchestrator import run_campaign
    console.print(f"[bold green]Starting campaign for:[/bold green] {client_name}")
    brief = load_brief(client_name)
    result = await run_campaign(brief, client_name)
    console.print(f"[bold green]Campaign complete![/bold green] Output: {result.get('output_dir', 'see outputs/')}")


async def run_all_clients() -> None:
    from agency.orchestrator import run_campaign
    from agency.queue import AgencyQueue, CampaignJob

    client_dirs = [d for d in Path("clients").iterdir() if d.is_dir() and d.name != "_template"]
    if not client_dirs:
        console.print("[yellow]No clients found in clients/[/yellow]")
        return

    console.print(f"[bold]Running campaigns for {len(client_dirs)} clients...[/bold]")

    async def worker_fn(job: CampaignJob):
        return await run_campaign(job.brief, job.client_name)

    queue = AgencyQueue(worker_fn)
    await queue.start()

    for client_dir in client_dirs:
        brief = load_brief(client_dir.name)
        await queue.enqueue(client_dir.name, brief)

    await queue.wait_all()
    await queue.stop()

    status = queue.status()
    console.print(f"\n[bold]All campaigns complete:[/bold] {status['completed']} succeeded, {status['failed']} failed")


async def run_clients_list(client_names: list[str]) -> None:
    from agency.orchestrator import run_campaign
    from agency.queue import AgencyQueue, CampaignJob

    async def worker_fn(job: CampaignJob):
        return await run_campaign(job.brief, job.client_name)

    queue = AgencyQueue(worker_fn)
    await queue.start()

    for name in client_names:
        brief = load_brief(name)
        await queue.enqueue(name, brief)

    await queue.wait_all()
    await queue.stop()


def cmd_status() -> None:
    """Show queue and worker status."""
    console.print("[bold]Agency Status[/bold]")
    console.print("No active queue — use 'agency run' to start a campaign.")
    _print_cache_status()


def _print_cache_status() -> None:
    from agency.cache import get_competitor_cache, get_content_cache
    table = Table(title="Cache Status")
    table.add_column("Brand")
    table.add_column("Competitor Cache")
    table.add_column("Content Cache")

    competitor_base = Path("competitor_intel")
    content_base = Path("content_intel")

    brands = set()
    if competitor_base.exists():
        brands.update(d.name for d in competitor_base.iterdir() if d.is_dir())
    if content_base.exists():
        brands.update(d.name for d in content_base.iterdir() if d.is_dir())

    for brand in sorted(brands):
        comp_stats = get_competitor_cache(brand).stats()
        cont_stats = get_content_cache(brand).stats()
        table.add_row(
            brand,
            f"{comp_stats['fresh']} fresh / {comp_stats['stale']} stale (TTL {comp_stats['ttl_days']}d)",
            f"{cont_stats['fresh']} fresh / {cont_stats['stale']} stale (TTL {cont_stats['ttl_days']}d)",
        )

    if brands:
        console.print(table)
    else:
        console.print("[dim]No cached intel found.[/dim]")


def cmd_cache_clear(client_name: str | None = None) -> None:
    from agency.cache import get_competitor_cache, get_content_cache

    if client_name:
        n1 = get_competitor_cache(client_name).invalidate_all()
        n2 = get_content_cache(client_name).invalidate_all()
        console.print(f"Cleared {n1 + n2} cache entries for '{client_name}'")
    else:
        from agency.config import OUTPUT_DIR
        total = 0
        for base in [Path("competitor_intel"), Path("content_intel")]:
            if base.exists():
                for brand_dir in base.iterdir():
                    if brand_dir.is_dir():
                        for f in brand_dir.glob("*.cache.json"):
                            f.unlink()
                            total += 1
        console.print(f"Cleared {total} cache entries for all clients")


def print_help() -> None:
    console.print("""[bold]AI Marketing Agency CLI[/bold]

[bold yellow]Commands:[/bold yellow]
  agency run --client <name>         Run campaign for one client
  agency run --all                   Run campaigns for all clients in parallel
  agency run --clients a,b,c         Run campaigns for multiple clients
  agency status                      Show queue + cache status
  agency cache clear                 Clear all cache entries
  agency cache clear --client <name> Clear cache for one client
  agency --help                      Show this help
""")


def main() -> None:
    import os
    from agency.config import LOG_LEVEL
    setup_logging(os.getenv("LOG_LEVEL", LOG_LEVEL))

    args = sys.argv[1:]

    if not args or "--help" in args or "-h" in args:
        print_help()
        return

    cmd = args[0]

    if cmd == "run":
        if "--all" in args:
            asyncio.run(run_all_clients())
        elif "--client" in args:
            idx = args.index("--client")
            client_name = args[idx + 1] if idx + 1 < len(args) else None
            if not client_name:
                console.print("[red]--client requires a name[/red]")
                sys.exit(1)
            asyncio.run(run_single(client_name))
        elif "--clients" in args:
            idx = args.index("--clients")
            names_str = args[idx + 1] if idx + 1 < len(args) else ""
            names = [n.strip() for n in names_str.split(",") if n.strip()]
            if not names:
                console.print("[red]--clients requires a comma-separated list[/red]")
                sys.exit(1)
            asyncio.run(run_clients_list(names))
        else:
            console.print("[red]Usage: agency run --client <name> | --all | --clients a,b,c[/red]")
            sys.exit(1)

    elif cmd == "status":
        cmd_status()

    elif cmd == "cache":
        if len(args) < 2:
            console.print("[red]Usage: agency cache clear [--client <name>][/red]")
            sys.exit(1)
        subcmd = args[1]
        if subcmd == "clear":
            client = None
            if "--client" in args:
                idx = args.index("--client")
                client = args[idx + 1] if idx + 1 < len(args) else None
            cmd_cache_clear(client)
        else:
            console.print(f"[red]Unknown cache command: {subcmd}[/red]")
            sys.exit(1)

    else:
        console.print(f"[red]Unknown command: {cmd}[/red]")
        print_help()
        sys.exit(1)
