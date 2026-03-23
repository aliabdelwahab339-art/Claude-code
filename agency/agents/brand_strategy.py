"""Creative Phase — Brand Strategy Agent.

Develops positioning strategy using all intel reports.
Exploits competitor weaknesses identified in analysis.
"""

import logging

import anthropic

from agency.config import ANTHROPIC_API_KEY, MODELS, MAX_TOKENS

logger = logging.getLogger(__name__)

BRAND_STRATEGY_SYSTEM = """You are a brand strategist with deep expertise in positioning,
differentiation, and category design. You help brands win by:
- Finding the positioning space competitors don't own
- Creating a distinctive point of view
- Building a brand that attracts the right customers and repels the wrong ones
- Connecting the brand story to the founder's vision and frameworks

You base all strategy on competitive intelligence — you know what competitors claim
and you deliberately position the brand to own different ground."""


async def run(brand: str, brief: str, intel: dict) -> str:
    """Generate brand positioning strategy and identity framework."""
    competitor_intel = intel.get("competitor_intel", "")
    meta_ads_intel = intel.get("meta_ads_intel", "")
    content_prefs = intel.get("content_preferences", "")
    frameworks = intel.get("frameworks", "")
    personas = intel.get("personas", "")
    pain_points = intel.get("pain_points", "")
    case_studies = intel.get("case_studies", "")
    brand_guidelines = intel.get("brand_guidelines", "")

    system = BRAND_STRATEGY_SYSTEM
    if frameworks:
        system += f"\n\n## Owner's Personal Frameworks (brand strategy must reflect these)\n{frameworks[:1500]}"

    prompt = f"""Develop a complete brand strategy for: {brand}

## Business Brief
{brief}

## Target Personas
{personas}

## Pain Points
{pain_points}

## Case Studies / Proof
{case_studies}

## Existing Brand Guidelines
{brand_guidelines}

## Competitive Intelligence
{competitor_intel[:2000] if competitor_intel else 'Not available'}

## Competitor Ad Positioning
{meta_ads_intel[:1000] if meta_ads_intel else 'Not available'}

---

Deliver:

# Brand Strategy — {brand}

## 1. Positioning Statement
[Classic format: For [persona] who [need], [Brand] is the [category] that [key benefit] because [proof/reason to believe]]

## 2. Category Design
[What category does this brand own or create? How do you change the competitive conversation?]

## 3. Brand Differentiation Map
| Attribute | Competitor 1 | Competitor 2 | Competitor 3 | {brand} |
|---|---|---|---|---|
[Map where each player sits on 6-8 key attributes — highlight {brand}'s white space]

## 4. Brand Voice & Tone
- **Voice**: [3 adjectives]
- **Tone**: [how it adjusts — formal vs. casual, expert vs. peer]
- **What we say**: [core messages]
- **What we never say**: [phrases/claims to avoid — especially competitor clichés]
- **Writing principles**: [3-5 rules for all copy]

## 5. Brand Story
[The founder/brand origin story — why this company exists, the problem they've lived]

## 6. Messaging Architecture
### Primary Message (one sentence)
[Core value proposition]

### Supporting Messages (5 pillars)
1. [Pillar 1: claim + proof]
2. [Pillar 2]
3. [Pillar 3]
4. [Pillar 4]
5. [Pillar 5]

## 7. ICP Narrative
[Write the day-in-the-life of the ideal customer — their pain, their search, their transformation]

## 8. Go-To-Market Positioning
[Which channels, which messages, which audiences to prioritize first and why]

## 9. Strategic Recommendations
[Top 5 brand-level moves to make in the next 90 days to build a distinctive market position]"""

    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    message = await client.messages.create(
        model=MODELS["specialists"],
        max_tokens=MAX_TOKENS["specialists"],
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )

    result = message.content[0].text
    logger.info("[%s] Brand strategy complete (%d chars)", brand, len(result))
    return result
