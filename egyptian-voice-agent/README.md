# Egyptian Voice Agent

An AI voice agent that answers your business phone in **Egyptian Arabic dialect** (العامية المصرية), qualifies inbound leads (BANT), and logs them to your CRM — built for cost efficiency at scale (~$0.10 per 3-minute call).

## What it does

- **Inbound:** picks up Twilio calls in a warm, natural Egyptian voice.
- **Outbound:** dials a list of Egyptian leads from a CSV or your CRM, respecting DNC and local calling hours.
- Runs a scripted BANT qualification (Need, Budget, Authority, Timeline) in Egyptian colloquial — never switches to MSA.
- Calls tools mid-conversation: `log_lead`, `book_callback`, `transfer_to_human`, `end_call`.
- Writes qualified leads to Google Sheets (default), HubSpot, or a generic webhook.
- Emits per-call telemetry (tokens, STT/TTS seconds, estimated $) as JSONL for weekly cost rollups.

## Stack

| Layer | Component |
|---|---|
| Telephony | Twilio Voice + Media Streams |
| Pipeline | Pipecat (async Python) |
| STT | Deepgram Nova-3 Arabic (streaming) — Azure ar-EG fallback |
| LLM | Claude Haiku 4.5 (Anthropic SDK, prompt caching on) |
| TTS | Azure Neural `ar-EG-SalmaNeural` / `ShakirNeural` — ElevenLabs optional |
| Deploy | Dockerfile + Fly.io |

## Quickstart (local)

```bash
git clone <this repo> && cd egyptian-voice-agent
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env      # fill in keys
python scripts/replay_wav.py tests/fixtures/ar_eg_greeting.wav
```

You should hear the agent's Egyptian Arabic reply saved to `out.wav` and see a `log_lead` tool call in the telemetry JSONL.

## Deploy (Fly.io)

```bash
fly launch --no-deploy
fly secrets import < .env
fly deploy
```

Point your Twilio number's Voice webhook at `https://<your-app>.fly.dev/twilio/voice`. Call it. Done.

## Outbound dialing

Single call:
```bash
python scripts/outbound_call.py \
  --to +201012345678 \
  --name "أحمد" \
  --context "متابعة طلب عرض السعر"
```

Batch from CSV (`to,name,context` columns; see `tests/fixtures/leads_example.csv`):
```bash
python scripts/outbound_call.py --csv leads.csv --pace 20 --max 50
```

Enforced guards:
- **DNC list** at `DNC_PATH` — E.164 numbers one per line, never dialed.
- **Calling hours** — 09:00–21:00 Cairo, Saturday–Thursday (Friday is off). Bypass with `--force` only when you have explicit consent.

Or trigger dials from your own system by POSTing to `/outbound/call` with an `X-API-Key` header matching `OUTBOUND_API_KEY`.

Full walkthrough: [`docs/DEPLOY.md`](docs/DEPLOY.md).

## Customize

- **Brand + persona:** set `BRAND_NAME`, `AGENT_NAME`, `AGENT_VOICE` in `.env`.
- **Script:** edit `prompts/system_prompt_ar_eg.md` — keep it in Egyptian Arabic, one question per turn.
- **CRM:** set `CRM_SINK=sheets|hubspot|webhook`.
- **Dialect tuning:** run `python -m tests.dialect_eval` — see [`docs/DIALECT_TUNING.md`](docs/DIALECT_TUNING.md).

Full customization guide: [`docs/CUSTOMIZE.md`](docs/CUSTOMIZE.md).

## Cost per 3-min call (estimate)

| Component | Cost |
|---|---|
| Twilio (inbound + Media Streams) | $0.051 |
| Deepgram STT | $0.023 |
| Claude Haiku 4.5 | ~$0.007 |
| Azure TTS | ~$0.014 |
| Compute (amortized) | ~$0.001 |
| **Total** | **~$0.096** |

## License

MIT — see [LICENSE](LICENSE).
