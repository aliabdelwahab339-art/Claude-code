"""CMO Orchestrator — 3-phase campaign execution: Intel → Content Intel → Creative."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

import anthropic

from agency.config import ANTHROPIC_API_KEY, MODELS, MAX_TOKENS
from agency.tools.file_tools import (
    read_all_client_files,
    read_intel_file,
    write_output,
    write_campaign_summary,
    ensure_output_dirs,
    read_frameworks,
)
from agency.validator import validate_all_outputs, summarize_validation

logger = logging.getLogger(__name__)

CMO_SYSTEM = """You are the CMO (Chief Marketing Officer) of an AI-native marketing agency.

Your role:
- Receive client briefs and orchestrate the full campaign workflow
- Phase 1A: Competitor intelligence (research + analysis)
- Phase 1B: Content intelligence (niche mapping + creator research + content preferences)
- Phase 2: Parallel creative execution (copy, SEO, social, ads, brand strategy)
- Assemble all deliverables into a coherent campaign package

You delegate all execution to specialist agents. Your job is strategy, quality, and assembly."""


async def run_campaign(brief: dict, client_name: str) -> dict:
    """Full campaign pipeline: Intel → Creative → Validate → Deliver."""
    run_id = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    logger.info("Starting campaign for '%s' (run_id: %s)", client_name, run_id)

    # Load client files
    client_files = read_all_client_files(client_name)
    brand_guidelines = client_files.get("brand_guidelines.md", "")
    personas = client_files.get("personas.md", "")
    pain_points = client_files.get("pain_points.md", "")
    case_studies = client_files.get("case_studies.md", "")
    brief_text = client_files.get("brief.md", brief.get("brief", ""))

    brief_summary = f"""Client: {client_name}
Brief: {brief_text[:500]}
Personas: {personas[:300]}
Pain Points: {pain_points[:300]}"""

    # Create output directories
    ensure_output_dirs(client_name, run_id)

    # ── PHASE 1A: COMPETITOR INTELLIGENCE ────────────────────────────────────
    logger.info("[%s] Phase 1A: Competitor Intelligence", client_name)
    from agency.agents.competitor_research import run as competitor_research_run
    from agency.agents.competitor_analysis import run as competitor_analysis_run

    await competitor_research_run(client_name, brief_text, personas)
    competitor_intel = await competitor_analysis_run(client_name)

    # Save competitor intel to output
    if competitor_intel:
        write_output(client_name, "intelligence", "competitor_analysis.md", competitor_intel, run_id)

    # ── PHASE 1B: CONTENT INTELLIGENCE (parallel with analysis) ──────────────
    logger.info("[%s] Phase 1B: Content Intelligence", client_name)
    from agency.agents.niche_research import run as niche_research_run
    from agency.agents.creator_research import run as creator_research_run
    from agency.agents.content_analysis import run as content_analysis_run
    from agency.agents.meta_ads_analysis import run as meta_ads_run

    # Niche mapping first (sequential — creator research depends on it)
    await niche_research_run(client_name, brief_text, personas)

    # Creator research + meta ads in parallel
    await asyncio.gather(
        creator_research_run(client_name),
        meta_ads_run(client_name, brief_text),
        return_exceptions=True,
    )

    # Content analysis synthesizes creator research (sequential)
    content_preferences = await content_analysis_run(client_name)
    meta_ads_intel = read_intel_file("competitor", client_name, "meta_ads_analysis.md")

    if content_preferences:
        write_output(client_name, "intelligence", "content_preferences.md", content_preferences, run_id)
    if meta_ads_intel:
        write_output(client_name, "intelligence", "meta_ads_analysis.md", meta_ads_intel, run_id)

    # ── PHASE 2: CREATIVE EXECUTION (all parallel) ────────────────────────────
    logger.info("[%s] Phase 2: Creative Execution (parallel)", client_name)
    from agency.agents.copywriter import run as copywriter_run
    from agency.agents.seo import run as seo_run
    from agency.agents.social_media import run as social_media_run
    from agency.agents.ad_campaigns import run as ad_campaigns_run
    from agency.agents.brand_strategy import run as brand_strategy_run

    intel_context = {
        "competitor_intel": competitor_intel,
        "content_preferences": content_preferences,
        "meta_ads_intel": meta_ads_intel,
        "brand_guidelines": brand_guidelines,
        "personas": personas,
        "pain_points": pain_points,
        "case_studies": case_studies,
        "frameworks": read_frameworks(),
    }

    creative_results = await asyncio.gather(
        copywriter_run(client_name, brief_text, intel_context),
        seo_run(client_name, brief_text, intel_context),
        social_media_run(client_name, brief_text, intel_context),
        ad_campaigns_run(client_name, brief_text, intel_context),
        brand_strategy_run(client_name, brief_text, intel_context),
        return_exceptions=True,
    )

    outputs = {}
    output_names = ["copy", "seo", "social_media", "ad_campaigns", "brand_strategy"]
    for name, result in zip(output_names, creative_results):
        if isinstance(result, Exception):
            logger.error("[%s] %s failed: %s", client_name, name, result)
            outputs[name] = ""
        else:
            outputs[name] = result or ""
            if result:
                subdir_map = {
                    "copy": "copy",
                    "seo": "seo",
                    "social_media": "social",
                    "ad_campaigns": "ads",
                    "brand_strategy": "brand_strategy",
                }
                write_output(client_name, subdir_map[name], f"{name}.md", result, run_id)

    # ── VALIDATION ────────────────────────────────────────────────────────────
    logger.info("[%s] Validating outputs", client_name)
    validated = await validate_all_outputs(
        outputs, client_name, brand_guidelines, competitor_intel, brief_summary
    )
    validation_summary = summarize_validation(validated)
    write_output(client_name, "", "validation_report.md", validation_summary, run_id)

    # ── CAMPAIGN SUMMARY ──────────────────────────────────────────────────────
    deliverables = {
        name: f"{subdir_map.get(name, name)}/{name}.md"
        for name, result in zip(output_names, creative_results)
        if not isinstance(result, Exception) and result
    }
    output_dir = str(Path("outputs") / client_name / run_id)
    write_campaign_summary(
        client_name,
        run_id,
        {
            "intelligence": {
                "Competitor Analysis": "intelligence/competitor_analysis.md",
                "Content Preferences": "intelligence/content_preferences.md",
                "Meta Ads Analysis": "intelligence/meta_ads_analysis.md",
            },
            "deliverables": deliverables,
        },
    )

    logger.info("[%s] Campaign complete → %s", client_name, output_dir)
    return {"output_dir": output_dir, "run_id": run_id, "validated": validated}
