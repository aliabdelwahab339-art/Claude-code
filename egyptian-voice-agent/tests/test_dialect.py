"""Unit tests for dialect post-processing + SSML building."""

from __future__ import annotations

from egyptian_voice_agent.dialect.fallbacks import normalize_egyptian
from egyptian_voice_agent.dialect.ssml import build as build_ssml


def test_normalize_fixes_common_misrecognitions() -> None:
    assert normalize_egyptian("انا ماش عايز") == "انا مش عايز"
    assert normalize_egyptian("دلوقت عايز") == "دلوقتي عايز"
    assert normalize_egyptian("ازايك يا باشا") == "إزيك يا باشا"
    assert normalize_egyptian("امتي الميعاد") == "إمتى الميعاد"
    assert normalize_egyptian("انا عاوز استفسر") == "انا عايز استفسر"


def test_normalize_strips_msa_fillers() -> None:
    assert "لقد" not in normalize_egyptian("لقد اتصلت امبارح")


def test_ssml_wraps_voice_and_prosody() -> None:
    doc = build_ssml("أهلاً، عايز إيه؟", voice="ar-EG-SalmaNeural")
    assert '<voice name="ar-EG-SalmaNeural">' in doc
    assert "<prosody" in doc
    assert 'xml:lang="ar-EG"' in doc


def test_ssml_applies_ipa_for_dilwaqti() -> None:
    doc = build_ssml("دلوقتي هكلمك", voice="ar-EG-SalmaNeural")
    assert '<phoneme alphabet="ipa"' in doc


def test_ssml_inserts_break_after_question_mark() -> None:
    doc = build_ssml("إزيك النهارده؟", voice="ar-EG-SalmaNeural")
    assert '<break time="250ms"/>' in doc
