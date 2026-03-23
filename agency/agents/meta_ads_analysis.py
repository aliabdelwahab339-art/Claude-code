"""Content Intelligence Phase 1D — Meta Ads Analysis Agent.

Scrapes Meta/Facebook Ads Library for each competitor and produces
a structured breakdown: hook, persona, pain, offer, format, CTA, social proof, duration.
"""

import asyncio
import logging
from pathlib import Path

import anthropic

from agency.config import ANTHROPIC_API_KEY, MODELS, MAX_TOKENS
from agency.tools.file_tools import write_intel_file, read_intel_file
from agency.tools.web_tools import brave_search, fetch_page, format_search_results

logger = logging.getLogger(__name__)

ADS_ANALYSIS_SYSTEM = """You are a paid advertising intelligence analyst. You've been given
data about a competitor's Facebook/Meta ads. Extract and categorize every ad you can find.

For each ad, create a structured breakdown:

### Ad [N]: [brief description]
| Field | Content |
|---|---|
| **Hook** | [first line of copy or first frame description] |
| **Persona** | [who this targets — job title, life stage, pain profile] |
| **Pain Point** | [specific problem the ad leads with] |
| **Offer** | [what's being offered — free trial, demo, discount, lead magnet] |
| **Format** | [Image / Video / Carousel / Story / UGC-style / Testimonial] |
| **CTA** | [button text + destination] |
| **Social Proof** | [reviews, numbers, logos used] |
| **Running Duration** | [how long active — older = likely winning] |
| **Messaging Angle** | [pain / gain / fear / aspiration / social proof] |

After all ads, add:

## Winning Ad Patterns
- **Hook formulas used most**: [list]
- **Most common offer type**: [list]
- **Dominant formats**: [list]
- **CTA patterns**: [list]
- **Emotional triggers**: [list]

## Competitor Weaknesses in Ads
- [gaps, missing angles, weak copy areas you can exploit]

## Opportunities for [Brand]
- **Untested hook angles**: [list]
- **Offers competitors aren't making**: [list]
- **Formats no one is using well**: [list]
- **Audiences being ignored**: [list]"""


async def fetch_competitor_ads(competitor_name: str, competitor_url: str = "") -> str:
    """Fetch Meta Ads Library data for one competitor."""
    # Method 1: Direct ads library URL
    ads_library_url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=ALL&q={competitor_name}"

    # Method 2: Search for ad screenshots and breakdowns
    search_tasks = [
        brave_search(f"{competitor_name} facebook ads 2026 examples", count=8),
        brave_search(f"{competitor_name} meta ads library active", count=5),
        brave_search(f"{competitor_name} facebook advertising copy hooks", count=5),
    ]

    search_results_list = await asyncio.gather(*search_tasks, return_exceptions=True)

    combined_search = ""
    for results in search_results_list:
        if isinstance(results, list):
            combined_search += format_search_results(results) + "\n"

    # Try fetching the ads library page
    ads_page_content = await fetch_page(ads_library_url, max_chars=4000)

    return f"""## Competitor: {competitor_name}
Ads Library URL: {ads_library_url}

### Ads Library Content
{ads_page_content}

### Search Intelligence
{combined_search[:3000]}"""


async def run(brand: str, brief: str) -> str:
    """Analyze Meta ads for all discovered competitors."""
    # Read competitor list
    competitors_content = read_intel_file("", brand, "").strip() or ""
    client_competitors_path = Path("clients") / brand / "competitors.md"

    competitors: list[dict] = []
    if client_competitors_path.exists():
        comp_content = client_competitors_path.read_text()
        # Parse competitors from markdown
        current: dict = {}
        for line in comp_content.split("\n"):
            if line.startswith("## "):
                if current:
                    competitors.append(current)
                current = {"name": line[3:].strip()}
            elif "**URL**:" in line:
                current["url"] = line.split("**URL**:", 1)[1].strip()
        if current and "name" in current:
            competitors.append(current)

    if not competitors:
        logger.warning("[%s] No competitors found for Meta ads analysis", brand)
        return ""

    logger.info("[%s] Analyzing Meta ads for %d competitors", brand, len(competitors))

    # Fetch all competitor ads in parallel
    ad_data_list = await asyncio.gather(
        *[fetch_competitor_ads(c.get("name", ""), c.get("url", "")) for c in competitors],
        return_exceptions=True,
    )

    all_ad_data = ""
    for competitor, data in zip(competitors, ad_data_list):
        if isinstance(data, str):
            all_ad_data += f"\n\n{'='*60}\n{data}"

    if not all_ad_data.strip():
        return ""

    # Analyze with Claude
    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    message = await client.messages.create(
        model=MODELS["analysis"],
        max_tokens=MAX_TOKENS["analysis"],
        system=ADS_ANALYSIS_SYSTEM.replace("[Brand]", brand),
        messages=[{
            "role": "user",
            "content": f"""Analyze the Meta ads data for brand '{brand}' competitors.
Extract every ad you can identify and provide a full breakdown.

## Raw Ads Data
{all_ad_data[:14000]}""",
        }],
    )

    analysis = message.content[0].text
    report = f"# Meta Ads Intelligence — {brand}\n\n{analysis}"

    write_intel_file("competitor", brand, "meta_ads_analysis.md", report)
    logger.info("[%s] Meta ads analysis saved", brand)
    return report
