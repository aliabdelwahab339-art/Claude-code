"""Phase 1A — Competitor Research Agent.

Step 0: Discover 3-5 competitors from brief via Brave Search.
Step 1: Scrape each competitor in parallel (homepage, pricing, blog, reviews, ads).
Saves raw findings to competitor_intel/<brand>/raw_research/<competitor>.md
"""

import asyncio
import logging
from pathlib import Path

import anthropic

from agency.config import ANTHROPIC_API_KEY, MODELS, MAX_TOKENS, MAX_COMPETITORS
from agency.cache import get_competitor_cache
from agency.tools.file_tools import write_intel_file
from agency.tools.web_tools import brave_search, fetch_page, format_search_results

logger = logging.getLogger(__name__)

RESEARCH_SYSTEM = """You are a competitor intelligence researcher. Your job is to deeply analyze
a competitor's online presence and extract actionable marketing intelligence.

For each competitor, analyze and document:
- Homepage: headline, subheadline, value proposition, CTA
- Positioning: how they describe themselves, key differentiators they claim
- Pricing: tiers, pricing model, trial/freemium approach
- Features: main product claims
- Testimonials/Social proof: numbers, logos, case study angles
- Content: topics they cover, SEO keywords visible, content style
- Ad copy: any ad copy visible in search results
- Weaknesses: what they DON'T say, gaps in their positioning

Be specific and direct. This intelligence will inform all campaign creative work."""


DISCOVERY_SYSTEM = """You are a market research expert. Given a business brief and target personas,
identify the 3-5 most relevant direct competitors.

Output ONLY a structured list in this exact format:
## Discovered Competitors

1. **[Company Name]**
   - Website: [URL]
   - Why a competitor: [one sentence]

2. **[Company Name]**
   ...

Focus on DIRECT competitors (same product category, same target customer).
Do not include tangential or aspirational competitors."""


async def discover_competitors(brief: str, personas: str) -> list[dict[str, str]]:
    """Use Brave Search + Claude to discover 3-5 direct competitors from the brief."""
    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

    # Search for competitors
    search_query = f"competitors alternatives to {brief[:200]}"
    search_results = await brave_search(search_query, count=15)
    search_text = format_search_results(search_results)

    prompt = f"""Based on this business brief and search results, identify the 3-5 most direct competitors.

## Business Brief
{brief}

## Target Personas
{personas}

## Search Results
{search_text}

List the direct competitors with their websites."""

    message = await client.messages.create(
        model=MODELS["research"],
        max_tokens=1000,
        system=DISCOVERY_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    response = message.content[0].text
    competitors = []
    current = {}
    for line in response.split("\n"):
        line = line.strip()
        if line.startswith("**") and line.endswith("**"):
            if current:
                competitors.append(current)
            current = {"name": line.strip("*")}
        elif "Website:" in line:
            url = line.split("Website:", 1)[1].strip()
            current["url"] = url
        elif "Why a competitor:" in line:
            reason = line.split("Why a competitor:", 1)[1].strip()
            current["reason"] = reason
    if current and "name" in current:
        competitors.append(current)

    return competitors[:MAX_COMPETITORS]


async def research_competitor(competitor: dict, brand: str) -> str:
    """Scrape and analyze a single competitor. Returns markdown research report."""
    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    name = competitor.get("name", "Unknown")
    url = competitor.get("url", "")

    logger.info("Researching competitor: %s (%s)", name, url)

    # Fetch multiple pages
    pages_to_fetch = []
    if url:
        pages_to_fetch.append(url)
        pages_to_fetch.append(f"{url.rstrip('/')}/pricing")
        pages_to_fetch.append(f"{url.rstrip('/')}/blog")

    # Search for reviews and ads
    search_tasks = [
        brave_search(f"{name} reviews G2 Capterra", count=5),
        brave_search(f"{name} facebook ads 2026", count=5),
        brave_search(f"site:{url.replace('https://', '').replace('http://', '').split('/')[0]} case study" if url else f"{name} case study", count=5),
    ]

    fetch_tasks = [fetch_page(p, max_chars=3000) for p in pages_to_fetch[:2]]

    fetched, searched = await asyncio.gather(
        asyncio.gather(*fetch_tasks, return_exceptions=True),
        asyncio.gather(*search_tasks, return_exceptions=True),
    )

    # Compile all data
    raw_data = f"# Competitor Research: {name}\nURL: {url}\n\n"
    for i, (page, content) in enumerate(zip(pages_to_fetch[:2], fetched)):
        if isinstance(content, str):
            raw_data += f"## Page: {page}\n{content[:2000]}\n\n"

    for search_result in searched:
        if isinstance(search_result, list):
            raw_data += format_search_results(search_result[:3]) + "\n"

    # Analyze with Claude
    message = await client.messages.create(
        model=MODELS["research"],
        max_tokens=MAX_TOKENS["research"],
        system=RESEARCH_SYSTEM,
        messages=[{
            "role": "user",
            "content": f"Analyze this competitor for brand '{brand}':\n\n{raw_data}",
        }],
    )

    analysis = message.content[0].text
    return f"# Competitor: {name}\nURL: {url}\n\n{analysis}"


async def run(brand: str, brief: str, personas: str) -> list[dict]:
    """Main entry point. Discovers + researches all competitors for a brand."""
    cache = get_competitor_cache(brand)

    # Check cache for competitor list
    cached_competitors = cache.get("competitors_list")
    if cached_competitors:
        logger.info("[%s] Using cached competitor list", brand)
        competitors = cached_competitors
    else:
        logger.info("[%s] Discovering competitors from brief", brand)
        competitors = await discover_competitors(brief, personas)
        cache.set("competitors_list", competitors)

        # Save to clients/<brand>/competitors.md
        lines = ["# Discovered Competitors\n"]
        for c in competitors:
            lines.append(f"## {c.get('name', 'Unknown')}")
            lines.append(f"- **URL**: {c.get('url', 'Unknown')}")
            lines.append(f"- **Why direct competitor**: {c.get('reason', '')}")
            lines.append("")
        competitors_md = "\n".join(lines)
        client_path = Path("clients") / brand / "competitors.md"
        client_path.parent.mkdir(parents=True, exist_ok=True)
        client_path.write_text(competitors_md)
        logger.info("[%s] Saved %d competitors to clients/%s/competitors.md", brand, len(competitors), brand)

    # Research each competitor in parallel (with cache check)
    async def research_with_cache(competitor: dict) -> str:
        cache_key = f"research_{competitor.get('name', 'unknown').lower().replace(' ', '_')}"
        cached = cache.get(cache_key)
        if cached:
            logger.info("[%s] Using cached research for %s", brand, competitor.get("name"))
            return cached
        result = await research_competitor(competitor, brand)
        cache.set(cache_key, result)
        safe_name = competitor.get("name", "unknown").lower().replace(" ", "_")
        write_intel_file("competitor", brand, f"raw_research/{safe_name}.md", result)
        return result

    results = await asyncio.gather(
        *[research_with_cache(c) for c in competitors],
        return_exceptions=True,
    )

    successful = [r for r in results if isinstance(r, str)]
    logger.info("[%s] Researched %d/%d competitors", brand, len(successful), len(competitors))
    return competitors
