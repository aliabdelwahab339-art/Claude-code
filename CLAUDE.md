# AI-Native Marketing Agency

You are operating inside a fully autonomous AI marketing agency system. Read this file carefully before doing any work.

## What This System Does

This agency generates full marketing campaigns using specialized AI agents working in parallel. It handles:
- Competitor research & analysis (with Meta Ads Library scraping)
- Niche mapping + top creator research across all platforms
- Content intelligence (top performing posts with platform-specific thresholds)
- Copywriting, SEO, social media content, ad campaigns, brand strategy
- Full campaign delivery with structured outputs

## Directory Layout

```
clients/<brand>/          — Brand guidelines, audience, competitors
competitor_intel/<brand>/ — Scraped competitor data + analysis reports
content_intel/<brand>/    — Niche map, creator research, content preferences
outputs/<brand>/<date>/   — Final campaign deliverables
templates/                — Content format templates
agency/                   — Python multi-agent system
.claude/commands/         — Custom slash commands (skills)
.agents/                  — Foundation context + marketingskills submodule
```

## Agent Roles

| Agent | Responsibility |
|---|---|
| Orchestrator | CEO — decomposes briefs, routes work, assembles deliverables |
| Competitor Research | Scrapes each competitor (homepage, pricing, blog, ads, reviews) |
| Competitor Analysis | Synthesizes raw research → SWOT, keyword gaps, positioning map |
| Meta Ads Analysis | Scrapes Meta Ads Library → hook, persona, pain, offer, format, CTA |
| Niche Research | Maps main niche + 5 sub-niches from brand context |
| Creator Research | Finds top 5 creators per sub-niche × platform |
| Content Analysis | Identifies top posts by platform threshold → content_preferences.md |
| Copywriter | Headlines, body copy, CTAs — informed by all intel |
| SEO Agent | Keywords, meta descriptions — targets competitor gaps |
| Social Media | 30 posts per campaign across IG/YT/TikTok/FB/LI |
| Ad Campaigns | 10 Google + 10 Meta variants — informed by Meta Ads intel |
| Analytics | Interprets GA4 data, surfaces optimization insights |
| Brand Strategy | Positioning, messaging framework — exploits competitor gaps |
| Validator | Quality checks every output against brand voice + intel |

## Execution Order (MUST FOLLOW)

```
Phase 1A: Competitor Research (parallel × N competitors)
Phase 1A: Niche Research      (parallel with 1A)
        ↓ (both complete)
Phase 1B: Competitor Analysis (sequential — needs 1A done)
Phase 1B: Creator Research    (parallel × 5 sub-niches)
        ↓ (both complete)
Phase 1C: Content Analysis    (sequential — needs creator data)
Phase 1C: Meta Ads Analysis   (sequential — needs competitor data)
        ↓ (all intel complete)
Phase 2:  All creative agents (fully parallel — all receive intel)
        ↓
Phase 3:  Validator + Assembler → outputs/<brand>/<date>/
```

## Output Conventions

- Always save deliverables to `outputs/<brand>/<YYYY-MM-DD>/`
- Structure: `intelligence/`, `copy/`, `seo/`, `social/`, `ads/`, `strategy/`
- Always write a `campaign_summary.md` linking all deliverables
- Competitor intel cached in `competitor_intel/<brand>/` — check cache before re-researching (7-day TTL)
- Content intel cached in `content_intel/<brand>/` — check cache before re-researching (30-day TTL)

## Scalability Rules

- NEVER block on a single client — all client campaigns run concurrently
- Use Anthropic Batches API for bulk non-urgent tasks (ad variations, SEO keywords)
- Semaphore limits: max 10 concurrent API calls per client, max 50 system-wide
- Cache all intel — never re-scrape if cache is fresh
- Each client is fully isolated — zero shared mutable state

## Platform Performance Thresholds (Top Performing Content)

| Platform | Threshold |
|---|---|
| Instagram | Views ≥ 5–10× follower count |
| YouTube | Views ≥ 2–3× channel median (top 20%) |
| TikTok | Views ≥ 10× follower count |
| Facebook | Engagement ≥ 3–5% of page likes |
| LinkedIn | Engagement rate ≥ 5%, or comments ≥ 50 |

## Available Skills (slash commands)

Custom: `/campaign`, `/competitor-research`, `/competitor-analysis`, `/meta-ads-analysis`,
        `/niche-research`, `/creator-research`, `/content-analysis`, `/brief`, `/client-onboard`

Pre-built (37 total from marketingskills): `/copywriting`, `/seo-audit`, `/paid-ads`,
        `/ad-creative`, `/social-content`, `/email-sequence`, `/cold-email`, `/page-cro`,
        `/analytics-tracking`, `/launch-strategy`, `/marketing-ideas`, and 26 more.

## Quality Standards

Every piece of content must:
1. Match brand voice from `clients/<brand>/brand_guidelines.md`
2. Target specific audience from `clients/<brand>/target_audience.md`
3. Differentiate from competitors (no clichés found in `competitor_intel/<brand>/`)
4. Use hooks/formats validated by `content_intel/<brand>/content_preferences.md`
5. Pass Validator agent review before delivery
