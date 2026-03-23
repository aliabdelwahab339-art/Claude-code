"""Analytics Agent — Generates analytics tracking plan and GA4 setup recommendations."""

import logging

import anthropic

from agency.config import ANTHROPIC_API_KEY, MODELS, MAX_TOKENS

logger = logging.getLogger(__name__)

ANALYTICS_SYSTEM = """You are a marketing analytics expert specializing in GA4, conversion
tracking, and marketing measurement frameworks. You build measurement systems that connect
marketing activity to business outcomes."""


async def run(brand: str, brief: str, intel: dict) -> str:
    """Generate analytics tracking plan and measurement framework."""
    personas = intel.get("personas", "")
    pain_points = intel.get("pain_points", "")

    prompt = f"""Create a complete analytics and tracking plan for brand: {brand}

## Business Brief
{brief}

## Target Personas
{personas}

---

Deliver:

# Analytics & Tracking Plan — {brand}

## 1. Key Business Metrics
[Revenue, leads, CAC, LTV, churn — define each with formula]

## 2. Marketing Funnel Metrics
[Awareness → Interest → Decision → Action — metrics at each stage]

## 3. GA4 Event Tracking Plan
| Event Name | Trigger | Parameters | Business Value |
|---|---|---|---|
[10+ events to track]

## 4. Conversion Goals
[5 primary conversion goals with values assigned]

## 5. UTM Parameter Strategy
[Naming conventions for all paid + organic campaigns]

## 6. Dashboard Setup
[Key reports to build — weekly/monthly marketing performance review]

## 7. A/B Testing Roadmap
[First 5 tests to run — hypothesis, metric, sample size]

## 8. Attribution Model
[Recommended attribution model and why, given the sales cycle]

## 9. Reporting Cadence
[Daily checks, weekly reviews, monthly analysis — what to look at when]"""

    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    message = await client.messages.create(
        model=MODELS["specialists"],
        max_tokens=MAX_TOKENS["specialists"],
        system=ANALYTICS_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    result = message.content[0].text
    logger.info("[%s] Analytics plan complete (%d chars)", brand, len(result))
    return result
