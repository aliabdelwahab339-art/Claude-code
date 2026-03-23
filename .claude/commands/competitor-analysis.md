---
description: Synthesize raw competitor research into strategic SWOT + keyword/content gap report
allowed-tools: Read, Write, mcp__filesystem__read_file, mcp__filesystem__write_file
---

# Competitor Analysis

Synthesize all raw competitor research into a strategic intelligence report.
Run this after `/competitor-research` completes.

## Usage
```
/competitor-analysis <client_name>
```

## What This Does

1. Read all files in `competitor_intel/$ARGUMENTS/raw_research/*.md`
2. Synthesize into `competitor_intel/$ARGUMENTS/analysis_report.md`

## Output: analysis_report.md Structure

### Positioning Map
Where each competitor sits across key axes:
- Premium vs. budget
- Enterprise vs. SMB
- Simple vs. full-featured
- Established vs. challenger
- Product-led vs. sales-led

### Messaging Patterns
- Common claims all competitors make (avoid these — they're table stakes)
- Overused words and phrases to avoid
- Differentiation angles that are open and unowned

### Keyword Gaps
Terms competitors rank for that represent SEO opportunities:
| Keyword | Competitor that ranks | Volume (est.) | Your opportunity |

### Ad Creative Patterns
- Most common headline formulas
- CTA button text patterns
- Offer types used (free trial, demo, discount)
- Emotional angles (pain/gain/fear/aspiration)

### Content Gaps
- Topics competitors publish about
- Topics NO competitor covers well (your content opportunity)

### Pricing Intelligence
- Pricing tier structures
- Anchoring strategies used
- Freemium/trial approaches

### SWOT vs. Each Competitor
For each competitor: your Strengths, Weaknesses, Opportunities, Threats

### Strategic Recommendations
Top 5 actionable opportunities derived from the intelligence
