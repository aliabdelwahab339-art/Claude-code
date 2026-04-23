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

1. In the Twilio console, buy an Egypt number (or a US/UK number if Egypt
   inbound regulation is not yet cleared — see **Egypt regulation** below).
2. Phone Numbers → Active Numbers → your number → Voice & Fax → **A Call Comes In**:
   set to `Webhook`, URL = `https://<app>.fly.dev/twilio/voice`, HTTP POST.
3. Call the number. You should hear the Egyptian-Arabic greeting.

### Egypt regulation (heads-up)

Egypt's NTRA requires a local entity + ID for inbound PSTN numbers. Options:

- Start **outbound-only** from a US/UK Twilio number (caller ID still reads
  the Twilio number). Good for cold-outreach pilots.
- Use a Twilio **regulatory bundle** via a local partner.
- Port an existing Egyptian landline you already operate.

The code is identical either way — only the Twilio number provisioning differs.

## 5. Daily operations

- Lead flow: check the Google Sheet tab configured in `GOOGLE_SHEET_TAB` (default `Leads`).
- Cost audit: `fly ssh console -C "python scripts/cost_rollup.py --days 7"`.
- Dialect eval: run `python -m tests.dialect_eval` locally against `tests/fixtures/*.wav`.
- Prompt iteration: edit `prompts/system_prompt_ar_eg.md` and redeploy.

## 6. Scaling

- Fly.io autoscale: set `min_machines_running = 2` in `fly.toml` once you
  regularly see >20 concurrent calls.
- Twilio concurrency limits: default is 1 call/sec for new accounts —
  request a limit raise before launch day.
- Anthropic rate limits: Haiku 4.5 org limits are generous; monitor 429s in
  logs and request a raise via the console if you hit them.
