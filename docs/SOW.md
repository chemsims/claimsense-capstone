# Statement of Work: ClaimSense claims adjudication co-pilot (pilot)

**Vendor:** Satyugjit Virk, forward deployed engineer · **Client:** motor insurer (VP of Claims, approver) · **Version:** v1.0, 2026-11-23

## 1. Background and objectives
One adjuster per claim works by hand across three unconnected systems: claims management (CMS), policy administration (PAS) and the document store. Throughput is limited by one person, decisions vary between adjusters, reasoning isn't recorded, and fraud referral is a score threshold, not a reading of the file. **Objective:** an adjuster's first pass in minutes, with recorded reasoning and a licensed adjuster accountable for every outcome.

## 2. Scope and deliverables
A co-pilot that, given a claim, returns one of APPROVE, DENY, FLAG (to a senior adjuster) or ROUTE_SIU (to the fraud unit), with plain-language reasoning and citations to the clauses, documents and fields relied on. It **refuses** users not entitled to the claim and returns no data. Identity, access, policy dates and money are computed in code. Clause interpretation and narrative consistency are model judgments, and every judgment is cited.

| Deliverable | Milestone |
|---|---|
| Charter, RACI, success criteria, decisions, 20 seed evals | M1 ✓ |
| This SoW, architecture, pricing, risk register, typed contracts, data shapes, AWS environment | M2 |
| Agents (OpenAI Agents SDK, strict types), clause retrieval with citations, containers, CI eval gate | M3 |
| Access layer: auth on every route, entitlement before any agent, two-user test, audit of every call | M4 |
| 150-case eval suite with adversarial families, dashboard + alarm, incident drill, runbook, demo, handover pack | M5 |

## 3. Acceptance criteria (= Milestone 1 success criteria)
Measured on a **held-out** 150-case synthetic set whose labels the Claims Supervisor confirms. The system is not tuned on these cases.

| # | Criterion | Threshold |
|---|---|---|
| AC1 | Decision accuracy (matches confirmed label) | ≥ 90% overall |
| AC2 | Pipeline latency, request to decision | 95% of claims ≤ 60 s |
| AC3 | Adjuster confirmation rate (draft confirmed without change, in the Week 5 adjuster review) | ≥ 80% |
| AC4 | Fraud routing | ≥ 95% of fraud-labelled cases routed to SIU; **0** approved |
| AC5 | Entitlement | 100% of non-entitled requests refused, zero claim fields returned, refusal audited |
| AC6 | Attribution | 100% of responses label each value as code or model; every coverage citation is a retrieved clause |

AC1–AC4 are reset once the client provides today's baseline (charter Q1).

## 4. Out of scope
Paying claims, sending letters or changing claim status. Third-party liability, subrogation and bodily-injury valuation (injury claims are FLAGGED). Any real or personal data. Changes to the existing fraud-score model. Production rollout.

## 5. Timeline (five weeks)
| Week | Milestone | Sign-off |
|---|---|---|
| 1 · Nov 15–21 | M1 Discovery and scoping ✓ | VP Claims |
| 2 · Nov 22–Dec 5 | M2 SoW, pricing, architecture, cloud environment (review Dec 3; checkpoint before Week 3) | VP Claims + CISO (data annex) |
| 3 · from Dec 6 | M3 Production agents under CI | Head of Claims Ops |
| 4 (date TBC) | M4 Integration and access control | CISO |
| 5 (date TBC) | M5 Evaluation, observability, handover | VP Claims |

## 6. Pricing and payment
Fixed floor **$151,000** plus **$7,500 for each of AC1–AC4 met** (maximum $181,000). Model and AWS run costs are passed through at cost (about $0.003 per claim). Payment: 30% at M2 sign-off, 40% at M4 acceptance, 30% plus bonus at M5 acceptance. Assumptions are in `PRICING.md`.

## 7. Intellectual property
**Client owns**, on final payment: agents, prompts, eval cases and configuration built for it, plus the clause index, embeddings and any data derived from its material (deleted from vendor systems at exit). **Vendor keeps** its pre-existing tools and libraries; the client gets a perpetual licence to use them in this system. No model fine-tuning in the pilot.

## 8. Data handling (data annex)
| Data | Where | Retention | Deletion | Subprocessors |
|---|---|---|---|---|
| Synthetic claims, policies, documents | Client-designated AWS account, us-west-2, encrypted (S3, KMS) | Pilot + 30 days | Vendor deletes, client verifies via inventory | AWS |
| Prompts and model outputs | OpenAI API | Per OpenAI API data policy; not used for training | Not stored by vendor beyond logs | OpenAI |
| Audit log | DynamoDB, append-only | 1 year, or exported to client at exit | Client decides | AWS |

**Synthetic data only;** production data needs a new SoW after the CISO's controls review. Policyholder names are never ingested. Secrets live in AWS Secrets Manager. Agents act under the adjuster's identity, access is enforced in code, and every call is audited.

## 9. Change control
Written request; vendor sizes it (days, price) within 2 business days; no work starts until the VP of Claims approves. Changes to acceptance criteria also need the Claims Supervisor.

## 10. Assumptions and dependencies
By end of Week 2 the client confirms: AWS sandbox, decision labels (flag = senior review, route = SIU), total-loss threshold (assumed 75% of ACV), inclusive policy end date (assumed), and two adjusters for weekly feedback. Each week of delay moves later milestones a week.

## 11. Exit
Vendor hands over repository, runbook and audit export; revokes its access within 24 hours; deletes client-derived data within 30 days and confirms in writing.

**Signatures** · Vendor: ______________ · Client (VP of Claims): ______________
