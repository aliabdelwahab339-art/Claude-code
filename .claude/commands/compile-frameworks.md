---
description: Compile all personal frameworks into the master .agents/my-frameworks.md skill file
allowed-tools: Read, Write, mcp__filesystem__read_file, mcp__filesystem__write_file
---

# Compile Frameworks

Read all files in `frameworks/books/` and `frameworks/mental_models/` and compile them
into the master skill file `.agents/my-frameworks.md`. This file is injected into all agents.

## Usage
```
/compile-frameworks
```

## What This Does

1. Read every file in:
   - `frameworks/books/*.md` — book summaries and takeaways
   - `frameworks/mental_models/*.md` — personal frameworks
2. Synthesize into `.agents/my-frameworks.md` with this structure:

```markdown
# Owner's Personal Frameworks & Mental Models
Last compiled: [date]

## Overview
[Summary of total books + frameworks loaded]

## Core Mental Models

### [Framework 1 Name]
[Description + how to apply in marketing]

### [Framework 2 Name]
[Description + how to apply]

## Book-Derived Principles

### [Book 1 Title]
**Core idea**: [one sentence]
**How this shapes our marketing**:
- [Principle 1 → application]
- [Principle 2 → application]

### [Book 2 Title]
...

## Copy Principles (derived from all frameworks)
- [Principle that applies to copywriting]
- [Another principle]

## Strategy Principles
- [Principle that applies to positioning/strategy]

## Campaign Principles
- [Principle that applies to ads/campaigns]

## Things We Never Do
- [Anti-patterns from frameworks]
```

3. Report: "Compiled [N] books + [M] mental models into `.agents/my-frameworks.md`"

## Effect
Once compiled, every agent run will load this file and apply your frameworks to:
- Copy tone and angle
- Brand positioning
- Ad hook selection
- Content angles
- Strategic recommendations

Run this every time you add new books or frameworks with `/add-framework`.
