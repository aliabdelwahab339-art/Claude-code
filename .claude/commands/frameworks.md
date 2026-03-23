---
description: List all active personal frameworks and which agents use them
allowed-tools: Read, mcp__filesystem__read_file
---

# Frameworks

List all personal frameworks and books currently loaded in the system.

## Usage
```
/frameworks
```

## What This Does

1. Scan `frameworks/books/*.md` — list all books
2. Scan `frameworks/mental_models/*.md` — list all mental models
3. Check `.agents/my-frameworks.md` — confirm it's compiled and up to date
4. Report which agents use the frameworks

## Output Format

```
📚 Active Frameworks — AI Marketing Agency

Books Loaded (N):
  ✅ [Book Title] by [Author]
  ✅ [Book Title] by [Author]
  ...

Mental Models Loaded (N):
  ✅ [Framework Name]
  ✅ [Framework Name]
  ...

Compiled Skill: .agents/my-frameworks.md
Last compiled: [date] ← or "⚠️ NOT COMPILED — run /compile-frameworks"

Agents Using These Frameworks:
  • CMO / Orchestrator   — campaign strategy shaped by your frameworks
  • Copywriter           — copy written through your mental models
  • Brand Strategy       — positioning uses your frameworks as foundation
  • Ad Campaigns         — ad angles derived from your principles
  • Social Media         — content angles filtered through your worldview

To add a new book or framework: /add-framework
To rebuild after adding: /compile-frameworks
```

## Quick Add Reminder
If frameworks haven't been compiled after adding new ones:
> ⚠️ New frameworks found that aren't compiled yet. Run `/compile-frameworks` to activate them.
