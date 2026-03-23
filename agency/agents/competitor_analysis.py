"""Phase 1B — Competitor Analysis Agent.

Reads all raw_research/*.md files and synthesizes into analysis_report.md:
- Positioning map, messaging patterns, keyword gaps, ad patterns,
  content gaps, pricing intelligence, SWOT, strategic recommendations
"""

import logging
from pathlib import Path

import anthropic

from agency.config import ANTHROPIC_API_KEY, MODELS, MAX_TOKENS
from agency.tools.file_tools import list_raw_research_files, write_intel_file

logger = logging.getLogger(__name__)

ANALYSIS_SYSTEM = """You are a senior marketing strategist. You have just received raw competitor
research reports. Your job is to synthesize them into a strategic intelligence report.

This report will be read by copywriters, SEO strategists, social media managers, ad campaign
managers, and brand strategists. It must be actionable — not just descriptive.

Structure your output EXACTLY as:

## Positioning Map
[Where each competitor sits: premium vs. budget, enterprise vs. SMB, simple vs. full-featured, etc.]

## Messaging Patterns
[Common claims across competitors, overused buzzwords to AVOID, differentiation angles that are open]

## Keyword Gaps
[Terms competitors rank for that represent SEO opportunities. Format: keyword → why it's valuable]

## Ad Creative Patterns
[Headline formulas used, CTA styles, offer types, what emotions they target]

## Content Gaps
[Topics competitors publish about, AND topics they DON'T cover (your opportunities)]

## Pricing Intelligence
[Pricing tiers, anchoring strategies, trial/freemium approaches, pricing page patterns]

## SWOT Analysis
### vs. [Competitor 1]
- **Strengths**: [your advantages]
- **Weaknesses**: [your gaps]
- **Opportunities**: [angles you can win on]
- **Threats**: [risks]

[Repeat for each competitor]

## Strategic Recommendations
1. [Top opportunity — specific and actionable]
2. [Second opportunity]
3. [Third opportunity]
4. [Fourth opportunity]
5. [Fifth opportunity]"""


async def run(brand: str) -> str:
    """Synthesize all raw competitor research into a strategic analysis report."""
    raw_files = list_raw_research_files(brand)
    if not raw_files:
        logger.warning("[%s] No raw research files found for competitor analysis", brand)
        return ""

    # Read all raw research
    all_research = ""
    for path in raw_files:
        all_research += f"\n\n{'='*60}\n"
        all_research += path.read_text()

    logger.info("[%s] Analyzing %d competitor research files", brand, len(raw_files))

    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    message = await client.messages.create(
        model=MODELS["analysis"],
        max_tokens=MAX_TOKENS["analysis"],
        system=ANALYSIS_SYSTEM,
        messages=[{
            "role": "user",
            "content": f"Synthesize this competitor research for brand '{brand}' into a strategic intelligence report:\n\n{all_research[:15000]}",
        }],
    )

    analysis = message.content[0].text
    report = f"# Competitor Intelligence Report — {brand}\n\n{analysis}"

    write_intel_file("competitor", brand, "analysis_report.md", report)
    logger.info("[%s] Competitor analysis report saved", brand)
    return report
