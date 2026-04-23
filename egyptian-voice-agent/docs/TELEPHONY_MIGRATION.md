# Telephony migration — how to cut your bill 5–30×

Your telephony bill is 85–92% of total cost. Everything else (LLM, STT, TTS,
compute) is a rounding error at any volume under 100K minutes/month. So this
is the one doc that matters for unit economics.

There are three tiers. Move up the tier ladder as your volume justifies the
operational overhead of the next one.

## Tier 1 — Twilio (default, shipped code)

- **Rate to Egypt mobile:** ~$0.17/min blended
- **Setup:** regulatory bundle with your Egyptian entity (1–5 business days)
- **Pros:** everything works out of the box, `scripts/outbound_call.py` +
  Media Streams already wired.
- **Cons:** most expensive termination. No local caller-ID presence.
- **When to use:** pilot up to ~1,000 calls/month. Under that, the 25–95%
  savings from tiers 2–3 are smaller than the engineering time to migrate.

## Tier 2 — Wholesale SIP (DIDWW / CommPeak / AstraQom)

- **Rate to Egypt mobile:** ~$0.14–$0.18/min (20–30% below Twilio)
- **Setup:** open an account with DIDWW or CommPeak, request an Egypt rate
  sheet, get a SIP trunk (IP auth or username/password), port or buy an
  Egyptian DID through them. Timeline: 1–2 weeks.
- **Code changes:** swap Twilio for a SIP provider. The cleanest route is
  **LiveKit SIP** (Apache 2.0, self-hostable or cloud). You keep Pipecat as
  the pipeline, swap the transport. See *Code migration* below.
- **When to use:** 1,000–10,000 calls/month. Realistic monthly saving at
  10K calls: ~$1,500. Worth 1–2 weeks of engineering once.

## Tier 3 — Local Egyptian SIP (the big lever)

- **Rate to Egypt mobile:** ~$0.005/min (essentially free vs. Tier 1)
- **Providers:** Telecom Egypt Business, WE Business, Vodafone Egypt
  Business, Orange Egypt Business, Etisalat Misr.
- **Setup (operational — not code):**
  1. **NTRA Contact Center License** under NTRA's 2024 commercial-calling
     regulations. Takes 4–8 weeks. Your Egyptian entity applies; a lawyer
     familiar with telecoms law (~EGP 15–30K one-time fee) is recommended.
  2. **SIP trunk contract** with one of the local operators above, tied to
     your NTRA license. Most operators quote EGP/month plus per-minute
     rates; expect a ~EGP 3,000–10,000/mo base fee plus usage, plus a
     deposit.
  3. **Caller-ID registration** — every outbound number must be registered
     in the mobile operators' commercial-numbers database (the "NTRA
     Alert" / company-name system). Unregistered numbers get disconnected
     within weeks; repeat violators are permanently banned.
  4. **PDPC Electronic Marketing license** (see `COMPLIANCE.md`).
- **Code changes:** same as Tier 2 — LiveKit SIP with a different trunk
  configuration. Once LiveKit SIP is running, swapping trunks is a config
  change.
- **When to use:** ≥5,000 calls/month sustained. Break-even versus Tier 1
  is typically month 2. At 10K calls/month the saving is ~$4,400.

## Realistic math

At 10,000 calls/month × 3 min avg = 30,000 min/month:

| Tier | Telephony $/min | Monthly telephony | All-in $/call | Ops overhead |
|---|---|---|---|---|
| 1 — Twilio | $0.174 | $5,220 | $0.57 | None (shipped) |
| 2 — DIDWW wholesale | $0.145 | $4,350 | $0.48 | 1–2 wk engineering + BAA |
| 3 — Local EG SIP | $0.005 | $150 | $0.13 | NTRA license + local contract + ~1 month cal. time |

At 1,000 calls/month the absolute savings are smaller and Tier 1 is fine.

## Code migration (Tier 2 and Tier 3 both)

The current code talks to Twilio via Media Streams. The migration target is
**LiveKit SIP** because:

- Apache-2.0, cloud or self-host (self-host in `me-south-1` Bahrain for
  PDPL-clean data residency — see `COMPLIANCE.md`).
- Native SIP ingress for any Tier 2/3 trunk provider.
- Pipecat has a first-class `LiveKitTransport` — the STT→LLM→TTS pipeline
  in `src/egyptian_voice_agent/pipeline.py` is unchanged. Only the
  transport at the edges swaps out.

Rough shape of the migration:

1. Create a LiveKit project (cloud) or deploy LiveKit self-hosted.
2. Configure LiveKit SIP with your trunk credentials (IP-auth or
   user/pass depending on provider).
3. Add a `TRANSPORT=livekit` option alongside today's `TRANSPORT=twilio` —
   `pipeline.run_call()` already takes `direction` + context as plain
   args, so swapping the transport layer is isolated.
4. Configure the LiveKit SIP dispatch rule to route calls into a Pipecat
   worker room.
5. For outbound, use LiveKit's SIP "CreateSIPParticipant" REST API instead
   of `twilio.calls.create` in `src/egyptian_voice_agent/outbound.py`.

Keep the Twilio path in place during migration — flip per-call with an env
flag so you can roll back if the local trunk has quality issues on day one.

## Three other cost levers (smaller, but additive)

1. **Call-duration tuning.** The system prompt already pushes < 25-word
   turns; the April 2026 update (commit e2485d0+) tightens it further to
   target 90–120s median call length. That alone cuts ~30% off every
   telephony bill across all tiers.
2. **Opt-out short-circuit.** `src/egyptian_voice_agent/dialect/optout.py`
   intercepts opt-out phrases before the LLM, hangs up in ~3s instead of
   ~20s, and skips a Claude round-trip. Saves ~$0.10–$0.30 per opt-out call
   and is PDPL-required.
3. **Self-hosted TTS (future).** NAMAA-Egyptian-TTS or NileTTS on a single
   L4 GPU (~$400/mo fixed) breaks even on TTS spend around 25M
   characters/month (~28K calls). Below that, Azure + ElevenLabs is
   cheaper. Don't self-host early.

## When NOT to migrate

- Below 1,000 calls/month: stay on Twilio. Total bill at that volume is
  under $100/mo; the ops work on Tier 2/3 isn't justified.
- Inbound-heavy traffic (lead calls you): Twilio inbound is already
  ~$0.013/min, so the Tier-3 lever on outbound doesn't help much.
- If your product is high-AOV B2B (each closed lead >$1,000): quality
  matters more than $/min. Stay on Twilio and upgrade TTS instead.
