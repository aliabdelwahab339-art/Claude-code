---
description: Find top 5 creators per sub-niche across all 5 platforms
allowed-tools: Read, Write, Agent, mcp__brave-search__brave_web_search, mcp__fetch__fetch, mcp__filesystem__write_file
---

# Creator Research

Research top creators for each sub-niche across Instagram, YouTube, TikTok, Facebook, LinkedIn.
Requires `/niche-research` to have been run first.

## Usage
```
/creator-research <client_name>
```

## What This Does

1. Read `content_intel/$ARGUMENTS/niches.md` — extract the 5 sub-niches
2. For each sub-niche × platform (25 combinations total), search:
   - "top [sub-niche] creators on [platform] 2026"
   - "best [sub-niche] [platform] accounts to follow"
3. For each creator found, research:
   - Handle/URL
   - Estimated followers
   - Content focus and posting style
   - Why they're top in this niche
   - Recurring content themes

All 25 combinations research in **parallel** (one Agent subagent per sub-niche).

## Output per Sub-niche: creators/<sub_niche>.md
```markdown
# Top Creators — [sub-niche]

## Instagram
### [Creator Name / @handle]
- Handle: @handle
- Followers: [number]
- Content focus: [what they create]
- Posting style: [Reels / Carousels / Static]
- Why they're top: [what makes them stand out]
- Top themes: [list]

[repeat for top 5 creators]

## YouTube
[same format]

## TikTok
[same format]

## Facebook
[same format]

## LinkedIn
[same format]
```

## Next Steps
After running this, use `/content-analysis $ARGUMENTS` to identify top performing content patterns.
