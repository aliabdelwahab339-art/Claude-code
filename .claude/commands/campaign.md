---
description: Full campaign pipeline — competitor intel + content intel → parallel creative → validate → deliver
allowed-tools: Read, Write, Bash, Agent, mcp__brave-search__brave_web_search, mcp__fetch__fetch, mcp__filesystem__read_file, mcp__filesystem__write_file, mcp__slack__chat_postMessage
---

# Full Campaign Workflow

Run the complete AI marketing agency pipeline for a client.

## Usage
```
/campaign <client_name>
```

## What This Does

### PHASE 1A — Competitor Intelligence
1. Read `clients/$ARGUMENTS/brief.md`, `personas.md`, `pain_points.md`, `case_studies.md`
2. Auto-discover 3-5 direct competitors using Brave Search (based on brief + personas)
3. Save discovered competitors to `clients/$ARGUMENTS/competitors.md`
4. Spawn ONE Agent subagent per competitor (in parallel):
   - Scrape: homepage, pricing page, blog, social profiles, G2/Capterra reviews
   - Capture: headlines, value props, CTAs, pricing tiers, testimonials, ad copy
   - Save: `competitor_intel/$ARGUMENTS/raw_research/<competitor_name>.md`
5. After all research → Competitor Analysis Agent:
   - Read all raw files, synthesize → `competitor_intel/$ARGUMENTS/analysis_report.md`
   - Sections: positioning map, keyword gaps, ad patterns, content gaps, SWOT, opportunities

### PHASE 1B — Content Intelligence (runs in parallel with Phase 1A analysis)
6. Niche Research → `content_intel/$ARGUMENTS/niches.md` (main + 5 sub-niches)
7. Creator Research (parallel per sub-niche × platform):
   - Top 5 creators per niche across Instagram, YouTube, TikTok, Facebook, LinkedIn
   - `content_intel/$ARGUMENTS/creators/<sub_niche>.md`
8. Content Analysis → `content_intel/$ARGUMENTS/content_preferences.md`
   - Apply thresholds: IG: 5-10× followers | YT: 2-3× median | TikTok: 10× | FB: 3-5% | LI: 5%+
9. Meta Ads Analysis → `competitor_intel/$ARGUMENTS/meta_ads_analysis.md`
   - Ads Library scrape + breakdown: hook, persona, pain, offer, format, CTA, duration

### PHASE 2 — Creative Execution (all parallel, all receive full intel)
10. Copywriter Agent → 10 headlines, email sequences, landing page copy, taglines
11. SEO Agent → keyword strategy, meta tags, 5 blog post briefs, topic clusters
12. Social Media Agent → 30 posts (6 per platform) with hooks, captions, visual direction
13. Ad Campaign Agent → 10 Google + 10 Meta variations (uses Batches API)
14. Brand Strategy Agent → positioning statement, differentiation map, voice/tone
15. Analytics Agent → tracking plan, GA4 events, KPIs, A/B test roadmap

### VALIDATION & DELIVERY
16. Validator Agent reviews all outputs against brand guidelines + intel
17. Save all deliverables to `outputs/$ARGUMENTS/<YYYY-MM-DD-HHMMSS>/`
18. Generate `campaign_summary.md` with links to all intel + creative files
19. Post completion notice to Slack (if SLACK_BOT_TOKEN is configured)

## Output Structure
```
outputs/<client>/<run_id>/
├── campaign_summary.md
├── validation_report.md
├── intelligence/
│   ├── competitor_analysis.md
│   ├── meta_ads_analysis.md
│   └── content_preferences.md
├── copy/copy.md
├── seo/seo.md
├── social/social_media.md
├── ads/ad_campaigns.md
└── brand_strategy/brand_strategy.md
```

## Running via Python CLI
```bash
agency run --client $ARGUMENTS
```
