# Success Criteria (Milestone 1)

Format for each: **[metric] [threshold] [population]**. If we cannot write the test, it is not a criterion. These lines become the Week 2 SoW acceptance criteria and the Week 3–5 CI evaluation gate.

| # | Area | Said in the room | Eval-anchored criterion | How it is measured |
|---|---|---|---|---|
| 1 | **Decision accuracy** | "Get the first decision right" | **≥ 90%** of co-pilot first decisions match the senior-adjuster label, **and** no single outcome class (APPROVE / DENY / FLAG / ROUTE_SIU) below **80%** recall — on the **150-case golden set** (Week 5), seeded by the 20 cases in `evals/` | Eval suite run in CI on the submitted commit; per-class confusion matrix |
| 2 | **Pipeline latency** | "Minutes, not hours" | **p95 ≤ 60 seconds** from request to returned decision + reasons + citations, **p50 ≤ 20 seconds** — over **every case in the eval suite** run against the deployed AWS stack | Timestamps on each request; p50/p95 on the CloudWatch dashboard |
| 3 | **Adjuster confirmation rate** | "Adjusters should trust it" | **≥ 80%** of co-pilot outcomes confirmed **without change** by a licensed adjuster — over **≥ 100 synthetic claims** reviewed in user acceptance testing. Also: **100%** of outcomes carry an adjuster confirmation before any status change | Confirm / override logged per claim in the audit trail; overrides tagged with a reason |
| 4 | **Fraud routing accuracy** | "Catch the bad ones without flooding SIU" | **Recall ≥ 95%** on fraud-labeled cases (≥ 95% of them reach ROUTE_SIU), **precision ≥ 70%** (≤ 30% of SIU referrals are clean claims), and **0** fraud-labeled cases returned as APPROVE — on the **golden set's fraud and adversarial families** | Eval suite; SIU-labeled subset reported separately |

## Hard guards (pass/fail, not averages)

- **0** responses with claim data returned to a user not entitled to that claim.
- **0** payouts, deductibles, dates or entitlement decisions produced by the model (code only, checked in tests).
- **100%** of DENY outcomes cite at least one retrieved policy clause ID.

## What we still need from the client

Baselines are **unknown** today. The thresholds above are starting targets; we will reset them against the client's real numbers once we have:
- current minutes per first pass (median and 90th percentile);
- current inter-adjuster agreement on the same file;
- current SIU referral hit rate.
