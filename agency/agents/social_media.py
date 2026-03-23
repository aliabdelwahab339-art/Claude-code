"""Creative Phase — Social Media Agent.

Generates 30 platform-specific posts using content_preferences.md intelligence.
"""

import logging

import anthropic

from agency.config import ANTHROPIC_API_KEY, MODELS, MAX_TOKENS

logger = logging.getLogger(__name__)

SOCIAL_SYSTEM = """You are a social media content strategist and copywriter. You create
high-performing organic social content based on what actually works in the niche.

You study what top creators do and then create content that:
- Uses proven hook formulas from the niche (adapted, not copied)
- Targets the sub-niches where the brand's audience lives
- Matches the formats that perform best per platform
- Has a distinctive point of view — the owner's frameworks and perspective

You write for humans, not algorithms. Compelling content earns reach."""


async def run(brand: str, brief: str, intel: dict) -> str:
    """Generate 30 social media posts across platforms."""
    content_prefs = intel.get("content_preferences", "")
    frameworks = intel.get("frameworks", "")
    competitor_intel = intel.get("competitor_intel", "")
    personas = intel.get("personas", "")

    system = SOCIAL_SYSTEM
    if frameworks:
        system += f"\n\n## Owner's Personal Frameworks (all content must reflect these)\n{frameworks[:1500]}"

    prompt = f"""Create a 30-post social media content calendar for brand: {brand}

## Business Brief
{brief}

## Target Personas
{personas}

## Content Preferences (what performs in this niche)
{content_prefs[:3000] if content_prefs else 'Not available'}

## Competitor Intel (angles to AVOID — already saturated)
{competitor_intel[:1000] if competitor_intel else 'Not available'}

---

Create 30 posts across platforms (6 per platform):

# Social Media Content — {brand}

## Instagram (6 posts)
[For each post:]
### Post [N] — [format: Reel/Carousel/Static]
**Hook**: [first line — must stop the scroll]
**Caption**: [full caption including hook, body, CTA]
**Hashtags**: [10-15 relevant hashtags]
**Visual Direction**: [what the image/video should show]
**Why this will perform**: [based on content preferences data]

## YouTube (6 posts — shorts + long-form)
[For each:]
### Video [N] — [format: Short/Long-form] — [duration]
**Title**: [SEO-optimized, click-worthy]
**Hook (first 3 seconds)**: [exact words]
**Script outline**: [intro, sections, CTA]
**Thumbnail concept**: [description]

## TikTok (6 posts)
[Same format as Instagram but TikTok-native style]

## LinkedIn (6 posts)
[For each:]
### Post [N] — [format: Text/Carousel/Video]
**Opening line**: [hook — no "Excited to share" opener]
**Body**: [full post — professional but human]
**CTA**: [call to action]

## Facebook (6 posts)
[Community/group-oriented content]

## Content Calendar Schedule
[Recommended posting schedule across all 5 platforms for 2 weeks]"""

    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    message = await client.messages.create(
        model=MODELS["specialists"],
        max_tokens=MAX_TOKENS["specialists"],
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )

    result = message.content[0].text
    logger.info("[%s] Social media content complete (%d chars)", brand, len(result))
    return result
