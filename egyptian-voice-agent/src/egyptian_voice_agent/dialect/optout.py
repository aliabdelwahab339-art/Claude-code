"""Opt-out phrase detection — short-circuits the LLM on clear rejections.

Matches on the normalized Arabic transcript before the LLM runs. When a
match is found we:
  1. Speak a brief Egyptian farewell ("حاضر، يوم سعيد").
  2. Emit an `end_call` tool call with outcome="not_qualified".
  3. Hang up the Twilio leg.

This is both an economics lever (skips a Claude round-trip + cuts ~15s off
every opt-out call — ~$0.10/call saved on Twilio) AND a PDPL requirement:
the law requires honoring opt-out immediately and not pitching further.

The list is conservative on purpose — only high-confidence phrases. We'd
rather send an ambiguous case to the LLM than hang up on a lead who just
said "مش دلوقتي" (not right now — which ISN'T opt-out).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from egyptian_voice_agent.dialect.fallbacks import normalize_egyptian


# Arabic opt-out / Do-Not-Call phrases, regex-anchored on word boundaries.
# Keep this list minimal and high-precision; add conservatively.
_OPT_OUT_PATTERNS: list[re.Pattern[str]] = [
    # "don't call me (again)"
    re.compile(r"ما\s*تكلم(?:ني|وني)ش(\s*تاني)?"),
    re.compile(r"ما\s*تتصل(?:ش|وش)(\s*بي(?:ا|ه))?(\s*تاني)?"),
    re.compile(r"لا\s*تتصل(?:وا)?\s*ب(?:ي(?:ا|ه)|ي)"),
    # "remove my number" / "delete my number"
    re.compile(r"شيل\s*رقم(?:ي|ى)"),
    re.compile(r"امسح\s*رقم(?:ي|ى)"),
    re.compile(r"احذف\s*رقم(?:ي|ى)"),
    # "unsubscribe / cancel"
    re.compile(r"إلغاء\s*الاشتراك"),
    re.compile(r"(?:ألغي|الغي)\s*الاشتراك"),
    # Hard "not interested" — only the unambiguous forms.
    re.compile(r"مش\s*مهتم(?:ة)?\s*(?:خالص|أبد(?:اً|ا)?)"),
    re.compile(r"(?:انا\s*)?مش\s*عايز(?:\s*حاجة)?\s*(?:خالص|أبد(?:اً|ا)?)"),
    # English opt-outs (lead code-switches)
    re.compile(r"\b(?:stop|unsubscribe|remove\s+me|do\s+not\s+call)\b", re.IGNORECASE),
]


@dataclass(frozen=True)
class OptOutMatch:
    matched_phrase: str
    rule_index: int


def detect_opt_out(text: str) -> OptOutMatch | None:
    """Return the first opt-out match in the utterance, or None."""
    normalized = normalize_egyptian(text)
    for i, pattern in enumerate(_OPT_OUT_PATTERNS):
        m = pattern.search(normalized)
        if m:
            return OptOutMatch(matched_phrase=m.group(0), rule_index=i)
    return None


# The Egyptian farewell read back before we hang up. Short on purpose —
# PDPL Article 12 prohibits pitching after opt-out.
FAREWELL_AR_EG = "حاضر، يوم سعيد."
