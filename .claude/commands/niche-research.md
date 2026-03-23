---
description: Map the main niche + 5 sub-niches from brand context
allowed-tools: Read, Write, mcp__brave-search__brave_web_search, mcp__filesystem__write_file
---

# Niche Research

Map the content niche landscape for a brand — identifies the main niche and 5 sub-niches
where the target audience lives online.

## Usage
```
/niche-research <client_name>
```

## What This Does

1. Read `clients/$ARGUMENTS/brief.md` and `clients/$ARGUMENTS/personas.md`
2. Use Brave Search for market context queries:
   - "[product category] content creators community"
   - "[persona type] follows online [year]"
3. Use Claude to identify:
   - **1 main niche** — the primary content category (e.g., "B2B SaaS Productivity")
   - **5 sub-niches** — specific audiences within the main niche
4. Save to `content_intel/$ARGUMENTS/niches.md`

## Sub-niche Selection Criteria
Each sub-niche should be:
- Specific enough to have dedicated creators and communities
- Broad enough to have an active content ecosystem
- Directly relevant to the brand's target personas
- Different from each other (no overlap)

## Output: niches.md Structure
```markdown
# Niche Map — [brand]

## Main Niche
[One clear label — e.g. "B2B SaaS Productivity Tools"]

## 5 Sub-Niches
1. **[Sub-niche name]** — [why this audience cares about this brand]
2. **[Sub-niche name]** — [explanation]
3. **[Sub-niche name]** — [explanation]
4. **[Sub-niche name]** — [explanation]
5. **[Sub-niche name]** — [explanation]

## Content Opportunity Summary
[2-3 sentences on biggest opportunities in this niche landscape]
```

## Next Steps
After running this, use `/creator-research $ARGUMENTS` to find top creators per sub-niche.
