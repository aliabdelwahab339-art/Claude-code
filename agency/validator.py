"""Builder-Validator quality checker — reviews all creative outputs before delivery."""

import logging
from pathlib import Path

import anthropic

from agency.config import ANTHROPIC_API_KEY, MODELS, MAX_TOKENS
from agency.tools.file_tools import read_frameworks

logger = logging.getLogger(__name__)

VALIDATOR_SYSTEM = """You are a senior marketing quality reviewer (validator).

Your job is to review creative marketing outputs and check them against:
1. Brand guidelines — does the copy match the brand voice and tone?
2. Competitive differentiation — does it avoid clichés used by competitors?
3. Strategic alignment — does it address the core pain points and personas?
4. Personal frameworks — does it reflect the owner's mental models and principles?
5. Quality bar — is it compelling, specific, and action-oriented?

For each piece of content, output:
## Quality Review

### Pass/Fail: [PASS or FAIL]

### Score: [1-10]

### Strengths
- [What works well]

### Issues Found
- [Any problems]

### Suggested Improvements
- [Specific, actionable fixes]

Be direct. Only PASS work that is genuinely ready to deliver to a client."""


async def validate_output(
    content: str,
    content_type: str,
    brand: str,
    brand_guidelines: str,
    competitor_intel: str,
    brief_summary: str,
) -> dict:
    """Validate a single creative output. Returns {passed, score, feedback, revised_content}."""
    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    frameworks = read_frameworks()

    user_prompt = f"""Review this {content_type} for brand '{brand}':

## Content to Review
{content}

## Brand Guidelines
{brand_guidelines}

## Brief Summary
{brief_summary}

## Competitor Intelligence (avoid these patterns)
{competitor_intel[:2000] if competitor_intel else 'Not available'}

## Personal Frameworks (outputs should reflect these)
{frameworks[:1500] if frameworks else 'Not loaded'}

Please review and score this content."""

    message = await client.messages.create(
        model=MODELS["validator"],
        max_tokens=MAX_TOKENS["validator"],
        system=VALIDATOR_SYSTEM,
        messages=[{"role": "user", "content": user_prompt}],
    )

    review = message.content[0].text
    passed = "PASS" in review.upper() and "FAIL" not in review.upper()

    score = 0
    for line in review.split("\n"):
        if "Score:" in line:
            try:
                score = int(line.split(":")[1].strip().split("/")[0])
            except (ValueError, IndexError):
                pass

    return {
        "passed": passed,
        "score": score,
        "review": review,
        "content": content,
        "content_type": content_type,
    }


async def validate_all_outputs(
    outputs: dict[str, str],
    brand: str,
    brand_guidelines: str,
    competitor_intel: str,
    brief_summary: str,
) -> dict[str, dict]:
    """Validate all campaign outputs in parallel. Returns {output_key: validation_result}."""
    import asyncio
    tasks = {
        key: validate_output(
            content, key, brand, brand_guidelines, competitor_intel, brief_summary
        )
        for key, content in outputs.items()
        if content
    }
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    validated = {}
    for key, result in zip(tasks.keys(), results):
        if isinstance(result, Exception):
            logger.error("Validation failed for %s: %s", key, result)
            validated[key] = {
                "passed": False,
                "score": 0,
                "review": f"Validation error: {result}",
                "content": outputs[key],
                "content_type": key,
            }
        else:
            validated[key] = result
    return validated


def summarize_validation(validated: dict[str, dict]) -> str:
    """Generate a validation summary report."""
    total = len(validated)
    passed = sum(1 for v in validated.values() if v.get("passed"))
    avg_score = sum(v.get("score", 0) for v in validated.values()) / max(total, 1)

    lines = [
        "# Validation Summary",
        "",
        f"**Total outputs reviewed:** {total}",
        f"**Passed:** {passed}/{total}",
        f"**Average score:** {avg_score:.1f}/10",
        "",
        "## Results by Output",
        "",
    ]
    for key, v in validated.items():
        status = "✅ PASS" if v.get("passed") else "❌ FAIL"
        lines.append(f"### {key} — {status} (Score: {v.get('score', 0)}/10)")
        if not v.get("passed") and "Issues Found" in v.get("review", ""):
            lines.append(v["review"])
        lines.append("")
    return "\n".join(lines)
