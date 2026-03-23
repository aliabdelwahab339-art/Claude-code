"""Content Intelligence Phase 1C — Content Analysis Agent.

Reads all creator research files, applies platform performance thresholds,
and synthesizes into content_preferences.md with top performing links.
"""

import logging
from pathlib import Path

import anthropic

from agency.config import ANTHROPIC_API_KEY, MODELS, MAX_TOKENS, PLATFORM_THRESHOLDS
from agency.tools.file_tools import write_intel_file, read_intel_file

logger = logging.getLogger(__name__)

CONTENT_ANALYSIS_SYSTEM = """You are a content performance analyst. You've been given creator
research across multiple niches and platforms. Your job is to identify content patterns
and produce a master content preferences document.

Apply these platform performance thresholds when identifying "top performing" content:
- Instagram: Views ≥ 5–10× follower count
- YouTube: Views ≥ 2–3× the channel's median view count (top 20%)
- TikTok: Views ≥ 10× follower count, or FYP indicator
- Facebook: Engagement (reactions + comments + shares) ≥ 3–5% of page likes
- LinkedIn: Engagement rate ≥ 5% (vs 2% platform average), or comments ≥ 50

Output EXACTLY in this format:

## Top Performing Links by Platform

### Instagram
- [URL or post description] — [topic] — Hook: "[hook]" — Why it worked: [reason]
[repeat for each top post found]

### YouTube
[same format]

### TikTok
[same format]

### Facebook
[same format]

### LinkedIn
[same format]

## Recurring Patterns

### Topics That Perform
- [topic pattern]
[list all]

### Hooks That Work
- [hook formula or example]
[list all]

### Dominant Formats
- [format + why it works in this niche]
[list all]

### Posting Patterns
- [cadence, timing, frequency observations]

## Content Gaps & Opportunities
- [topic/angle no top creator has covered well]
[list all gaps]

## Recommended Content Strategy
[3-5 bullet points on how to use this intelligence to create content that outperforms competitors]"""


async def run(brand: str) -> str:
    """Synthesize all creator research into content_preferences.md."""
    # Read all creator files
    creators_dir = Path("content_intel") / brand / "creators"
    if not creators_dir.exists():
        logger.warning("[%s] No creator research files found", brand)
        return ""

    all_creator_data = ""
    for creator_file in sorted(creators_dir.glob("*.md")):
        all_creator_data += f"\n\n{'='*60}\n"
        all_creator_data += creator_file.read_text()

    if not all_creator_data.strip():
        logger.warning("[%s] Creator research files are empty", brand)
        return ""

    logger.info("[%s] Analyzing content from creator research files", brand)

    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    message = await client.messages.create(
        model=MODELS["analysis"],
        max_tokens=MAX_TOKENS["analysis"],
        system=CONTENT_ANALYSIS_SYSTEM,
        messages=[{
            "role": "user",
            "content": f"""Analyze this creator research for brand '{brand}' and create the content preferences document.

Platform performance thresholds to apply:
- Instagram: views ≥ 5-10× followers
- YouTube: views ≥ 2-3× channel median
- TikTok: views ≥ 10× followers or FYP
- Facebook: engagement ≥ 3-5% of page likes
- LinkedIn: engagement rate ≥ 5% or comments ≥ 50

## Creator Research
{all_creator_data[:15000]}""",
        }],
    )

    analysis = message.content[0].text
    content = f"# Content Preferences — {brand}\n\n{analysis}"

    write_intel_file("content", brand, "content_preferences.md", content)
    logger.info("[%s] Content preferences document saved", brand)
    return content
