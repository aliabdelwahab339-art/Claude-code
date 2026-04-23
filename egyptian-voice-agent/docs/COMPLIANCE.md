# Compliance (Egypt)

This is not legal advice. Get a telecoms + data-protection lawyer licensed
in Egypt before going live. What follows is the operational shape of what
you need to have in place.

## The two laws that will stop you from operating

### 1. NTRA — commercial calling registration (since Aug 2025)

Since August 2025, Egypt's National Telecommunications Regulatory Authority
actively disconnects unregistered outbound commercial-calling numbers, with
permanent bans for repeat violators. Every caller-ID number you dial from
must be:

- Registered in the mobile operators' commercial-numbers database.
- Labeled with either your **company name** or an "**NTRA Alert**" tag,
  which is shown on the recipient's handset screen during the call.
- Tied to an **NTRA Contact Center License** held by your Egyptian entity.

Obtaining the contact-center license takes 4–8 weeks. A telecoms lawyer
(~EGP 15–30K) handles the NTRA filings, the commercial registration
attachments, and the follow-up with operators.

Fines have teeth: Mountain View (real estate) was fined EGP 20M in
October 2024 and referred to prosecution for unregistered marketing calls.

### 2. PDPL — Personal Data Protection Law (operational since Nov 10, 2025)

Law 151/2020 was largely dormant until **Decree 816/2025** activated it on
November 10, 2025. It's GDPR-style. You, as a controller of Egyptian
personal data (phone numbers, voice recordings, CRM entries), must:

1. **Register with the PDPC** (Personal Data Protection Center) as a data
   controller. One-time filing, annual renewal.
2. **Appoint a Data Protection Officer** (DPO). EGP 2M fine for
   non-appointment. The DPO can be an employee or an outsourced service;
   small firms commonly outsource for ~$500–2,000/month.
3. **Obtain an "Electronic Marketing" license** from the PDPC before doing
   any outbound direct marketing. Separate from the NTRA license.
4. **Collect explicit, informed consent** before processing a phone number
   or voice. For warm inbound leads (they submitted a form with a consent
   checkbox), the consent is already documented. For cold outbound, you
   need a lawful basis — legitimate interest works narrowly but consent is
   cleaner.
5. **Disclose AI status and call recording in the greeting** (bilingual,
   Arabic + English in case the lead is English-first). The shipped
   outbound greeting at `prompts/greeting_outbound_ar_eg.md` already does
   this — do not remove it.
6. **Honor opt-out immediately and permanently**. The pipeline's
   `dialect/optout.py` processor short-circuits the LLM on opt-out phrases
   and hangs up within seconds. The `scripts/outbound_call.py` dialer
   respects a DNC CSV; add opt-out numbers to it within 24 hours of the
   request.
7. **Restrict cross-border transfer.** Article 14 requires PDPC
   authorization or explicit consent before moving Egyptian personal data
   outside Egypt. Azure regions `uaenorth` and AWS `me-south-1` (Bahrain)
   are the practical near-in-region choices. Today's shipped Fly.io
   deployment is in Frankfurt (`fra`) — fine for a pilot, but **you'll
   want to migrate to a MENA region before Tier-3 launch** (see
   `fly.toml`; change `primary_region` and re-deploy to `cdg` → `bah`
   when Fly.io offers it, or move to AWS Bahrain).

Voice is personal data under Article 1. **Unauthorized voice cloning of a
real Egyptian speaker** (e.g., cloning a voice actor without written
consent) exposes you to fines up to EGP 5M plus criminal liability under
the Anti-Cybercrime Law 175/2018. If you upgrade TTS to ElevenLabs with a
cloned voice, use Professional Voice Cloning which requires documented
consent from the speaker, and retain that consent in your DPO records.

## Checklist before you launch Tier 1

- [ ] Egyptian entity registered (commercial registration, tax ID)
- [ ] Appoint a DPO (internal or outsourced). Document in writing.
- [ ] PDPC registration as data controller filed.
- [ ] PDPC Electronic Marketing license obtained.
- [ ] Consent copy on your website / form / CRM intake flow.
- [ ] Outbound greeting includes AI disclosure + recording disclosure.
      Verify on `prompts/greeting_outbound_ar_eg.md`.
- [ ] Opt-out phrases in `dialect/optout.py` reviewed by your DPO.
- [ ] Written data-processing agreements (DPA) with every sub-processor:
      Twilio, Deepgram, Anthropic, Azure, Google (for Sheets),
      ElevenLabs if used. All four majors have standard GDPR-style DPAs
      that generally satisfy PDPC; confirm with your lawyer.
- [ ] Retention policy documented: how long you keep call recordings,
      transcripts, telemetry JSONL. Default shipped behavior writes
      telemetry indefinitely to `$TELEMETRY_PATH` — implement rotation
      (cron / logrotate) to match your retention policy.

## Checklist to add before Tier 3 (local Egyptian SIP)

- [ ] NTRA Contact Center License.
- [ ] SIP trunk contract with a licensed local operator (Telecom Egypt /
      WE / Vodafone Egypt / Orange / Etisalat).
- [ ] Every caller-ID registered in the mobile operators' commercial-
      numbers database, labeled with your company name.
- [ ] Migrate hosting into Egypt or Bahrain for data residency.
- [ ] Revisit DPA with the new SIP provider.

## What the code enforces automatically

Not a substitute for the paperwork, but the agent won't help you break
these rules by accident:

- **Calling hours:** `outbound.within_calling_hours()` blocks dials outside
  09:00–21:00 Cairo, Sat–Thu (Friday rest day). Bypass only with explicit
  lead consent.
- **DNC:** `outbound.DNC.load()` silently skips any number in your DNC CSV.
- **Opt-out detection:** `dialect/optout.py` matches Egyptian opt-out
  phrases on the STT transcript before the LLM runs, emits `end_call`
  with `outcome="not_qualified"`, and hangs up. No sales pitch after an
  opt-out — PDPL Article 12 + consumer-protection law.
- **Machine detection:** Twilio `DetectMessageEnd` is enabled on all
  outbound — you won't pitch to voicemail.
- **E.164 validation:** `outbound.place_call` rejects non-E.164 numbers.

## What the code cannot do for you

- Obtain the licenses.
- Pay the fines.
- Register your caller IDs.
- Verify a sub-processor's DPA.
- Document consent capture on your intake forms.

Those are human operations. Put them on a checklist; review quarterly.

## If you skip any of this

- **Skip NTRA registration** → caller-ID disconnected within weeks,
  permanent ban for repeat violations. Operation dies.
- **Skip PDPC registration / DPO** → EGP 2M fine for no DPO, up to EGP 5M
  for serious violations, criminal exposure.
- **Skip consent + opt-out** → PDPL + Consumer Protection Law 181/2018 +
  potential Anti-Cybercrime Law exposure. Mountain View's EGP 20M fine is
  the reference point.
- **Skip cross-border controls** → worst case is a PDPC order to stop
  processing, which kills your service until you migrate hosting.

This is not optional overhead — it's the cost of being allowed to operate.
Build it in on day one, not on day 90.
