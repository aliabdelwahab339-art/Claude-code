# Customize

Everything you'd change per customer or per product launch.

## Brand + persona

Edit `.env`:

```env
BRAND_NAME=شركة النور
AGENT_NAME=مروة
AGENT_VOICE=ar-EG-SalmaNeural    # or ar-EG-ShakirNeural for a male voice
```

Both brand and agent name are injected into the system prompt via `{{brand}}`
and `{{agent_name}}` placeholders — no code changes required.

## The script

Live at `prompts/system_prompt_ar_eg.md`. Keep in mind:

1. **It must stay in Egyptian colloquial**, never MSA. The first-page rules
   about forbidden MSA words (`حضرتك تفضّل`, `لقد`, `سوف`, `إنّ`) are what
   stop Claude from drifting — don't delete them.
2. **One question per turn.** Longer turns feel like a survey.
3. **Confirm before moving on.** "فاهمة إنك عايز ... صح؟" — this mirrors
   natural Egyptian conversation and halves misunderstandings.
4. Keep BANT questions in the same order unless you know what you're doing.
   Budget-first kills a lot of leads emotionally.

After editing, redeploy (`fly deploy`) or restart the local server.

## First-turn greeting

`prompts/greeting_ar_eg.md` is what the agent says before the caller speaks.
Keep it under 15 seconds and include the consent/recording notice — some
jurisdictions require it.

## CRM sink

Pick one in `.env`:

- `CRM_SINK=sheets` (default) — append to a Google Sheet. Simplest. Needs
  `GOOGLE_SERVICE_ACCOUNT_JSON` + `GOOGLE_SHEET_ID`.
- `CRM_SINK=hubspot` — create a contact + a task. Needs `HUBSPOT_ACCESS_TOKEN`.
- `CRM_SINK=webhook` — POST JSON to any URL. Needs `CRM_WEBHOOK_URL`.

To add a new sink, implement the `CRMSink` protocol in
`src/egyptian_voice_agent/integrations/crm/__init__.py` and register it in
`get_sink()`.

## Voice

Azure ar-EG options:

- `ar-EG-SalmaNeural` — female, warm, default
- `ar-EG-ShakirNeural` — male, steady

If the voice feels flat on a specific product, try these in order:

1. Bump `rate_pct` in `dialect/ssml.py:build()` (default `+5`). Try `+8`.
2. Add IPA overrides for key product terms in `dialect/ssml.py:IPA_OVERRIDES`.
3. Switch to ElevenLabs: `TTS_PROVIDER=elevenlabs`, set
   `ELEVENLABS_API_KEY` + `ELEVENLABS_VOICE_ID` (a cloned Egyptian voice
   works best — clone from 3–5 minutes of real Cairo dialect audio).

ElevenLabs Flash v2.5 is ~2× the per-call TTS cost; only upgrade when the
default actually hurts conversion.

## Tools

Tool schemas live in `src/egyptian_voice_agent/llm/tools.py`. To add a new
one (e.g. `send_whatsapp_brochure`):

1. Define a pydantic `BaseModel` with the arguments.
2. Append a dict to `TOOLS` with `name`, `description`, and `input_schema`.
3. Add a branch in `dispatch()` that runs the side effect and returns an
   ar-EG confirmation string.
4. Mention the tool in `prompts/system_prompt_ar_eg.md` under "الأدوات (Tools)".

## Dialect tuning

Measure before you tune. See [`DIALECT_TUNING.md`](DIALECT_TUNING.md).
