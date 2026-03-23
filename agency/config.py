"""Model routing, token limits, and tool assignments per agent."""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Model Routing ─────────────────────────────────────────────────────────────
MODELS = {
    "orchestrator": "claude-opus-4-6",   # CMO — planning, delegation, assembly
    "specialists": "claude-sonnet-4-6",  # All specialist agents — fast execution
    "validator": "claude-sonnet-4-6",    # Quality review pass
    "research": "claude-sonnet-4-6",     # Competitor + content research
    "analysis": "claude-sonnet-4-6",     # Synthesis agents
}

# ── Thinking Configuration ────────────────────────────────────────────────────
THINKING = {
    "orchestrator": {"type": "adaptive"},
    "specialists": {"type": "adaptive"},
    "validator": {"type": "disabled"},
    "research": {"type": "disabled"},
}

# ── Token Limits ──────────────────────────────────────────────────────────────
MAX_TOKENS = {
    "orchestrator": 16000,
    "specialists": 8000,
    "validator": 4000,
    "research": 8000,
    "analysis": 8000,
}

# ── Tools per Agent ───────────────────────────────────────────────────────────
TOOLS_BY_AGENT = {
    "orchestrator": ["filesystem", "fetch", "brave_search"],
    "competitor_research": ["brave_search", "fetch", "filesystem"],
    "competitor_analysis": ["filesystem"],
    "niche_research": ["brave_search", "filesystem"],
    "creator_research": ["brave_search", "fetch", "filesystem"],
    "content_analysis": ["filesystem"],
    "meta_ads_analysis": ["brave_search", "fetch", "filesystem"],
    "copywriter": ["filesystem", "fetch"],
    "seo": ["brave_search", "fetch", "filesystem"],
    "social_media": ["brave_search", "filesystem", "fetch"],
    "ad_campaigns": ["brave_search", "filesystem"],
    "analytics": ["filesystem"],
    "brand_strategy": ["brave_search", "fetch", "filesystem"],
    "validator": ["filesystem"],
}

# ── Scalability Configuration ─────────────────────────────────────────────────
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "20"))
MAX_CONCURRENT_API_CALLS = int(os.getenv("MAX_CONCURRENT_API_CALLS", "50"))
MAX_CONCURRENT_PER_CLIENT = int(os.getenv("MAX_CONCURRENT_PER_CLIENT", "10"))

# ── Cache TTL ─────────────────────────────────────────────────────────────────
COMPETITOR_CACHE_TTL_DAYS = int(os.getenv("COMPETITOR_CACHE_TTL_DAYS", "7"))
CONTENT_CACHE_TTL_DAYS = int(os.getenv("CONTENT_CACHE_TTL_DAYS", "30"))

# ── Output Configuration ──────────────────────────────────────────────────────
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "outputs")

# ── Anthropic API Key ─────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ── Retry Configuration ───────────────────────────────────────────────────────
RETRY_MAX_ATTEMPTS = 5
RETRY_MIN_WAIT = 1   # seconds
RETRY_MAX_WAIT = 60  # seconds

# ── Competitor Discovery ──────────────────────────────────────────────────────
MAX_COMPETITORS = 5
MIN_COMPETITORS = 3

# ── Content Intelligence ──────────────────────────────────────────────────────
MAX_SUB_NICHES = 5
MAX_CREATORS_PER_NICHE = 5
PLATFORMS = ["instagram", "youtube", "tiktok", "facebook", "linkedin"]

# Platform performance thresholds
PLATFORM_THRESHOLDS = {
    "instagram": {"metric": "views_to_followers_ratio", "min": 5.0, "max": 10.0},
    "youtube": {"metric": "views_to_channel_median_ratio", "min": 2.0, "max": 3.0},
    "tiktok": {"metric": "views_to_followers_ratio", "min": 10.0},
    "facebook": {"metric": "engagement_to_page_likes_pct", "min": 3.0, "max": 5.0},
    "linkedin": {"metric": "engagement_rate_pct", "min": 5.0, "comments_min": 50},
}
