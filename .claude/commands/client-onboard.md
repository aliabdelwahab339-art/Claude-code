---
description: Interactive client onboarding — collect brief, personas, pain points, case studies
allowed-tools: Read, Write, mcp__filesystem__write_file
---

# Client Onboarding

Set up a new client in the marketing agency system. Accepts a business brief (pasted text or file path).

## Usage
```
/client-onboard
```
Then paste the brief or provide a file path when prompted.

## What This Does

1. **Accept the brief** — paste business description, product info, target market, goals
2. **Extract and structure** the following into separate files:
   - Brand name and website URL
   - Product/service description (what it does, how it works)
   - Stage of business (startup, growth, scale)
   - Revenue model and pricing approach
   - Business goals (lead gen, brand awareness, revenue, etc.)

3. **Write structured files** to `clients/<brand_name>/`:

### brief.md
Full business context from the owner/CEO perspective including:
- What the company does
- Current traction / proof points
- Why now / market timing
- Founder story / origin

### personas.md
Ideal Customer Profiles (extracted from brief or requested):
- Demographics: age, role, industry, company size
- Psychographics: values, beliefs, aspirations
- Pain profile: daily frustrations, challenges
- Buying triggers: what makes them buy
- Language: how they describe their problems

### pain_points.md
Problems the product/service solves:
- Primary pain (the one they'll pay to fix)
- Secondary pains (supporting reasons)
- Emotional pain (how it makes them feel)
- Financial pain (cost of inaction)

### case_studies.md
Success stories and proof points:
- Customer outcomes with specific numbers
- Before/after scenarios
- Testimonials or quotes

### brand_guidelines.md (inferred from brief)
- Tone of voice (inferred from how the founder writes)
- Values and principles
- What the brand is / is not
- Messaging do's and don'ts

4. **Prime `.agents/product-marketing-context.md`** with the brand context

5. **Do NOT ask for competitor URLs** — competitors will be auto-discovered in Phase 1A

## Output
```
clients/<brand_name>/
├── brief.md
├── personas.md
├── pain_points.md
├── case_studies.md
├── brand_guidelines.md
└── competitors.md  ← written by competitor_research agent during /campaign
```

Confirms: "Client '<brand_name>' onboarded. Run `/campaign <brand_name>` to start the campaign."
