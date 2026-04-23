"""Opt-out phrase detection — no false positives on near-miss phrases."""

from __future__ import annotations

import pytest

from egyptian_voice_agent.dialect.optout import detect_opt_out


@pytest.mark.parametrize(
    "utterance",
    [
        "ما تكلمنيش تاني",
        "ماتكلمنيش تاني",
        "ما تتصلش بيا تاني",
        "لا تتصلوا بيا",
        "شيل رقمي",
        "امسح رقمي من عندك",
        "احذف رقمي",
        "إلغاء الاشتراك",
        "ألغي الاشتراك",
        "انا مش مهتم خالص",
        "مش عايز حاجة أبدا",
        "STOP",
        "please remove me from the list",
        "do not call me again",
        "unsubscribe please",
    ],
)
def test_detects_opt_out(utterance: str) -> None:
    match = detect_opt_out(utterance)
    assert match is not None, f"should detect opt-out: {utterance!r}"


@pytest.mark.parametrize(
    "utterance",
    [
        # Soft deferral — NOT opt-out. Lead is busy, not refusing.
        "مش دلوقتي",
        "مش فاضي دلوقتي",
        "ممكن تكلمني بعدين؟",
        "كلمني بكرة",
        # Inquiry, not rejection.
        "مش فاهم، ممكن توضحي؟",
        "مش سامع كويس",
        # "not interested" without the hard qualifier — ambiguous, send to LLM.
        "مش مهتم",
        "انا مش عايز",
        # Generic negation, not opt-out.
        "لأ",
        "لأه",
        # English near-miss.
        "I'm busy",
        "not now",
    ],
)
def test_does_not_false_fire(utterance: str) -> None:
    assert detect_opt_out(utterance) is None, (
        f"should NOT trigger opt-out: {utterance!r}"
    )


def test_match_reports_rule_index() -> None:
    match = detect_opt_out("شيل رقمي")
    assert match is not None
    assert match.rule_index >= 0
    assert "رقم" in match.matched_phrase
