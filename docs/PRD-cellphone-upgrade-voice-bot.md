# Product Requirements Document (PRD)

**Product name:** Cellphone Upgrade Advisor (voice bot)  
**Platform:** AudioCodes Live Hub  
**Document status:** Draft v0.1 — for brainstorming  
**Owner:** גל  
**Last updated:** 2026-08-25

This document describes a voice agent that helps a customer decide whether they can upgrade their phone, whether a trade-in is possible, and what they would pay given their budget.

Open decisions are marked **[TBD]**. Working assumptions used so this draft is concrete are marked **[Assumption]**.

---

## 1. Why this product exists

Customers who want a new phone often do not know:

- what their current device is worth
- whether it qualifies for trade-in
- what a target device costs after trade-in
- whether that amount fits their budget

The bot’s job is to collect those facts in a spoken conversation, compute a clear quote, and tell the caller if the upgrade (and optional trade-in) is possible.

This is **not** a full checkout / SIM-port / contract-signing system in v1. It is an **advisor** that ends with a quote and a recommended next step.

---

## 2. Goals and non-goals

### 2.1 Goals (v1)

1. Collect, in one call, the four required facts:
   - current device
   - desired new device
   - whether the customer wants a trade-in
   - budget for the new device
2. If trade-in is requested, assess **eligibility** from a short condition questionnaire (voice-only).
3. Return a spoken quote:
   - list / sale price of the new device
   - trade-in credit (or why there is none)
   - estimated amount due
   - whether that amount is within budget
4. Stay inside Live Hub: native **AI Agent** + **Tools** + **Documents**, then a **Bot Connection** and a test channel (browser / WebRTC first).
5. Produce a post-call structured summary of slots (device, trade-in, quote) for later review.

### 2.2 Non-goals (v1)

- Completing a purchase, taking a credit card, or binding a contract
- Diagnosing hardware with photos or a technician
- Unlocking, IMEI blacklists, or carrier-account authentication **[Assumption: no CRM/login in v1]**
- Multi-line family plans, accessories bundles, insurance upsell (unless asked later)
- Human live-agent transfer as a required path **[TBD]**
- WhatsApp / SMS as a primary channel in v1 (phone or WebRTC only)

---

## 3. Success definition

A call is a **success** if all of the following are true:

| Criterion | Definition |
|-----------|------------|
| Slots complete | Current device, target device, trade-in intent (yes/no), budget |
| Quote given | Caller hears amount due and “fits budget / over budget” |
| Trade-in rule applied | If yes: eligible / ineligible with a reason; if no: quote without credit |
| Call ends cleanly | Bot confirms the caller has no more questions, then hangs up or offers a recap |
| No hallucinated catalog | Prices and trade-in values come from tools or the uploaded catalog, not from the LLM’s general knowledge |

**Target for a student / demo MVP [Assumption]:** 8 of 10 scripted test calls complete the success definition.

---

## 4. Users and context

| Actor | Description |
|-------|-------------|
| Caller | Person considering an upgrade. No login. Speaks naturally. |
| Bot | Live Hub AI Agent “Upgrade Advisor”. |
| Catalog / pricing backend | Source of truth for devices, prices, trade-in values. **[TBD: mock JSON vs real retailer API]** |
| Operator (you) | Configures agent, documents, tools, routing, and test suites in Live Hub. |

**Language [TBD]:** Hebrew, English, or both. Voice UX must be designed for the chosen language (device names, currency, number reading).

**Market [TBD]:** which country, currency, and retailer/carrier this represents (e.g. Israeli cellular operator vs generic demo store). This changes device names, VAT, and trade-in rules.

---

## 5. Live Hub architecture (how we will actually build it)

Live Hub is the runtime: telephony or WebRTC in, STT → AI Agent → TTS out.

Recommended v1 stack:

```
Caller (phone or browser WebRTC)
        │
        ▼
Live Hub routing rule  →  Bot Connection
        │                      │
        │                      ├─ STT provider
        │                      ├─ TTS provider + voice
        │                      └─ Language + barge-in
        ▼
Live Hub AI Agent
        │
        ├─ System prompt (persona + numbered conversation steps)
        ├─ Documents (catalog, FAQ, policy text) — grounding
        ├─ Tools (lookup current device, lookup target, quote, end call)
        ├─ Optional strict Flow (if we need a fixed script)
        └─ Post-call analysis (extract slots + quote)
```

### 5.1 Live Hub components we will use

| Component | Role in this product |
|-----------|----------------------|
| **AI Agent** | Persona, welcome message, numbered instructions, tool-use rules |
| **Documents** | Price list, trade-in matrix, eligibility policy (so the model does not invent prices) |
| **Tools** | Deterministic lookups and quote calculation; `end_call`; optional `transfer` later |
| **Flows** | Optional: force slot order if free-form LLM skipping is too unreliable |
| **Bot Connection** | Bind agent to STT/TTS, barge-in, language |
| **Routing** | Map a test number or WebRTC widget to this bot |
| **Test suites** | Scripted utterances before “go live” |
| **Post-call analysis** | Structured JSON: devices, condition, quote, outcome |
| **Logs / dashboard** | Debug missed slots, tool failures, latency |

### 5.2 Why tools exist (not “just a prompt”)

AudioCodes’ own prompt guidance: if the model is not forced to call tools, it may answer from general knowledge. For money, **the prompt must instruct the agent to call quote/lookup tools** and never invent a number.

**[Assumption]** v1 uses:

1. Live Hub native AI Agent (not Dialogflow / Lex / custom Bot API), to ship faster.
2. A small HTTP tool backend (or Live Hub tool that hits a mock API) for catalog + quote.
3. Documents as a fallback explanation of policy, not as the only price source.

If a hosted API is not ready, a **static catalog document + a quote tool with the catalog embedded** is acceptable for demo, as long as the agent is forbidden from quoting without the tool.

### 5.3 Channel plan

| Phase | Channel | Purpose |
|-------|---------|---------|
| 0 | Live Hub browser test call | Fast iteration |
| 1 | WebRTC click-to-call widget | Demo without a DID |
| 2 | Purchased / ported number or SIP trunk | Real phone UX **[TBD]** |

---

## 6. Conversation product (what the caller experiences)

### 6.1 Persona

- Name: **[TBD]** (working name: “Maya” / “the upgrade assistant”)
- Tone: short sentences, one question at a time, no jargon unless the caller uses it.
- Voice: TTS voice matching language **[TBD]**.
- Barge-in: **on** so callers can interrupt long lists **[Assumption]**.

### 6.2 Welcome

Example (English; Hebrew equivalent TBD):

> Hi, I’m the phone upgrade assistant. I can check a new device, optional trade-in, and whether it fits your budget. Shall we start?

If the caller says no → polite goodbye and end call.

### 6.3 Required slots

Collect in a **logical order**, but accept out-of-order answers (“I have an iPhone 13, I want a 16, budget 2000, no trade-in”).

| Slot ID | What to capture | Voice notes |
|---------|-----------------|-------------|
| `current_device` | Brand + family + generation (e.g. iPhone 13, Galaxy S23) | Confirm back: “You currently have an iPhone 13 — is that right?” |
| `target_device` | Desired model, storage if it changes price | If vague (“the new Samsung”), offer 2–3 catalog options, do not dump 20 models |
| `trade_in_intent` | yes / no | If no, skip condition questions |
| `device_condition` | Only if trade-in = yes | See §7 |
| `budget_amount` | Number + currency | Repeat the number; confirm currency |
| `quote` | Computed, not asked | Spoken once, then recap if asked |

Storage, color, and carrier variant are **optional in v1** unless they change price in the catalog.

### 6.4 Happy-path flow (numbered — this becomes the agent prompt)

1. Greet and confirm they want upgrade advice.
2. Ask for **current device**. Confirm.
3. Ask for **target device**. If unknown or not in catalog, say so and offer closest in-catalog alternatives. Confirm.
4. Ask if they want to **trade in** the current device.
5. If yes → condition questionnaire (§7). If no → skip.
6. Ask for **budget**. Confirm the number.
7. **Call the quote tool** with current device, target device, trade-in flag, condition grade, budget.
8. Speak the result in this order: new price → trade-in credit or reason for zero → amount due → fits budget or not.
9. Offer: repeat the numbers / change one slot / end.
10. End call with a one-line recap.

### 6.5 Example dialogues (abridged)

**A — Trade-in, in budget**

- Bot: current device?  
- User: iPhone 13.  
- Bot: upgrade to?  
- User: iPhone 16.  
- Bot: trade-in?  
- User: yes.  
- Bot: screen cracked? power on? battery swelling?  
- User: no / yes / no.  
- Bot: budget?  
- User: 1500 shekels.  
- Bot: iPhone 16 is 4299. Trade-in credit 800. Amount due 3499. That is over your 1500 budget. You can raise the budget, pick a cheaper model, or skip trade-in — which do you want?

**B — No trade-in, in budget**

- Quote uses full list price vs budget; no condition questions.

**C — Trade-in rejected**

- Condition fails policy → credit = 0, explain in one sentence, still quote full price vs budget.

---

## 7. Trade-in eligibility (voice-only assessment)

The bot **cannot inspect the phone**. Eligibility is a **declared condition grade**, not a physical inspection. The spoken disclaimer must make that clear.

**[Assumption]** v1 uses a small yes/no set, then maps to a grade:

| Question (ask one at a time) | Fail if |
|------------------------------|---------|
| Does the phone power on? | No → ineligible |
| Is the screen badly cracked or unreadable? | Yes → ineligible **or** reduced credit **[TBD]** |
| Is the body badly bent or missing parts? | Yes → ineligible |
| Does the battery swell or overheat? | Yes → ineligible |
| Is the device reported stolen / not yours? | Yes → ineligible (legal) |

**Possible outcomes**

| Outcome | Meaning |
|---------|---------|
| Eligible — good | Full matrix value for that model |
| Eligible — fair | Reduced value (e.g. 50%) **[TBD if v1 needs two grades]** |
| Ineligible | Credit = 0; still allow purchase-at-full-price advice |

Always say:

> This is an estimate based on what you told me. Final trade-in is confirmed when the store inspects the device.

---

## 8. Pricing and “is it possible?” logic

All money math happens in a **tool**, not in the LLM.

### 8.1 Inputs

- `current_sku` (resolved from spoken name)
- `target_sku`
- `trade_in`: boolean
- `condition_grade`: `good` | `fair` | `ineligible` | `skipped`
- `budget`: number
- `currency`: **[TBD]**

### 8.2 Outputs (spoken + stored)

| Field | Rule |
|-------|------|
| `list_price` | Catalog price of target |
| `trade_in_credit` | 0 if no trade-in or ineligible; else matrix[current_sku][grade] |
| `amount_due` | max(0, list_price − trade_in_credit) |
| `within_budget` | amount_due ≤ budget |
| `possible` | Target exists in catalog **and** (if they require trade-in as a must-have, eligibility is true) **[TBD: is “possible” only about catalog + budget, or also trade-in?]** |

**Advice rules**

1. If `within_budget` → “Yes, this upgrade fits your budget. Amount due is X.”
2. If not → “It does not fit. You are short by Y.” Then offer, in order:
   - cheaper in-catalog target in the same family
   - proceed without trade-in only if that was increasing due (usually trade-in **lowers** due — so the useful alternatives are cheaper phone or higher budget)
   - stop
3. If target not in catalog → cannot quote; offer 2–3 similar models from tool `search_devices`.
4. If current device not in trade-in matrix and they want trade-in → credit 0, explain “we don’t have a trade-in value for that model in this demo catalog.”

**Installments / VAT / promotions:** out of scope unless you add them later.

---

## 9. Catalog (data the bot is allowed to use)

**[Assumption]** v1 ships a **demo catalog** of ~8–15 popular devices (Apple + Samsung), each with:

- display name (how people say it)
- aliases (13, “thirteen”, “אייפון 13”)
- sku
- list_price
- trade_in_value_good
- trade_in_value_fair (optional)
- brand, family, generation

The catalog is both:

1. a **Live Hub Document** (human-readable policy + table) for explanations
2. the **tool backend’s JSON** as source of truth for numbers

Keep them in sync. If they diverge, the tool wins.

---

## 10. Tools (Live Hub)

Tool descriptions must be short and explicit. The prompt must say: *never state a price or trade-in value unless this tool returned it.*

| Tool | When | Key parameters | Returns |
|------|------|----------------|---------|
| `resolve_device` | After user names a device | raw utterance | sku, display_name, confidence, alternatives[] |
| `get_quote` | After slots are filled | current_sku, target_sku, trade_in, condition_grade, budget | list_price, credit, amount_due, within_budget, message_code |
| `search_cheaper_targets` | Over budget | target_sku, budget, current_sku, trade_in, grade | up to 3 alternatives with amount_due |
| `end_call` | User done or refuses | reason | — |

Optional later: `transfer_to_agent`, `send_sms_recap`.

**Failure handling:** if a tool errors, say we cannot calculate right now; do not guess.

---

## 11. Prompt and flow design (Live Hub-specific)

Follow AudioCodes prompt practice:

- Numbered steps matching §6.4.
- One question at a time.
- Confirm numbers and model names by repeating them.
- Explicit tool calls: `Use get_quote with …`
- Use **variables / prompt conditions** if we add flags (e.g. skip trade-in block when `trade_in_intent` is false).
- Prefer a **strict Flow** only if test calls show the LLM skipping slots. Start with prompt + tools; add Flow if needed.

**Guardrails in the prompt**

- Do not give legal, medical, or stolen-device advice beyond “we cannot take this for trade-in.”
- Do not claim a locked-in price.
- Do not list the entire catalog unprompted.
- If the user goes off-topic, one-sentence redirect.

---

## 12. Speech, NLU, and voice UX risks

Voice is messier than chat. Design for:

| Risk | Mitigation |
|------|------------|
| “iPhone 15” vs “15 Pro” vs “15 Pro Max” | Confirm disambiguation with two options, not five |
| Hebrew/English mix (Heblish) | Language policy **[TBD]**; aliases in catalog |
| Budget “two thousand” vs 2000 vs 2K | Confirm digit form |
| Barge-in cutting the quote | Repeat-on-request; keep quotes short |
| STT errors on model names | Phonetic aliases; confirmation loop (max 2 retries then offer spelling or “Apple or Samsung?”) |
| Long silences | Reprompt once, then offer to end |

---

## 13. Error, edge, and policy cases

| Case | Bot behavior |
|------|----------------|
| Caller wants a device not sold here | Not in catalog; offer nearest 2–3 |
| Caller does not know current model | Ask brand → year-ish → “Settings → About” style hint (one short hint); if still unknown, continue **without** trade-in |
| Caller changes a slot mid-call | Update slot, re-run `get_quote` |
| Abusive / empty audio | End politely after 2 failures |
| Caller asks to buy now | “I only advise. A store or website completes the sale.” |
| Caller insists the LLM’s memory of street prices | Refuse; catalog only |

---

## 14. Privacy, compliance, recording

**[TBD]** with Live Hub region, GDPR/Israeli privacy, and whether calls are recorded.

v1 defaults:

- Do not ask for ID number, full IMEI, credit card, or account password.
- Optional last-4 IMEI only if a future eligibility API needs it — **not in v1**.
- Post-call summary stores devices, grades, and amounts — treat as demo data unless production rules apply.
- Disclaimer that trade-in is estimate-only.

---

## 15. Analytics and post-call analysis

Configure Live Hub **post-call analysis** to extract:

```json
{
  "current_device": "string",
  "target_device": "string",
  "trade_in_intent": true,
  "condition_grade": "good|fair|ineligible|skipped",
  "budget": 0,
  "currency": "ILS",
  "list_price": 0,
  "trade_in_credit": 0,
  "amount_due": 0,
  "within_budget": true,
  "outcome": "quoted|cannot_quote|abandoned",
  "notes": "string"
}
```

Dashboard: completion rate, tool error rate, average turns to quote.

---

## 16. Testing (before adding features)

Live Hub **test suites** plus a written script pack:

1. Happy path, trade-in eligible, in budget  
2. Happy path, no trade-in, in budget  
3. Trade-in ineligible, still quote  
4. Over budget → cheaper alternatives  
5. Unknown current device  
6. Unknown target → disambiguation  
7. Caller changes target after quote  
8. Out of catalog brand  
9. Barge-in during quote  
10. Hebrew or mixed language **[if in scope]**

Do not add installment logic, CRM, or WhatsApp until these pass.

---

## 17. Delivery phases (small increments)

Aligned with building in Live Hub without a giant first drop.

| Phase | Deliverable |
|-------|-------------|
| **P0 — this PRD** | Agreed slots, quote rules, Live Hub shape |
| **P1 — catalog** | JSON + Document with 8–15 devices and trade-in values |
| **P2 — tools** | `resolve_device` + `get_quote` against that catalog |
| **P3 — agent** | Welcome, prompt steps, tool wiring, end_call |
| **P4 — bot connection** | STT/TTS, barge-in, browser test call |
| **P5 — hardening** | Confirmations, over-budget alternatives, test suite |
| **P6 — optional** | DID/SIP, WebRTC widget, Hebrew, human transfer |

---

## 18. Open decisions (must resolve to freeze v1)

These are the items still marked TBD in this draft. Answers will be edited into this file as v0.2.

1. Language(s) and currency.  
2. Real operator/retailer vs generic demo store.  
3. Native Live Hub AI Agent vs external bot (Dialogflow, custom API). **Recommendation: native AI Agent.**  
4. Strict Flow vs prompt-only for slot order. **Recommendation: prompt-first.**  
5. One condition grade vs good/fair/ineligible.  
6. Cracked screen: reject vs reduced credit.  
7. Does “possible” require trade-in success, or only “we can sell you this phone”?  
8. Human handoff required in v1?  
9. Catalog size and which models.  
10. Whether amount due can be 0 (trade-in ≥ list price) and how to word that.  
11. Recording / data retention.  
12. Target channel for the first demo (browser vs real phone number).

---

## 19. Assumptions log (v0.1)

- Advisor only; no checkout.  
- No customer authentication.  
- Demo catalog is source of truth.  
- Voice-declared condition is enough for an *estimate*.  
- Barge-in enabled.  
- Native Live Hub AI Agent + HTTP tools.  
- English draft copy until language is chosen.  
- Single caller, single line, one upgrade per call.

---

## 20. References (Live Hub)

- Live Hub product: https://www.audiocodes.com/livehub  
- AI Agents overview: https://techdocs.audiocodes.com/livehub/Content/AI-Agents/AI%20Agents.htm  
- Prompt engineering (numbered steps, force tool use): https://techdocs.audiocodes.com/livehub/Content/AI-Agents/Prompt-engineering.htm  
- Build/deploy agent (agent → bot connection → test → routing): Live Hub Help Center, “Building and Deploying an AI Agent”  
- Bot API (only if we later leave native agents): https://techdocs.audiocodes.com/livehub/Content/LiveHub/AudiocodesAPI-framework.htm  

---

## 21. Next edit to this document

After the brainstorm answers, update:

- §4 language/market  
- §7 condition rules  
- §8 “possible” definition  
- §9 initial SKU list  
- §17 phase dates if you want them  

Then freeze **v1 scope** and implement P1 (catalog) only.
