# Deploy

End-to-end setup: API keys → local run → Fly.io → Twilio.

## 1. API keys you need

| Service | What for | Where |
|---|---|---|
| Anthropic | LLM (Claude Haiku 4.5) | <https://console.anthropic.com> |
| Deepgram | Streaming Arabic STT | <https://console.deepgram.com> |
| Azure Speech | Egyptian TTS (+ optional fallback STT) | Azure portal → Cognitive Services → Speech |
| Twilio | Phone number + Media Streams | <https://console.twilio.com> |
| Google Cloud service account (optional) | Google Sheets CRM sink | IAM → Service accounts → JSON key |

Put them in `.env` (copy from `.env.example`).

## 2. Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env          # fill in keys
python -m egyptian_voice_agent # http://0.0.0.0:8080
```

Sanity-check: `curl http://localhost:8080/health` should return JSON with your brand/voice.

Text-only dialogue dev loop (no audio, no Twilio):
```bash
python scripts/local_call.py
```

WAV replay (no Twilio, real STT + LLM + SSML):
```bash
python scripts/replay_wav.py tests/fixtures/ar_eg_greeting.wav
```

## 3. Deploy to Fly.io

```bash
fly auth login
fly launch --no-deploy           # registers app; pick a unique name
fly volumes create voice_agent_data --size 1 --region fra
fly secrets import < .env        # or: fly secrets set KEY=value ...
# If using Google Sheets, also upload the SA JSON:
fly secrets set GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT="$(cat path/to/sa.json)"
fly deploy
```

If using Google Sheets, adjust `Dockerfile` or add a small startup script to
write `$GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT` to `$GOOGLE_SERVICE_ACCOUNT_JSON`
on boot.

Verify:
```bash
fly logs
curl https://<app>.fly.dev/health
```

## 4. Wire up Twilio

1. In the Twilio console, buy an Egypt number. You'll need to submit a
   regulatory bundle via Twilio using your Egyptian entity's commercial
   registration / tax ID (CRN) and a proof of local address. Approval
   usually takes 1–5 business days.
2. Phone Numbers → Active Numbers → your number → Voice & Fax → **A Call Comes In**:
   set to `Webhook`, URL = `https://<app>.fly.dev/twilio/voice`, HTTP POST.
3. Set `TWILIO_PHONE_NUMBER=+20...` in `.env` (or `fly secrets set`). This is
   the caller ID used for outbound dials too.
4. Call the number. You should hear the Egyptian-Arabic greeting.

## 5. Make outbound calls

The agent can both receive and place calls. Outbound uses the same pipeline
with an outbound-specific greeting.

**Single call (for testing):**
```bash
python scripts/outbound_call.py \
  --to +201012345678 \
  --name "أحمد" \
  --context "متابعة طلب عرض السعر"
```

**Batch from a CSV** (columns: `to,name,context`; sample at
`tests/fixtures/leads_example.csv`):
```bash
python scripts/outbound_call.py --csv leads.csv --pace 20 --max 50
```

**From your own system**, POST to the HTTP endpoint:
```bash
curl -X POST https://<app>.fly.dev/outbound/call \
  -H "X-API-Key: $OUTBOUND_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"to":"+201012345678","lead_name":"أحمد","context":"متابعة"}'
```

### Compliance guardrails (enabled by default)

- **DNC list.** Path at `DNC_PATH` (one E.164 per line, `#` comments allowed).
  Any number in this list is silently skipped.
- **Calling hours.** 09:00–21:00 Cairo local time, Saturday–Thursday.
  Friday is a rest day and skipped by default. Bypass with `--force` **only
  when you have explicit consent from the lead** (e.g. they booked a 10 PM
  callback themselves).
- **Machine detection.** Twilio's `DetectMessageEnd` mode is enabled — the
  pipeline will not speak to voicemail.
- **Opt-out.** The system prompt instructs the agent to immediately end any
  call where the lead says "ما تكلمنيش تاني" (don't call me again). Add
  those numbers to your DNC CSV and redeploy.

## 6. Daily operations

- Lead flow: check the Google Sheet tab configured in `GOOGLE_SHEET_TAB` (default `Leads`).
- Cost audit: `fly ssh console -C "python scripts/cost_rollup.py --days 7"`.
- Dialect eval: run `python -m tests.dialect_eval` locally against `tests/fixtures/*.wav`.
- Prompt iteration: edit `prompts/system_prompt_ar_eg.md` and redeploy.

## 7. Scaling

- Fly.io autoscale: set `min_machines_running = 2` in `fly.toml` once you
  regularly see >20 concurrent calls.
- Twilio concurrency limits: default is 1 call/sec for new accounts —
  request a limit raise before launch day.
- Anthropic rate limits: Haiku 4.5 org limits are generous; monitor 429s in
  logs and request a raise via the console if you hit them.
