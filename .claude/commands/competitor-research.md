---
description: Auto-discover and deeply research competitors from the client brief
allowed-tools: Read, Write, Agent, mcp__brave-search__brave_web_search, mcp__fetch__fetch, mcp__filesystem__write_file
---

# Competitor Research

Auto-discover and research 3-5 direct competitors for a client. Runs as a standalone skill.

## Usage
```
/competitor-research <client_name>
```

## What This Does

### Step 0 — Competitor Discovery
1. Read `clients/$ARGUMENTS/brief.md` and `clients/$ARGUMENTS/personas.md`
2. Use Brave Search to find direct competitors:
   - Query: "[product category] alternatives [year]"
   - Query: "[pain point] solution tool software"
   - Query: "best [category] for [persona type]"
3. Use Claude to select the 3-5 most direct competitors from results
4. Save to `clients/$ARGUMENTS/competitors.md`

### Step 1 — Deep Scrape (one Agent per competitor, in parallel)
For each competitor:
- **Homepage**: headline, subheadline, value prop, main CTA, feature claims
- **Pricing page**: tiers, prices, trial terms, freemium model
- **Blog/Content**: topics covered, SEO keywords visible, content style
- **Social profiles**: found via search — follower counts, posting frequency
- **Reviews**: G2, Capterra, Trustpilot — common praise and complaints
- **Ad copy**: any ads visible in search results or ad libraries

Save each to: `competitor_intel/$ARGUMENTS/raw_research/<competitor_name>.md`

### Output Format per Competitor
```markdown
# Competitor: [Name]
URL: [url]

## Positioning
- Headline: [exact text]
- Subheadline: [exact text]
- Value prop: [summary]
- Key claims: [list]

## Pricing
- Tiers: [list with prices]
- Free trial: [yes/no + terms]
- Freemium: [yes/no + limits]

## Content/SEO
- Topics they cover: [list]
- Keywords visible: [list]
- Publishing frequency: [estimate]

## Social Proof
- G2 rating + review themes
- Testimonials on homepage

## Ad Intelligence
- Any ad copy found
- Offers used in ads

## Weaknesses Observed
- [gaps in their messaging/offering]
```
