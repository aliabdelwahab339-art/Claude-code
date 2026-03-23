---
description: Scrape Meta Ads Library for each competitor — hook, persona, pain, offer, format, CTA breakdown
allowed-tools: Read, Write, mcp__brave-search__brave_web_search, mcp__fetch__fetch, mcp__filesystem__write_file
---

# Meta Ads Analysis

Scrape and analyze Facebook/Meta ads for all discovered competitors.
Produces a structured breakdown of every ad found.

## Usage
```
/meta-ads-analysis <client_name>
```

## What This Does

1. Read `clients/$ARGUMENTS/competitors.md` for the competitor list
2. For each competitor, search:
   - Meta Ads Library: `https://facebook.com/ads/library/?q=<competitor>`
   - Brave Search: "[competitor] facebook ads 2026"
   - Brave Search: "[competitor] meta ads examples hooks"
3. Extract and categorize every ad found
4. Synthesize into `competitor_intel/$ARGUMENTS/meta_ads_analysis.md`

## Ad Breakdown Fields

For every ad found:

| Field | What to Capture |
|---|---|
| **Hook** | First line of copy or first frame description |
| **Persona** | Who this targets — job title, life stage, pain profile |
| **Pain Point** | Specific problem the ad leads with |
| **Offer** | Free trial / demo / discount / lead magnet / webinar |
| **Format** | Image / Single Video / Carousel / Story / UGC-style / Testimonial |
| **CTA** | Button text + destination (pricing page, free trial, etc.) |
| **Social Proof** | Reviews, numbers, logos, case study mentions |
| **Running Duration** | How long the ad has been active (older = likely winning) |
| **Messaging Angle** | Pain / Gain / Fear / Aspiration / Social Proof |

## Output: meta_ads_analysis.md Structure

```markdown
# Meta Ads Intelligence — [brand]

## Competitor Ad Breakdowns

### [Competitor 1]
- Total active ads found: N
#### Ad 1: [brief description]
| Hook | [text] |
| Persona | [who] |
| Pain Point | [problem] |
| Offer | [what] |
| Format | [type] |
| CTA | [button → destination] |
| Social Proof | [evidence used] |
| Running Duration | [time] |
| Angle | [pain/gain/fear/etc.] |

[repeat per ad]

### [Competitor 2]
[same format]

## Winning Ad Patterns
- Hook formulas used most: [list]
- Most common offer type: [list]
- Dominant formats: [list]
- CTA patterns: [list]

## Competitor Weaknesses in Ads
- [gaps to exploit]

## Opportunities for [brand]
- Untested hook angles: [list]
- Offers competitors aren't making: [list]
- Formats no one uses well: [list]
- Audiences being ignored: [list]
```

This report is injected into the Ad Campaign Agent context.
