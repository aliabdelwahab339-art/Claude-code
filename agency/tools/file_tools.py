"""File read/write tools for agents — read client profiles, write deliverables."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def read_client_file(client_name: str, filename: str) -> str:
    """Read a file from clients/<client_name>/<filename>. Returns empty string if missing."""
    path = Path("clients") / client_name / filename
    if path.exists():
        return path.read_text()
    return ""


def read_all_client_files(client_name: str) -> dict[str, str]:
    """Read all markdown files for a client. Returns {filename: content}."""
    client_dir = Path("clients") / client_name
    if not client_dir.exists():
        return {}
    return {
        f.name: f.read_text()
        for f in sorted(client_dir.glob("*.md"))
    }


def write_intel_file(category: str, brand: str, filename: str, content: str) -> Path:
    """Write to competitor_intel/<brand>/<filename> or content_intel/<brand>/<filename>."""
    path = Path(f"{category}_intel") / brand / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


def write_output(brand: str, subdir: str, filename: str, content: str, run_id: str | None = None) -> Path:
    """Write campaign output to outputs/<brand>/<run_id>/<subdir>/<filename>."""
    if run_id is None:
        run_id = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    path = Path("outputs") / brand / run_id / subdir / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


def write_campaign_summary(brand: str, run_id: str, summary: dict) -> Path:
    """Write campaign_summary.md to the run output directory."""
    lines = [
        f"# Campaign Summary — {brand}",
        f"**Run ID:** {run_id}",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Intelligence Files",
        "",
    ]
    for k, v in summary.get("intelligence", {}).items():
        lines.append(f"- [{k}]({v})")
    lines += ["", "## Deliverables", ""]
    for k, v in summary.get("deliverables", {}).items():
        lines.append(f"- **{k}**: {v}")
    content = "\n".join(lines)
    return write_output(brand, "", "campaign_summary.md", content, run_id)


def read_intel_file(category: str, brand: str, filename: str) -> str:
    """Read competitor or content intel file. Returns empty string if missing."""
    path = Path(f"{category}_intel") / brand / filename
    if path.exists():
        return path.read_text()
    return ""


def list_raw_research_files(brand: str) -> list[Path]:
    """List all raw competitor research files for a brand."""
    raw_dir = Path("competitor_intel") / brand / "raw_research"
    if not raw_dir.exists():
        return []
    return sorted(raw_dir.glob("*.md"))


def read_frameworks() -> str:
    """Read the compiled personal frameworks skill file."""
    path = Path(".agents") / "my-frameworks.md"
    if path.exists():
        return path.read_text()
    return ""


def read_product_context() -> str:
    """Read the product marketing context skill file."""
    path = Path(".agents") / "product-marketing-context.md"
    if path.exists():
        return path.read_text()
    return ""


def ensure_output_dirs(brand: str, run_id: str) -> dict[str, Path]:
    """Create all output subdirectories for a campaign run."""
    base = Path("outputs") / brand / run_id
    dirs = {}
    for subdir in ["intelligence", "copy", "seo", "social", "ads", "brand_strategy"]:
        d = base / subdir
        d.mkdir(parents=True, exist_ok=True)
        dirs[subdir] = d
    return dirs
