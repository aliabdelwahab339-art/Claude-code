---
description: Parse a client brief and route to the right agents
allowed-tools: Read, Write, mcp__filesystem__write_file
---

# Brief Parser

Accept a pasted client brief or file path, extract structured data, and route to agents.

## Usage
```
/brief
```
Then paste the brief text, or provide a file path.

Alternatively:
```
/brief clients/my_brand/brief.md
```

## What This Does

1. **Accept input** — pasted text or file path
2. **Extract structured data**:
   - Business overview (what the company does)
   - Product/service details
   - Stage of business
   - Target audience (personas)
   - Core pain points solved
   - Key differentiators
   - Business goals for this campaign
   - Budget/timeline constraints
   - Deliverables requested
   - Any competitor context provided

3. **Determine routing**:
   - Full campaign → suggest `/campaign <brand>`
   - Just competitor intel → suggest `/competitor-research <brand>`
   - Just content strategy → suggest `/niche-research <brand>`
   - Just ads → suggest `/meta-ads-analysis <brand>`
   - Specific deliverable → suggest relevant skill

4. **Write structured brief** to `clients/<brand_name>/brief.md` if not already there

5. **Show summary** of what was extracted + which agents will be invoked

## Quick Start Example

Paste a brief like:
> "We built a project management tool for remote teams. Our target is engineering managers at Series A-C startups, 20-200 employees. The main pain is that existing tools like Jira are too complex and Trello too simple. We have 3 case studies showing 40% faster sprint cycles. Goals: generate 500 leads in Q2."

The skill will:
- Extract brand name, product, personas, pain, proof, goals
- Recommend: `/campaign <brand>` for the full pipeline
- Ask: "Should I start the full campaign now?"
