---
description: Add a book summary or personal mental model to your frameworks library
allowed-tools: Read, Write, mcp__filesystem__write_file
---

# Add Framework

Add a book you've read or a mental model you use to your personal frameworks library.
All frameworks are automatically injected into every agent at campaign time.

## Usage
```
/add-framework
```
Then paste your book summary, key takeaways, or mental model description.

## What This Does

1. **Accept input** — paste a book summary, mental model description, or principles list
2. **Identify type**:
   - Book → saves to `frameworks/books/<book_title_by_author>.md`
   - Mental model / framework → saves to `frameworks/mental_models/<framework_name>.md`
3. **Structure it** using the standard format below
4. **Confirm** what was saved and remind to run `/compile-frameworks`

## Book Format
```markdown
# [Book Title] by [Author]

## Core Idea
[One sentence]

## Mental Models from This Book
### [Model Name]
**What it is**: [explanation]
**How to apply in marketing**: [specific application]

### [Model Name]
...

## Key Principles
- [Principle 1]
- [Principle 2]

## Quotes to Use
- "[Quote]"

## How This Shapes Our Marketing
[2-3 sentences on how this book changes how we write copy, position brands, run ads, etc.]
```

## Mental Model Format
```markdown
# [Framework / Mental Model Name]

## What It Is
[2-3 sentence explanation]

## The Core Principle
[One sentence — the essential insight]

## How We Apply It in Marketing
### In Copywriting
[Specific application]
### In Strategy
[Specific application]
### In Ad Campaigns
[Specific application]

## Examples
- [Concrete example 1]
- [Concrete example 2]

## Questions This Framework Answers
- [Strategic question this helps answer]
```

## After Adding
Run `/compile-frameworks` to rebuild the master skill file and activate your new framework
across all agents.
