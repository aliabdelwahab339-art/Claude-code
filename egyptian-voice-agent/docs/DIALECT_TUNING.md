# Dialect tuning

How to measure and improve the agent's Egyptian-Arabic accuracy.

## 1. Record a representative set

10 WAV clips — mono, 16 kHz, ≤ 15s each. Cover at minimum:

- Greeting
- Budget question answer
- Objection
- Callback request
- Heavy slang
- Noisy mobile (motorbike / street)
- Fast male speaker
- Slow female speaker
- Code-switch (Arabic + English)
- Spoken numerals ("تلات مرات")

Save them in `tests/fixtures/` and add reference transcripts to
`tests/fixtures/ground_truth.json`.

## 2. Run the eval

```bash
python -m tests.dialect_eval
```

Output is a rich table of `ref | hyp | WER` and a mean WER. Gates:

| Provider | Gate |
|---|---|
| Deepgram Nova-3 Arabic | < 18% WER |
| Azure ar-EG (fallback) | < 12% WER |

## 3. If Deepgram misses common words

Two places to fix:

1. `src/egyptian_voice_agent/dialect/keywords_ar_eg.txt` — append the word.
   Passed to Deepgram as streaming `keywords` at runtime (capped at 200 for
   model performance).
2. `src/egyptian_voice_agent/dialect/fallbacks.py` — add a `(pattern,
   replacement)` tuple if the same mis-transcription appears every time.
   Use word boundaries (`(?<!\S)...(?!\S)`) to avoid mid-word damage.

Re-run the eval. If WER is still above 18% after two passes, switch
`STT_PROVIDER=azure` and use Deepgram only as fallback.

## 4. If the TTS voice feels robotic

Azure ar-EG is a neural voice — it's good but not perfect. In order of
cheapness:

1. Tweak prosody in `dialect/ssml.py:build()` — `rate_pct=+5` → try `+8` to
   `+10` for energy; add `<mstts:express-as style="friendly">` wrappers for
   warmer delivery (Salma supports a handful of styles).
2. Add IPA overrides for the 5–10 product-specific words the voice mangles
   (`IPA_OVERRIDES` dict).
3. If still bad, flip to ElevenLabs Flash v2.5 with a **cloned** Egyptian
   voice. Generic ElevenLabs Arabic voices default to MSA; the only way to
   get reliable Egyptian dialect is a clone trained on ≥ 3 min of real
   Cairo-dialect audio.

## 5. Transcript review loop

Every week:

1. Pull the last 50 call recordings from Twilio.
2. Spot-check 10 for tool-use correctness and dialect drift.
3. If the agent is sliding into MSA, strengthen the forbidden-words list in
   `prompts/system_prompt_ar_eg.md`.
4. If qualification is missing context, add a "قبل ما تنادي log_lead، اتأكدي
   من ..." rule.

## 6. What "good" looks like

A healthy week:

- Mean STT WER < 15% on the 10-clip harness
- `log_lead` fires on ≥ 80% of calls that reach turn 4
- Mean call duration 120–210s (under 90s usually means the caller hung up
  on a clumsy turn; over 300s usually means the agent stopped moving the
  BANT forward)
- Est. cost / call from `scripts/cost_rollup.py` within 10% of $0.10
