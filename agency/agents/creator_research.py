"""Content Intelligence Phase 1B — Creator Research Agent.

For each sub-niche, finds top 5 creators across Instagram, YouTube, TikTok, Facebook, LinkedIn.
Saves to content_intel/<brand>/creators/<sub_niche>.md
"""

import asyncio
import logging
import re
from pathlib import Path

import anthropic

from agency.config import ANTHROPIC_API_KEY, MODELS, MAX_TOKENS, PLATFORMS, MAX_CREATORS_PER_NICHE
from agency.cache import get_content_cache
from agency.tools.file_tools import write_intel_file, read_intel_file
from agency.tools.web_tools import brave_search, format_search_results

logger = logging.getLogger(__name__)

CREATOR_SYSTEM = """You are a social media research expert. Given search results for creators
in a specific niche on a specific platform, identify and profile the top creators.

For each creator, output:

### [Creator Name / Handle]
- **Platform**: [platform]
- **Handle/URL**: [handle or profile URL]
- **Estimated followers**: [number]
- **Content focus**: [what they mainly create]
- **Posting style**: [format they use most — reels, long-form video, carousels, text posts, etc.]
- **Why they're top**: [what makes them stand out in this niche]
- **Top content themes**: [3-5 recurring topics]

List the top {count} creators you can identify from the search results."""


async def research_creators_for_niche_platform(
    niche: str, platform: str, brand: str
) -> str:
    """Research top creators for one niche + platform combo."""
    query = f"top {niche} creators {platform} 2026"
    search_results = await brave_search(query, count=10)
    search_text = format_search_results(search_results)

    # Also search for specific platform handles
    query2 = f"best {niche} {platform} accounts follow"
    search_results2 = await brave_search(query2, count=8)
    search_text += "\n" + format_search_results(search_results2)

    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    message = await client.messages.create(
        model=MODELS["research"],
        max_tokens=2000,
        system=CREATOR_SYSTEM.format(count=MAX_CREATORS_PER_NICHE),
        messages=[{
            "role": "user",
            "content": f"""Find top {MAX_CREATORS_PER_NICHE} {niche} creators on {platform}:

## Search Results
{search_text}

List the top creators with their profiles.""",
        }],
    )
    return message.content[0].text


async def research_sub_niche(niche_name: str, brand: str) -> str:
    """Research top creators across all platforms for one sub-niche."""
    cache = get_content_cache(brand)
    safe_niche = niche_name.lower().replace(" ", "_").replace("/", "_")
    cache_key = f"creators_{safe_niche}"

    cached = cache.get(cache_key)
    if cached:
        logger.info("[%s] Using cached creator research for niche: %s", brand, niche_name)
        return cached

    logger.info("[%s] Researching creators for niche: %s", brand, niche_name)

    # Research all platforms in parallel
    platform_results = await asyncio.gather(
        *[research_creators_for_niche_platform(niche_name, platform, brand) for platform in PLATFORMS],
        return_exceptions=True,
    )

    lines = [f"# Top Creators — {niche_name}\n"]
    for platform, result in zip(PLATFORMS, platform_results):
        lines.append(f"## {platform.title()}")
        if isinstance(result, str):
            lines.append(result)
        else:
            lines.append(f"[Research failed: {result}]")
        lines.append("")

    content = "\n".join(lines)
    write_intel_file("content", brand, f"creators/{safe_niche}.md", content)
    cache.set(cache_key, content)
    return content


def parse_sub_niches(niches_content: str) -> list[str]:
    """Extract sub-niche names from niches.md content."""
    niches = []
    for line in niches_content.split("\n"):
        # Match lines like "1. **Sub-niche name**"
        match = re.match(r"\d+\.\s+\*\*([^*]+)\*\*", line.strip())
        if match:
            niches.append(match.group(1).strip())
    return niches[:5]  # Max 5 sub-niches


async def run(brand: str) -> list[str]:
    """Research creators for all sub-niches of a brand."""
    niches_content = read_intel_file("content", brand, "niches.md")
    if not niches_content:
        logger.warning("[%s] No niches.md found — run niche_research first", brand)
        return []

    sub_niches = parse_sub_niches(niches_content)
    if not sub_niches:
        logger.warning("[%s] Could not parse sub-niches from niches.md", brand)
        return []

    logger.info("[%s] Researching creators for %d sub-niches", brand, len(sub_niches))

    # Research all sub-niches in parallel
    await asyncio.gather(
        *[research_sub_niche(niche, brand) for niche in sub_niches],
        return_exceptions=True,
    )

    return sub_niches
