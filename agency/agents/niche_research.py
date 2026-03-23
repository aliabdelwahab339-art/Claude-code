"""Content Intelligence Phase 1A — Niche Research Agent.

Maps the main niche and 5 sub-niches from the brand context.
Saves to content_intel/<brand>/niches.md
"""

import logging

import anthropic

from agency.config import ANTHROPIC_API_KEY, MODELS, MAX_TOKENS, MAX_SUB_NICHES
from agency.cache import get_content_cache
from agency.tools.file_tools import write_intel_file
from agency.tools.web_tools import brave_search, format_search_results

logger = logging.getLogger(__name__)

NICHE_SYSTEM = """You are a content strategy expert. Given a business brief and target personas,
map the brand's content niche landscape.

Output EXACTLY in this format:

## Main Niche
[One clear niche label, e.g. "B2B SaaS Productivity Tools"]

## 5 Sub-Niches
1. **[Sub-niche name]** — [one sentence explanation + why this audience cares about this brand]
2. **[Sub-niche name]** — [explanation]
3. **[Sub-niche name]** — [explanation]
4. **[Sub-niche name]** — [explanation]
5. **[Sub-niche name]** — [explanation]

## Content Opportunity Summary
[2-3 sentences on the biggest content opportunities in this niche landscape]

Sub-niches should be:
- Specific enough to find dedicated creators and communities
- Broad enough to have an active creator ecosystem
- Directly relevant to the brand's target personas"""


async def run(brand: str, brief: str, personas: str) -> str:
    """Map main niche + 5 sub-niches for a brand."""
    cache = get_content_cache(brand)
    cached = cache.get("niches")
    if cached:
        logger.info("[%s] Using cached niche research", brand)
        return cached

    # Search for market context
    search_results = await brave_search(f"{brief[:100]} market niche content creators 2026", count=8)
    search_text = format_search_results(search_results)

    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    message = await client.messages.create(
        model=MODELS["research"],
        max_tokens=MAX_TOKENS["research"],
        system=NICHE_SYSTEM,
        messages=[{
            "role": "user",
            "content": f"""Map the content niches for this brand:

## Business Brief
{brief}

## Target Personas
{personas}

## Market Context (search results)
{search_text}""",
        }],
    )

    result = message.content[0].text
    content = f"# Niche Map — {brand}\n\n{result}"

    write_intel_file("content", brand, "niches.md", content)
    cache.set("niches", content)
    logger.info("[%s] Niche research saved", brand)
    return content
