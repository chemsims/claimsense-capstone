# ClaimSense AI — Engagement Charter (Milestone 1)

**Client:** Motor insurer (claims division) · **Engagement:** 5 weeks, discovery → handover
**FDE:** Sat Virk · **Charter date:** 2026-11-19 · **Status:** Draft for sponsor sign-off

## 1. The problem (the real one, not the stated one)

**Stated ask:** "Make the adjuster's first pass faster."

**Real problem:** One adjuster is the only integration layer between three systems that do not talk to each other. For every claim they open the claims system, the policy system and the document store, re-key and cross-check by hand, then write a first decision. Three things follow:

1. **Throughput is capped by one pair of hands.** The queue waits on manual gathering, not on judgment.
2. **Judgment is invisible.** Two adjusters can reach different decisions on the same file, and the reasons are not recorded anywhere an auditor can check.
3. **Fraud referral is a score threshold, not a reading of the file.** A 2:14 AM unwitnessed loss with a contradictory medical note looks like any other claim unless the score happens to be high.

A bigger rule table does not fix this. Coverage depends on the wording of a policy clause, and fraud depends on whether the story is consistent across documents. The synthetic data already shows the trap: claim CLM-2024-2822 has policy status "Active", but the loss date (2024-01-31) is three days after the policy ended (2024-01-28). A rule table approves it. A reader denies it.

## 2. What we will build (scope)

A **claims adjudication co-pilot**. Given a claim, it returns:

- a **first decision** — one of four outcomes: **APPROVE**, **DENY**, **FLAG** (send to a senior adjuster: total loss, injury, missing or contradictory evidence) or **ROUTE_SIU** (refer to the fraud unit);
- the **reasoning**, in plain language an adjuster and an auditor can check;
- **citations** to the evidence the reasoning rests on (policy clause IDs, document IDs, claim fields).

If the requesting user is not entitled to the claim, it **refuses** and returns no claim data.

A **licensed adjuster confirms every outcome.** The co-pilot recommends; it never decides and never pays.

**Fixed constraints (from the client brief):**

| Done in code (deterministic, testable) | Done by the model (judgment, always cited) |
|---|---|
| Identity and access control | Reading the whole file |
| Policy dates — was the policy in force on the loss date | Does the clause wording cover this loss |
| Money — deductible, payout, total-loss ratio | Is the story consistent across documents (fraud) |
| | Drafting the decision and reasons |

Synthetic data only. No production or personal data at any stage.

## 3. The three client systems and their integration points

| # | System | What we need from it | Join key | Direction (MVP) | Access risk |
|---|---|---|---|---|---|
| 1 | **Claims management system (CMS)** | Claim record: loss date, incident type, narrative, damage, repair estimate, ACV, injuries, police report flag, assigned adjuster, prior claims, fraud score, status | `claim_id` (also `policy_id`, `vehicle_vin`) | **Read** claim. **Write** one thing only: a recommendation record (decision, reasons, citations, model version), idempotent per `claim_id` + version | Medium — writes need the CMS owner's sign-off |
| 2 | **Policy administration system (PAS)** | Policy term (start/end), coverage type, collision/comprehensive flags, deductibles, liability and med-pay limits, insured VIN, plus the **policy clause text** for retrieval | `policy_id`, cross-checked against `vehicle_vin` | **Read only** | High — holds personal data of policyholders; security gate |
| 3 | **Document store** | Document list per claim (FNOL, police report, medical report, repair estimate, photos, witness statements, rental receipts), OCR status, OCR text | `claim_id` → `document_id` | **Read only** | Medium — OCR may be "Pending"; the co-pilot must treat pending documents as missing evidence |

**Integration points in the flow:**
1. User asks for claim → **access check in code** against the user's identity and the CMS assignment (before any agent runs). Denied → refusal + audit record.
2. CMS claim → PAS policy via `policy_id`; **VIN match and term check in code**.
3. CMS claim → document store via `claim_id`; OCR text into the file the model reads.
4. PAS clause corpus → retrieval; coverage output must cite clause IDs actually retrieved.
5. Recommendation → written back to CMS as a draft for adjuster confirmation. Only the adjuster's confirmation changes claim status.

## 4. Out of scope (where the MVP stops)

- Paying claims, issuing letters, or changing claim status.
- Third-party liability and subrogation decisions.
- Bodily-injury valuation (injury cases are FLAGGED, not valued).
- Any real or production data. Any change to the existing fraud-score model.

## 5. How we will know it worked

Four quantified success criteria are in `success-criteria.md`: decision accuracy, pipeline latency, adjuster confirmation rate and fraud routing accuracy. They become the SoW acceptance criteria in Week 2 and the CI evaluation gate in Weeks 3–5.

## 6. Open questions for the client (asked, not assumed)

1. What is today's baseline: minutes per first pass, inter-adjuster agreement, current SIU referral hit rate? (Needed to set targets against a real number.)
2. Total-loss threshold: what ratio of repair estimate to ACV makes a total loss in your book? (Working assumption: 75%.)
3. Is the policy end date inclusive? (Working assumption: yes, the policy covers losses on the end date.)
4. Who may see a claim: assigned adjuster only, or the adjuster's team and supervisor too?
5. Does a hit-and-run need a police report before payment?

**Sign-off:** Sponsor (VP Claims) ______ · Security (CISO) ______ · FDE ______
