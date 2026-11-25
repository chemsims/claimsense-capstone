# DECISIONS.md

Architectural decisions for the ClaimSense AI engagement, newest at the bottom. Each entry records what we decided, why, what we rejected, and when to revisit. If someone later says "that's not what we agreed", this file is the record.

---

## D-001 · 2026-11-19 · Week 1 is discovery only

- **Decision:** No production build until the four success criteria are agreed in writing by the sponsor.
- **Why:** Nobody at the client can define success yet, and baselines are unknown. Building now means building the wrong thing fast.
- **Alternatives:** Ship a prototype to "show momentum" — rejected; momentum toward an undefined target is just risk. A throwaway POC is allowed only to test one risky assumption (can we read the data?).
- **Owner:** FDE. **Revisit:** after charter sign-off.

## D-002 · 2026-11-19 · A deterministic spine: code owns facts, the model owns judgment

- **Decision:** Identity, access control, policy-in-force on the loss date, VIN match, deductibles, payout and the total-loss ratio are computed in Python. The model only reads the file, judges coverage wording and narrative consistency, drafts the decision, and must cite evidence for each judgment. Model output is typed (OpenAI Agents SDK structured output) and every response marks which fields came from code and which from the model.
- **Why:** These are fixed client constraints, and the data proves the risk: CLM-2024-2822 shows `policy_status = Active` but the loss is three days after the term ended. Policy-in-force is therefore computed from `policy_start`/`policy_end`, **never** from the status field. Money and dates must be exact and unit-testable.
- **Alternatives:** Let one LLM do everything with a long prompt — rejected; untestable, and a model can be talked into a wrong date or amount. Pure rule table — rejected; it cannot read clause wording or spot contradictions.
- **Owner:** FDE. **Revisit:** Week 2 architecture review.

## D-003 · 2026-11-19 · Four decision outcomes, plus refusal as a separate response

- **Decision:** The co-pilot returns exactly one of **APPROVE**, **DENY**, **FLAG** (needs a senior adjuster: total loss, injury, missing or contradictory evidence) or **ROUTE_SIU** (refer to fraud unit). **REFUSE** is not a decision outcome: it is the access layer's response when the user is not entitled, and it returns no claim data.
- **Why:** The client brief lists "approve, flag, route, or deny". Keeping refusal outside the decision enum means access control can never be "decided" by the model.
- **Assumption to confirm:** We read "flag" as human-review and "route" as SIU referral. If the client means the reverse, only labels change.
- **Alternatives:** A free-text recommendation — rejected; cannot be scored or gated in CI.
- **Owner:** FDE + Claims Supervisor. **Revisit:** when the client confirms the taxonomy.

## D-004 · 2026-11-19 · Read-only integrations; one idempotent write-back

- **Decision:** MVP reads from all three systems. The only write is a recommendation record to the claims system, keyed by `claim_id` + recommendation version so retries never create duplicates. Only an adjuster's confirmation changes claim status.
- **Why:** Lowers the CISO and system-owner veto risk (see `charter/stakeholders.md`), keeps a human accountable for every outcome, and removes any path for the co-pilot to pay or close a claim.
- **Alternatives:** Co-pilot updates `claim_status` directly — rejected; it turns a recommendation into a decision.
- **Owner:** FDE + CMS owner. **Revisit:** Week 4 (integration and access).

## D-005 · 2026-11-19 · Fraud routing reads the file; the score is one input

- **Decision:** ROUTE_SIU is chosen from contradictions across the file (timeline, documents vs claim fields, cross-claim history on the same VIN), with the existing `fraud_risk_score` as one cited input — not a threshold.
- **Why:** The brief names threshold-based referral as part of the problem. The data shows why: CLM-2024-3041 has a low score (0.11) but is a new collision on a Civic that CLM-2024-1946 says was totaled seven days earlier.
- **Alternatives:** Keep the score threshold and add rules — rejected; misses low-score contradictions and floods SIU with high-score clean claims.
- **Owner:** FDE + SIU lead. **Revisit:** after first eval run.

## D-006 · 2026-11-19 · Evals first, in the repo, gating CI

- **Decision:** The 20 seed cases live in `evals/seed_cases.jsonl` with expected outcomes and the reason for each. They grow to 150 by Week 5. From Week 3, a failing eval gate blocks the image push.
- **Why:** The success criteria are only real if a test can fail. Writing cases now, with the client, stops later arguments about what "accurate" meant.
- **Alternatives:** Write evals after the build — rejected; the build would be tuned to what it already does.
- **Owner:** FDE. **Revisit:** weekly.

## D-007 · 2026-11-23 · Price as a fixed floor plus an acceptance-criteria bonus

- **Decision:** $151,000 fixed floor, plus $7,500 for each of AC1–AC4 met on the held-out 150-case set (max $181,000). Run costs passed through.
- **Why:** The pilot is synthetic-only, so there are no real resolved claims to price per outcome. The criteria are already measurable, and a bonus on them keeps the outcome alignment without inventing volume.
- **Alternatives:** T&M with cap (scope is already clear, so it gives the client less certainty than it needs). Pure fixed (vendor carries all controls-review delay). Per-claim outcome pricing (deferred to the production phase, once a baseline exists).
- **Owner:** FDE + VP Claims. **Revisit:** at production SoW.

## D-008 · 2026-11-23 · One access layer in our service; no separate MCP server in the pilot

- **Decision:** All client-system calls go through one FastAPI access layer that verifies the token, checks entitlement, strips fields and writes the audit record. Agents get only typed tools that run inside it.
- **Why:** 3 systems, request/reply, 5 weeks. One governed door gives the same control (scope in code, audit every call) with fewer moving parts.
- **Alternatives:** Dedicated MCP server (more parts, same control; revisit when other agents or teams need the same door). Direct agent DB access (access in a prompt, rejected).
- **Owner:** FDE. **Revisit:** Week 4, or when a second consumer appears.

## D-009 · 2026-11-23 · `policy_status` is display-only; dates decide coverage

- **Decision:** In-force is `policy_start <= incident_date <= policy_end` in code. The status label is never used in a decision.
- **Why:** CLM-2024-2822 is "Active" but the loss is 3 days after `policy_end`. The label is stale data.
- **Owner:** FDE. **Revisit:** if the client confirms the end date is exclusive.

## D-010 · 2026-11-23 · Idempotency key from the evidence, not a counter

- **Decision:** `key = sha256(claim_id | input_digest | pipeline_version)`. New evidence gives a new version and supersedes the old draft. A human decision is never overwritten. (Refines D-004.)
- **Why:** A retry can't create a duplicate. A late OCR document still produces a fresh draft.
- **Alternatives:** `claim_id + version counter` (a retry after a timeout can bump the counter and duplicate).
- **Owner:** FDE + CMS owner. **Revisit:** Week 4.

## D-011 · 2026-11-23 · Minimise data at the boundary

- **Decision:** Policyholder names are dropped when the policy is loaded and never reach a prompt, log or the model provider.
- **Why:** No decision needs them. Data we never hold can't leak (security questionnaire item 2).
- **Owner:** FDE + CISO.
