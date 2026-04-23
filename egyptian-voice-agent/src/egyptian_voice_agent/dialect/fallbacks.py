"""Post-processing for Arabic STT output.

Deepgram's Arabic model occasionally mis-transcribes high-frequency Egyptian
colloquial words. This module applies a small, high-confidence set of rewrites
before the transcript hits the LLM.
"""

from __future__ import annotations

import re

# (pattern, replacement). Word-boundary-anchored to avoid mid-word damage.
_REWRITES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?<!\S)ماش(?!\S)"), "مش"),
    (re.compile(r"(?<!\S)دلوا?قت(ي|ى)?(?!\S)"), "دلوقتي"),
    (re.compile(r"(?<!\S)ازاي(ك)?(?!\S)"), "إزيك"),
    (re.compile(r"(?<!\S)امتي(?!\S)"), "إمتى"),
    (re.compile(r"(?<!\S)عاوز(?!\S)"), "عايز"),
    # Strip MSA filler that slips in when caller code-switches mid-turn
    (re.compile(r"(?<!\S)لقد(?!\S)"), ""),
    (re.compile(r"(?<!\S)سوف(?!\S)"), "ح"),
]


def normalize_egyptian(text: str) -> str:
    out = text
    for pattern, repl in _REWRITES:
        out = pattern.sub(repl, out)
    # collapse runs of whitespace introduced by deletions
    out = re.sub(r"\s+", " ", out).strip()
    return out
