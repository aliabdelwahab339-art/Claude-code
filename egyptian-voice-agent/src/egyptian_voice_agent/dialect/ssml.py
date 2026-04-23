"""Azure SSML builder tuned for Egyptian-Arabic neural voices.

Azure respects IPA overrides on Arabic; we use those for stubborn Cairo-dialect
words the default voice mangles. Prosody is nudged slightly faster and higher
energy — the default cadence sounds flat on conversational turns.
"""

from __future__ import annotations

from xml.sax.saxutils import escape

from egyptian_voice_agent.config import settings

# IPA overrides for common Cairo-dialect pronunciations.
# Azure's ar-EG voices are pretty good but these specific words render weakly.
IPA_OVERRIDES = {
    "دلوقتي": "dɪlˈwaʔti",
    "عايز": "ˈʕaːjez",
    "عايزة": "ˈʕajza",
    "إزيك": "ʔezˈzajjak",
    "إزيكي": "ʔezˈzajjek",
    "إمتى": "ˈemta",
    "بقى": "ˈbaʔa",
}


def _apply_phoneme_overrides(text: str) -> str:
    for word, ipa in IPA_OVERRIDES.items():
        text = text.replace(
            word,
            f'<phoneme alphabet="ipa" ph="{ipa}">{word}</phoneme>',
        )
    return text


def build(text: str, *, voice: str | None = None, rate_pct: int = 5) -> str:
    """Return an Azure SSML document for the given Egyptian Arabic text."""
    voice_name = voice or settings.agent_voice
    safe = escape(text)
    safe = _apply_phoneme_overrides(safe)
    # Pause briefly after questions for natural turn-taking.
    safe = safe.replace("؟", '؟<break time="250ms"/>')
    return (
        '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        'xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="ar-EG">'
        f'<voice name="{voice_name}">'
        f'<prosody rate="{rate_pct:+d}%">{safe}</prosody>'
        "</voice></speak>"
    )
