# Cost model

Total monthly cost at three telephony tiers, two call-volume scenarios,
and the one-time setup costs. Per-minute rates change — verify with each
provider before committing a budget.

## Unit rates (as of late 2025 / early 2026)

### Telephony (the 85–92% of your bill)

| Provider | Egypt mobile outbound | Egypt landline outbound | Egypt inbound |
|---|---|---|---|
| Twilio (shipped) | $0.187/min | $0.172/min | $0.013/min |
| DIDWW / CommPeak wholesale | ~$0.145/min | ~$0.125/min | ~$0.01/min |
| Telecom Egypt / WE / Vodafone Egypt local SIP | ~$0.005/min | ~$0.005/min | n/a |
| Twilio Media Streams (added to any Twilio minute) | $0.004/min | $0.004/min | $0.004/min |

For Tier-3 local SIP you'll pay an additional EGP 3,000–10,000/month fixed
trunk fee, plus an NTRA license setup cost (~EGP 15–30K one-time lawyer
fee). Factored into the monthly totals below.

### AI components

| Component | Rate | Notes |
|---|---|---|
| Deepgram Nova-3 Arabic streaming | $0.0077/min | $200 signup credit |
| Claude Haiku 4.5 | $1 / $5 per MTok in/out | ~$0.006 per 3-min call with prompt caching |
| Azure Neural TTS ar-EG | $16/M chars | **500K chars/month free** |
| ElevenLabs Flash v2.5 (optional upgrade) | $0.05 / 1K chars | Only if Azure quality insufficient |

### Fixed infrastructure

| Item | Cost |
|---|---|
| Twilio Egypt local DID | ~$1.50/mo |
| Fly.io shared-1x 512 MB (1 machine, warm) | ~$3.75/mo |
| Fly.io 1 GB volume for telemetry | $0.15/mo |
| Google Sheets / HubSpot API | free |
| Domain (optional) | ~$1/mo |

## Scenario — 1,000 calls/month × 3 min average

| Line | Tier 1 (Twilio) | Tier 2 (Wholesale SIP) | Tier 3 (Local EG SIP) |
|---|---|---|---|
| Outbound telephony | $510 | $435 | $15 |
| Media Streams (Tier 1 only) | $12 | — | — |
| Deepgram STT | $23 | $23 | $23 |
| Claude Haiku | $5.70 | $5.70 | $5.70 |
| Azure TTS | $6.40 | $6.40 | $6.40 |
| Fixed infra (DID, Fly.io, volume, domain) | $6.40 | $6.40 | $6.40 |
| Local trunk fee (Tier 3 only) | — | — | ~$130 (EGP 6,500) |
| **Total** | **~$563** | **~$476** | **~$187** |
| **Per call** | **$0.56** | **$0.48** | **$0.19** |

## Scenario — 10,000 calls/month × 3 min average

| Line | Tier 1 (Twilio) | Tier 2 (Wholesale SIP) | Tier 3 (Local EG SIP) |
|---|---|---|---|
| Outbound telephony | $5,100 | $4,350 | $150 |
| Media Streams (Tier 1 only) | $120 | — | — |
| Deepgram STT | $231 | $231 | $231 |
| Claude Haiku | $57 | $57 | $57 |
| Azure TTS (9M chars) | $136 | $136 | $136 |
| Fixed infra | $30 | $30 | $30 |
| Local trunk fee | — | — | ~$200 |
| **Total** | **~$5,674** | **~$4,804** | **~$804** |
| **Per call** | **$0.57** | **$0.48** | **$0.08** |

At 10K calls/month, **Tier 3 saves ~$4,870/month vs. Tier 1** — more than
$58K/year. This is the single biggest financial decision in the stack.

## One-time costs

| Item | Cost |
|---|---|
| Twilio regulatory bundle (your Egyptian entity + CRN + address proof) | $0 |
| Twilio DID setup | ~$1 |
| Twilio prepaid starter | $20 |
| Azure free-tier + first-month $200 credit | $0 |
| Deepgram $200 signup credit | $0 |
| Anthropic signup | $0 |
| Domain (optional) | $12/yr |
| **NTRA Contact Center License (Tier 3 prerequisite)** | **~EGP 15–30K (~$300–600) + lawyer** |
| **PDPC registration as data controller** | ~EGP 5–10K (~$100–200) |
| **PDPC Electronic Marketing license** | ~EGP 10–20K (~$200–400) |
| **DPO appointment** | $0–$2K/mo if outsourced |
| **Total one-time (Tier 1 only)** | **~$33** |
| **Total one-time (Tier 3 target)** | **~$600–1,200 + legal fees** |

Tier-3 one-time costs are recovered in 2–3 weeks of Tier-3 savings at 10K
calls/month.

## How to read this

1. **Start on Tier 1.** Ship, iterate on the prompt, get the first 200
    calls right. Total cost under $150.
2. **If you're seeing >1,000 calls/month and the economics work, start the
    Tier-3 paperwork** (NTRA license, PDPC registration — both take 4–8
    weeks). In parallel, do the Tier-2 code migration to LiveKit SIP so the
    switch to local SIP is one config change later.
3. **Skip Tier 2 as a destination** — it's a 15–20% improvement at best,
    and the operational work to set it up is 80% of Tier 3's work.
4. **At Tier 3, AI becomes your dominant cost** (STT + TTS + LLM ≈ 53% of
    the bill). That's the healthy state — you're now buying quality
    minutes, not termination.

## What NOT to worry about

- LLM cost. At 10K calls/mo, Haiku 4.5 is $57/month. Switching to
  Gemini Flash-Lite saves ~$50/month — not worth the integration work and
  the loss of prompt caching.
- Self-hosted TTS. Break-even is ~25M chars/month (≈28K calls). Below that,
  a GPU ($400–800/mo) costs more than Azure TTS.
- Compute. Fly.io under $30/month even at 10K calls.
- Storage. Telemetry JSONL grows ~1 KB/call. You won't fill 1 GB in a year
  at 10K calls/month.
