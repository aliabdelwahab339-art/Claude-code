"""Creative Phase — Ad Campaigns Agent.

Generates 10 Google Search Ads + 10 Meta Ads using meta_ads_analysis.md intelligence.
Uses the Batches API for the 20 variations (non-urgent, bulk work).
"""

import logging

import anthropic

from agency.config import ANTHROPIC_API_KEY, MODELS, MAX_TOKENS
from agency.batch import MarketingBatch, BatchJob

logger = logging.getLogger(__name__)

AD_SYSTEM = """You are an expert performance marketer specializing in Google Search and Meta ads.
You create ads that outperform competitors by:
- Using hook angles competitors haven't tested
- Addressing pain points more specifically
- Making offers that stand out
- Writing copy that speaks to the exact ICP language

You know what the competitors are running and you deliberately do something different."""


async def run(brand: str, brief: str, intel: dict) -> str:
    """Generate 10 Google + 10 Meta ad variations using competitor ad intelligence."""
    meta_ads_intel = intel.get("meta_ads_intel", "")
    competitor_intel = intel.get("competitor_intel", "")
    frameworks = intel.get("frameworks", "")
    personas = intel.get("personas", "")
    pain_points = intel.get("pain_points", "")

    intel_summary = f"""## Competitor Ad Patterns (avoid these — they're saturated)
{meta_ads_intel[:2000] if meta_ads_intel else competitor_intel[:1500] if competitor_intel else 'Not available'}

## Target Personas
{personas}

## Core Pain Points
{pain_points}"""

    if frameworks:
        intel_summary += f"\n\n## Owner's Frameworks\n{frameworks[:800]}"

    # Use batch API for the 20 ad variations
    batch = MarketingBatch()

    google_system = f"""{AD_SYSTEM}

You are writing Google Search Ads. Format each ad as:
**Headline 1** (30 chars max): [text]
**Headline 2** (30 chars max): [text]
**Headline 3** (30 chars max): [text]
**Description 1** (90 chars max): [text]
**Description 2** (90 chars max): [text]
**Display URL**: [brand.com/path]
**Target keyword**: [main keyword this ad targets]
**Angle**: [what makes this ad unique vs. competitors]"""

    meta_system = f"""{AD_SYSTEM}

You are writing Meta/Facebook Ads. Format each ad as:
**Hook** (first line, stops scroll): [text]
**Primary Text** (full ad copy, 125 chars optimal): [text]
**Headline** (27 chars max): [text]
**Description** (30 chars max): [text]
**CTA Button**: [Shop Now / Learn More / Sign Up / etc.]
**Format**: [Image / Video / Carousel]
**Target Persona**: [who this is for]
**Offer**: [what's being offered]
**Angle**: [pain/gain/fear/aspiration/social proof]"""

    jobs = []
    for i in range(1, 11):
        jobs.append(BatchJob(
            custom_id=f"{brand}_google_{i}",
            prompt=f"Write Google Search Ad #{i} for {brand}.\n\nBrief: {brief[:300]}\n\n{intel_summary}\n\nUse a unique angle — variation #{i} of 10.",
            system=google_system,
            max_tokens=400,
        ))
    for i in range(1, 11):
        jobs.append(BatchJob(
            custom_id=f"{brand}_meta_{i}",
            prompt=f"Write Meta/Facebook Ad #{i} for {brand}.\n\nBrief: {brief[:300]}\n\n{intel_summary}\n\nUse a unique angle — variation #{i} of 10.",
            system=meta_system,
            max_tokens=500,
        ))

    try:
        logger.info("[%s] Submitting 20-ad batch to Anthropic Batches API", brand)
        results = await batch.run_batch_async(jobs)
        logger.info("[%s] Batch complete — %d results", brand, len(results))
    except Exception as exc:
        logger.warning("[%s] Batch API failed (%s) — falling back to sequential", brand, exc)
        # Fallback: generate inline if batch fails
        return await _run_sequential(brand, brief, intel_summary)

    # Assemble output
    lines = [f"# Ad Campaigns — {brand}", ""]
    lines.append("## Google Search Ads (10 Variations)")
    lines.append("")
    for i in range(1, 11):
        key = f"{brand}_google_{i}"
        lines.append(f"### Google Ad #{i}")
        lines.append(results.get(key, "[generation failed]"))
        lines.append("")

    lines.append("## Meta/Facebook Ads (10 Variations)")
    lines.append("")
    for i in range(1, 11):
        key = f"{brand}_meta_{i}"
        lines.append(f"### Meta Ad #{i}")
        lines.append(results.get(key, "[generation failed]"))
        lines.append("")

    return "\n".join(lines)


async def _run_sequential(brand: str, brief: str, intel_summary: str) -> str:
    """Fallback: generate all ads sequentially without Batches API."""
    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""Create 10 Google Search Ads and 10 Meta/Facebook Ads for brand: {brand}

## Brief
{brief[:500]}

{intel_summary}

## Google Search Ads (10 variations — each with unique angle)
[Format: Headline 1/2/3 + Description 1/2 + target keyword + angle]

## Meta/Facebook Ads (10 variations — each with unique angle)
[Format: Hook + Primary Text + Headline + Description + CTA + Format + Persona + Offer + Angle]"""

    message = await client.messages.create(
        model=MODELS["specialists"],
        max_tokens=MAX_TOKENS["specialists"],
        system=AD_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    result = message.content[0].text
    logger.info("[%s] Ad campaigns (sequential) complete (%d chars)", brand, len(result))
    return f"# Ad Campaigns — {brand}\n\n{result}"
