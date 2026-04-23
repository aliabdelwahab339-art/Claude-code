# Telephony — Tier-3 landline is the destination

Your target architecture is a commercial **Egyptian landline SIP trunk**
(Telecom Egypt / WE Business, Vodafone Business, Orange Business, or
e& Business) behind **LiveKit SIP**, with caller-ID registered against an
**NTRA contact-center license**.

Everything else in this codebase — Twilio, Pipecat, Deepgram, Claude,
Azure TTS — stays the same. The transport layer swaps; the pipeline
doesn't care.

## Why landline and not mobile SIP

1. **Cost:** landline SIP trunks from Egyptian operators price outbound
   minutes at roughly EGP 0.03–0.15/min (~$0.001–0.005) vs. Twilio's
   ~$0.17/min. That's a 30–150× cut on the dominant line item.
2. **Pickup rate:** Egyptian recipients heavily screen unknown mobile
   caller-IDs because of spam saturation. A registered landline DID
   (02-... Cairo, 03-... Alexandria, etc.) typically sees **1.5–2× the
   answer rate** of a mobile caller-ID. That effectively halves your cost
   per connected conversation on top of the per-minute saving.
3. **Regulatory simplicity:** landline-based SIP trunks are a standard
   business product from every Egyptian operator. You still need the
   NTRA contact-center license for high-volume outbound, but the trunk
   itself is turnkey from a licensed operator and comes with compliance
   attached.

## Where to start

If you have a specific company in mind that's already running a voice
agent on an Egyptian landline, ask them one question:

> "إنتوا متعاقدين مع مين على الـSIP trunk بتاع التليفون الأرضي؟"

Their answer is almost certainly one of: WE Business, Vodafone Business,
Orange Business, or e& Business. Go to the same operator with your
Egyptian entity's commercial registration in hand.

If you have no reference, **default to WE Business (Telecom Egypt)** —
largest network, broadest landline-DID inventory, most competitive
published rates. Detailed product list, sales script, and document
checklist: [`LANDLINE_PROVISIONING.md`](LANDLINE_PROVISIONING.md).

## Timeline

Plan ~8–12 weeks from "decision made" to "first production call":

| Week | Activity |
|---|---|
| 1 | Engage a telecoms lawyer; start the NTRA contact-center license filing |
| 1–2 | Operator sales call; request SIP trunk quote + product sheet |
| 2 | Sign operator contract; pay setup fee + deposit; operator begins provisioning |
| 2–3 | Operator activates trunk in test mode (inbound + on-net only) |
| 3–4 | Engineering: LiveKit project setup; wire trunk credentials into this codebase; end-to-end test call |
| 4–8 | NTRA license processing (lawyer follows up); PDPC registration in parallel |
| 8–10 | NTRA license issued; operator enables commercial outbound |
| 10–12 | Caller-ID registration propagates across mobile operators; scale up volume |

Tier-1 Twilio stays running during this whole period. You can run a pilot
(~500 calls/month) on Twilio while the paperwork processes, so you're
collecting prompt-tuning data and lead-qualification insights from day one
instead of waiting 10 weeks.

## The code migration (once credentials arrive)

One commit, contained to these files:

1. `src/egyptian_voice_agent/outbound.py` — LiveKit SIP branch dials via
   `livekit.api.LiveKitAPI.sip.create_sip_participant()` instead of
   `twilio.Client.calls.create()`.
2. `src/egyptian_voice_agent/transport/livekit.py` (new) — builds Pipecat's
   `LiveKitTransport` for inbound rooms dispatched by LiveKit SIP.
3. `src/egyptian_voice_agent/worker.py` (new) — long-running agent worker
   that registers with LiveKit, joins rooms as they're created, runs the
   existing pipeline.
4. `pyproject.toml` — add `livekit`, `livekit-api` to the `[sip]` optional
   deps group.

The shipped outbound path (`outbound.place_call()`) already branches on
`settings.telephony_provider`. Today the `livekit_sip` branch raises with
a "fill in SIP trunk credentials" error — that lights up as soon as you
set the env vars.

Nothing in the pipeline itself (STT → LLM → TTS) changes. The prompts
don't change. The tools don't change. Only the transport swap.

## One-time upfront cost to reach Tier 3

| Item | Cost (one-time) |
|---|---|
| Telecoms lawyer — NTRA + PDPC filings | EGP 20,000–40,000 (~$400–800) |
| NTRA contact-center license fee | EGP 10,000–25,000 (~$200–500) |
| PDPC data-controller registration | EGP 5,000–10,000 (~$100–200) |
| PDPC Electronic Marketing license | EGP 10,000–20,000 (~$200–400) |
| Operator setup fee + deposit (held, refundable) | EGP 5,000–15,000 (~$100–300) |
| LiveKit Cloud first-month starter | $0 (free tier covers pilot) |
| **Subtotal out-of-pocket** | **~$1,000–2,200** |

Recovered in **2–6 weeks** of operating at 1,000+ calls/month. At 10,000
calls/month the whole one-time budget is paid back in ~4 days of
telephony savings vs. Tier 1.

## Tier 2 (wholesale SIP) — skip it

Tier 2 (DIDWW / CommPeak / AstraQom wholesale SIP without an Egyptian
operator contract) was in the earlier version of this doc. **Skip it as
a destination.** Reasoning:

- It saves ~20–30% vs. Twilio. Tier 3 saves ~95%.
- The LiveKit-side code migration is identical — you're doing the
  engineering work anyway.
- The regulatory track (NTRA license) is the same.
- Wholesale caller-IDs don't carry the Egyptian-landline trust signal
  that drives answer rates, so you keep half the loss of going to mobile.

Tier 2 is only interesting as a **transitional bridge** if you need to get
off Twilio before the NTRA license lands — which is rarely justified
because Twilio works fine for pilot volumes (<1K calls/mo).

## When to stay on Tier 1 anyway

- Monthly call volume below ~500. Absolute savings (under ~$70/month) are
  smaller than the lawyer's retainer.
- Testing a new product line: stay on Twilio until you've validated the
  conversion economics before committing to the Tier-3 overhead.
- Inbound-only workloads: Twilio inbound is already ~$0.013/min, so the
  Tier-3 lever on outbound doesn't help much.

## Where to read next

- **[`LANDLINE_PROVISIONING.md`](LANDLINE_PROVISIONING.md)** — the step-
  by-step playbook: operators, sales script, trunk credentials, plugging
  them into this codebase.
- **[`COMPLIANCE.md`](COMPLIANCE.md)** — NTRA + PDPL in detail, required
  before live operation.
- **[`COSTS.md`](COSTS.md)** — full cost model at each tier and volume.
