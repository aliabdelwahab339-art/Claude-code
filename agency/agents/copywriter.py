"""Creative Phase — Copywriter Agent.

Generates differentiated copy using competitor intel + content preferences + personal frameworks.
"""

import logging

import anthropic

from agency.config import ANTHROPIC_API_KEY, MODELS, MAX_TOKENS

logger = logging.getLogger(__name__)

COPYWRITER_SYSTEM = """You are a world-class direct-response copywriter. You write copy that:
- Leads with a specific pain point or desire (never generic)
- Uses the brand's unique mechanism as the differentiator
- Avoids clichés and overused phrases from competitors
- Speaks directly to the ICP in their own language
- Has clear, compelling CTAs

You are guided by the owner's personal frameworks and mental models — all copy must reflect
their worldview and principles."""


async def run(brand: str, brief: str, intel: dict) -> str:
    """Generate full copy suite: headlines, email sequences, landing page copy."""
    frameworks = intel.get("frameworks", "")
    competitor_intel = intel.get("competitor_intel", "")
    content_prefs = intel.get("content_preferences", "")
    brand_guidelines = intel.get("brand_guidelines", "")
    personas = intel.get("personas", "")
    pain_points = intel.get("pain_points", "")
    case_studies = intel.get("case_studies", "")

    system = COPYWRITER_SYSTEM
    if frameworks:
        system += f"\n\n## Owner's Personal Frameworks\n{frameworks[:1500]}"

    prompt = f"""Write a complete copy suite for brand: {brand}

## Business Brief
{brief}

## Target Personas
{personas}

## Core Pain Points
{pain_points}

## Case Studies / Proof Points
{case_studies}

## Brand Guidelines
{brand_guidelines}

## Competitive Intelligence (avoid these patterns)
{competitor_intel[:2000] if competitor_intel else 'Not available'}

## Content Preferences (hooks that work in this niche)
{content_prefs[:1500] if content_prefs else 'Not available'}

---

Deliver:

# Copy Suite — {brand}

## 1. Headlines (10 variations)
[10 headlines that differentiate from competitors]

## 2. Subheadlines (5 variations)
[5 supporting subheadlines]

## 3. Hero Section Copy
[Full above-the-fold copy: headline + subheadline + bullet points + CTA]

## 4. Value Proposition Statement
[One paragraph, the brand's core positioning statement]

## 5. Email Subject Lines (10 variations)
[10 subject lines for cold and warm outreach]

## 6. Welcome Email
[Full welcome email sequence — email 1 of 5]

## 7. Pain Point Copy Blocks (one per pain point)
[Copy addressing each core pain point]

## 8. Testimonial Framing Templates
[3 templates for turning case studies into compelling testimonials]

## 9. CTA Variations (10)
[10 CTA button texts and supporting copy]

## 10. Tagline Options (5)
[5 short, memorable taglines]"""

    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    message = await client.messages.create(
        model=MODELS["specialists"],
        max_tokens=MAX_TOKENS["specialists"],
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )

    result = message.content[0].text
    logger.info("[%s] Copywriter complete (%d chars)", brand, len(result))
    return result
