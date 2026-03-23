"""Creative Phase — SEO Agent.

Targets keyword gaps from competitor analysis. Generates keyword strategy,
meta tags, content briefs for blog posts, and site architecture recommendations.
"""

import logging

import anthropic

from agency.config import ANTHROPIC_API_KEY, MODELS, MAX_TOKENS

logger = logging.getLogger(__name__)

SEO_SYSTEM = """You are a senior SEO strategist specializing in content-driven organic growth.
You identify keyword gaps competitors are missing and build content strategies that capture
high-intent traffic. You think in terms of search intent, topic clusters, and conversion paths."""


async def run(brand: str, brief: str, intel: dict) -> str:
    """Generate SEO strategy, keyword targets, meta tags, and content briefs."""
    competitor_intel = intel.get("competitor_intel", "")
    frameworks = intel.get("frameworks", "")
    personas = intel.get("personas", "")

    prompt = f"""Create a complete SEO strategy for brand: {brand}

## Business Brief
{brief}

## Target Personas
{personas}

## Competitor Intelligence (keyword gaps to exploit)
{competitor_intel[:3000] if competitor_intel else 'Not available'}

---

Deliver:

# SEO Strategy — {brand}

## 1. Primary Keywords (10)
| Keyword | Monthly Volume (est.) | Difficulty | Intent | Why We Target It |
|---|---|---|---|---|
[10 rows]

## 2. Long-Tail Keywords (20)
[20 long-tail keywords with intent labels]

## 3. Competitor Keyword Gaps
[Keywords competitors rank for that we should target — derived from intel]

## 4. Topic Clusters (3 pillars)
### Pillar 1: [Topic]
- Pillar page: [title + target keyword]
- Cluster pages: [5 supporting articles]

### Pillar 2: [Topic]
[same]

### Pillar 3: [Topic]
[same]

## 5. Meta Tags (Homepage + 5 key pages)
### Homepage
- Title: [60 chars max]
- Description: [155 chars max]

[repeat for each page]

## 6. Blog Post Briefs (5 posts targeting keyword gaps)
### Post 1: [Title]
- Target keyword: [keyword]
- Search intent: [informational/navigational/transactional]
- Outline: [H2s + H3s]
- Word count target: [N]
- Key differentiator vs. competitor content: [what makes ours better]

[repeat × 5]

## 7. Internal Linking Strategy
[How to structure internal links across pillar + cluster pages]

## 8. Featured Snippet Opportunities
[5 queries we can optimize for featured snippets]"""

    system = SEO_SYSTEM
    if frameworks:
        system += f"\n\n## Owner's Frameworks (apply to content angles)\n{frameworks[:800]}"

    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    message = await client.messages.create(
        model=MODELS["specialists"],
        max_tokens=MAX_TOKENS["specialists"],
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )

    result = message.content[0].text
    logger.info("[%s] SEO strategy complete (%d chars)", brand, len(result))
    return result
