# Landline provisioning — step by step

This is the operational playbook to go from "Egyptian entity in hand" to
"first outbound call over a commercial landline SIP trunk at ~$0.005/min."

It covers:
1. Which operator to contract with
2. What product to ask for
3. The NTRA license track (runs in parallel)
4. What the trunk credentials look like when they land
5. Plugging those credentials into this codebase

Everything below is based on public information as of late 2025. Pricing and
package names change; get written quotes before budgeting.

## 1. Pick an operator

Four realistic choices for a commercial SIP trunk with landline caller-ID
in Egypt:

| Operator | Product | Typical base fee | Per-minute (local / mobile) | Notes |
|---|---|---|---|---|
| **Telecom Egypt / WE Business** | WE Business Voice (IP Centrex / SIP Trunk) | EGP 500–2,000/mo | EGP 0.03–0.08 / EGP 0.10–0.18 | Largest network, most landline DIDs, best for Cairo/Alex/Giza. Default choice. |
| **Vodafone Egypt Business** | Vodafone Business Voice / Smart PBX | EGP 800–3,000/mo | EGP 0.05–0.10 / EGP 0.12–0.20 | Strong mobile-side termination rates (good if most leads are Vodafone mobile). |
| **Orange Business Egypt** | Orange Business Voice | EGP 600–2,500/mo | EGP 0.04–0.09 / EGP 0.11–0.19 | Decent enterprise SLA, smaller landline inventory. |
| **Etisalat Misr (e&)** | e& Business Voice | Similar range | Similar range | Usually 3rd choice unless your target leads skew e& mobile. |

**Default recommendation:** start with **WE Business (Telecom Egypt)**
because they have the largest landline-DID inventory and the best published
rates for the SIP trunk product. If your ideal-customer profile is
predominantly on one mobile operator, quoting that operator for outbound
can yield 15–25% savings on your mobile minutes through on-net pricing —
worth a second quote.

## 2. What to ask for (verbatim script for the sales call)

Call the operator's business sales line and say this. Adjusting the
numbers to your volume:

> "عايز SIP Trunk تجاري مربوط برقم أرضي ثابت بالقاهرة/الإسكندرية (حسب موقعك).
> نحتاج قناة واحدة متزامنة في البداية مع إمكانية التوسع، وباقة تبدأ من ٥٠٠٠ دقيقة خارجية
> شهرياً (محمول + أرضي داخل مصر). نحتاج اعتماد SIP بـ IP-Auth أو Username/Password،
> ودعم كودك G.711 μ-law للصوت. متى تقدروا تفعّلوه بعد توقيع العقد؟"

Rough translation: commercial SIP trunk tied to a fixed Cairo or Alex
landline DID, one concurrent channel initially with room to scale, 5,000
minute starter bundle, IP-auth or username/password SIP registration,
G.711 μ-law codec.

Things to confirm in writing before signing:

- **Caller-ID behavior**: confirm your Egyptian landline DID is presented
  as caller-ID on outbound mobile (this is what drives pickup rate).
- **NTRA requirement**: confirm the operator accepts your NTRA contact-
  center license at activation. Most require it for commercial outbound.
- **Per-minute rates broken out**: local landline, mobile by carrier
  (Vodafone / Orange / e& / WE), international disabled by default.
- **Concurrent-channel pricing**: each additional simultaneous call
  channel is usually EGP 200–500/mo extra.
- **Setup fee** (usually EGP 1,000–3,000 one-time) and **deposit**
  (commonly 2–3 months of base fee held as security).
- **Contract term**: typically 12 months. Negotiate a 30-day opt-out after
  month 3 if volumes don't materialize.
- **Codec + transport**: G.711 μ-law 8 kHz, SIP over UDP or TLS. If they
  insist on opus or G.729, flag it — Pipecat's Twilio serializer won't
  drop in cleanly; you'd need to transcode.

## 3. The NTRA Contact Center License — start this in parallel

You need this for any high-volume outbound marketing from Egypt under the
2024 regulations. Without it, operators will refuse to enable your trunk
for outbound commercial calling, and unregistered caller-IDs get
disconnected within weeks.

**What it is:** a license from Egypt's National Telecommunications
Regulatory Authority (NTRA) authorizing your entity to operate a
contact-center / outbound-calling service.

**How to obtain it:**

1. Hire a telecoms lawyer licensed in Egypt. Expect **EGP 15,000–30,000**
   one-time for the filing and follow-up. Any of the bigger firms
   (Zulficar & Partners, Sharkawy & Sarhan, ALC, Shalakany) have telecoms
   desks; solo practitioners with telecoms experience are cheaper and
   often just as effective.
2. Documents the lawyer will ask you to provide:
   - Commercial registration (السجل التجاري) of your Egyptian entity
   - Tax card (البطاقة الضريبية)
   - Managing director ID
   - Brief description of the contact-center service (inbound +
     outbound, expected call volumes, use cases)
   - Registered Egyptian office address (contract or lease)
3. NTRA processing time: **4–8 weeks** once filing is complete. Plan for 10
   weeks to be safe.
4. Fee paid to NTRA: varies by scope, commonly **EGP 10,000–25,000**
   one-time, plus an annual renewal (~EGP 5,000–10,000/year).

Start this the same week you sign the operator contract. The two tracks
run in parallel, not sequentially. The operator will typically activate
the SIP trunk for testing (inbound + internal calls) before your license
lands, then enable commercial outbound once you produce the license.

## 4. PDPL registration (runs in parallel too)

Separate from NTRA. Required under Decree 816/2025. See `COMPLIANCE.md`
for the full list. At minimum before going live:

- Register as data controller with the Personal Data Protection Center.
- Obtain the PDPC **Electronic Marketing license**.
- Appoint a DPO in writing.

Combined PDPC cost: roughly EGP 20,000–40,000 one-time (filings +
lawyer), plus ongoing DPO cost.

## 5. What the trunk credentials look like when they arrive

When the operator activates your trunk, they send a document (usually PDF
or a signed letter) with these fields. Save these — they go straight into
`.env` on the app side:

```
# From Telecom Egypt / WE Business / etc.
SIP Domain / Proxy:       sip.webusiness.eg  (example — yours will differ)
SIP Port:                 5060 (UDP) or 5061 (TLS)
Registration Type:        IP-Auth OR Username/Password
  If IP-Auth:
    Authorized source IPs:  <your Fly.io app egress IPs — they ask you for these>
  If User/Pass:
    Username:               21000123456@sip.webusiness.eg
    Password:               <long random string>
Assigned DID(s):          +20224xxxxxx  (Cairo landline; +20340xxxxxx = Alex)
Outbound Caller-ID:       <your registered landline DID>
Concurrent Channels:      1 (scale up via amendment)
Codec:                    G.711 μ-law, 8 kHz, 20 ms ptime
DTMF:                     RFC 2833 (out-of-band)
```

**IP-auth vs user/pass:** IP-auth is simpler but requires a stable egress
IP for your app. Fly.io machines have rotating egress IPs unless you pay
for a dedicated egress (~$2/month). Username/password is more portable and
works from any host; minor latency overhead on SIP REGISTER. Default to
username/password unless the operator strongly prefers IP-auth.

## 6. Register the caller-ID with NTRA

Once the trunk is live and your NTRA license is in hand:

1. Submit a caller-ID registration form to NTRA listing every DID you
   plan to present as caller-ID on outbound. Operators usually file this
   for you as part of activation.
2. Decide on the display label: **company name** (e.g., "Acme Egypt") OR
   the generic "NTRA Alert" marker. Company name is strongly preferred —
   it reads more legitimate to recipients and drives a materially higher
   pickup rate.
3. Wait for NTRA confirmation (typically 1–2 weeks) before high-volume
   outbound. Small-volume testing with an unlabeled caller-ID is usually
   tolerated during the registration window, but don't scale until
   confirmation lands.

## 7. Plug the credentials into this codebase

The code supports this path out of the box. When your credentials arrive:

1. Set up a LiveKit project (LiveKit Cloud is fine for pilot; self-host
   in AWS `me-south-1` Bahrain for cleaner PDPL posture at scale).
2. In the LiveKit console, create an **Inbound SIP Trunk** with the
   credentials from step 5, and an **Outbound SIP Trunk** with the same
   credentials + your assigned caller-ID as the `from_number`.
3. Copy the LiveKit `URL`, `API Key`, `API Secret`, and both SIP trunk
   IDs into `.env`:
   ```
   TELEPHONY_PROVIDER=livekit_sip
   LIVEKIT_URL=wss://<project>.livekit.cloud
   LIVEKIT_API_KEY=...
   LIVEKIT_API_SECRET=...
   SIP_TRUNK_ID=ST_xxxxxxxx         # outbound trunk id from LiveKit
   SIP_OUTBOUND_ADDRESS=sip.webusiness.eg
   SIP_OUTBOUND_USERNAME=21000123456@sip.webusiness.eg
   SIP_OUTBOUND_PASSWORD=<from the operator>
   NTRA_LICENSE_NUMBER=<for your records + logs>
   TWILIO_PHONE_NUMBER=+20224XXXXXX  # keep set to your landline DID; used
                                     # as outbound caller-ID by the dialer
   ```
4. `fly deploy`. Make a test call with `python scripts/outbound_call.py
   --to +20YOUROWNMOBILE --name "اختبار" --context "تجربة"`.
5. Confirm your phone shows the landline DID (or company name if NTRA
   registration has propagated). Confirm call audio quality.

## 8. Cost reality check

After all of the above, running 10K calls/month looks like:

| Item | Monthly |
|---|---|
| Operator base fee (WE Business Voice mid-tier) | EGP 1,500 (~$30) |
| Outbound minutes (30K min × blended EGP 0.12) | EGP 3,600 (~$72) |
| Deepgram STT | ~$231 |
| Claude Haiku | ~$57 |
| Azure TTS | ~$136 |
| LiveKit Cloud (at this volume, a Scale plan) | ~$50–$150 |
| Fly.io compute (MENA region once supported, or Bahrain AWS) | ~$30 |
| NTRA license amortized annual renewal | ~EGP 500 (~$10) |
| DPO (outsourced small-firm monthly) | ~$500–$1,000 |
| **Total monthly (target)** | **~$1,100–$1,700** |
| **Per call** | **~$0.11–$0.17** |

Notes on the numbers:
- LiveKit Cloud pricing varies; self-hosted LiveKit on a single $20/mo VPS
  handles up to ~50 concurrent calls and drops that line to near zero
  once you're confident in operations.
- DPO is the biggest recurring non-telephony cost at this point. Shop
  around — some boutique privacy firms charge EGP 3,000–5,000/mo flat.
- Compared to the Tier-1 Twilio baseline (~$5,700/mo at this volume),
  you're saving ~$4,000–$4,600/month — that funds the DPO and the NTRA
  renewal many times over.

## 9. Ongoing operational checklist (monthly)

- Review the telemetry JSONL cost rollup (`scripts/cost_rollup.py --days 30`).
- Confirm caller-ID still displays the registered label (spot-check from a
  colleague's phone on each major Egyptian mobile network).
- Update the DNC CSV with any opt-out numbers from the past month and
  `fly deploy`.
- Review 10 random call recordings with the DPO for consent + opt-out
  handling quality.
- Verify operator invoice reconciles with your telemetry minute-count.
  Discrepancies of >5% are worth chasing — operators occasionally bill by
  rounded-up minutes rather than per-second.
