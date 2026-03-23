---
description: Analyze top performing content → content_preferences.md with links, hooks, formats
allowed-tools: Read, Write, mcp__filesystem__read_file, mcp__filesystem__write_file
---

# Content Analysis

Synthesize all creator research into a master content preferences document.
Identifies top performing content using platform-specific thresholds.

## Usage
```
/content-analysis <client_name>
```

## Platform Performance Thresholds

| Platform | "Top Performing" Criteria |
|---|---|
| **Instagram** | Views ≥ 5–10× follower count |
| **YouTube** | Views ≥ 2–3× the channel's median view count (top 20%) |
| **TikTok** | Views ≥ 10× follower count, or FYP indicator |
| **Facebook** | Engagement (reactions + comments + shares) ≥ 3–5% of page likes |
| **LinkedIn** | Engagement rate ≥ 5% (vs 2% platform average), or comments ≥ 50 |

## What This Does

1. Read all files in `content_intel/$ARGUMENTS/creators/*.md`
2. Identify top performing posts per platform using the thresholds above
3. Synthesize patterns across creators and niches
4. Save to `content_intel/$ARGUMENTS/content_preferences.md`

## Output: content_preferences.md Structure

```markdown
# Content Preferences — [brand]

## Top Performing Links by Platform

### Instagram
- [post URL or description] — [topic] — Hook: "[hook text]" — Why: [reason]
[repeat for each top post]

### YouTube
[same]

### TikTok
[same]

### Facebook
[same]

### LinkedIn
[same]

## Recurring Patterns

### Topics That Perform
- [topic] — [why it resonates]

### Hooks That Work
- "[hook formula]" — [example]

### Dominant Formats
- [format] — [why it performs in this niche]

### Posting Patterns
- [cadence/timing observations]

## Content Gaps & Opportunities
- [topic no top creator covers well]

## Recommended Content Strategy
- [actionable content recommendations based on this intelligence]
```

This document is injected into Social Media Agent and Copywriter Agent context.
