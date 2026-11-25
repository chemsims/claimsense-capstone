# Synthetic data shapes: claims, policies, documents

All data is synthetic. Course files are in [`data/course/`](../data/course) and unchanged. Our additions are in [`data/synthetic/`](../data/synthetic). Each shape is a typed model in [`contracts/`](../contracts) with a JSON Schema in [`data/schemas/`](../data/schemas). `pytest` loads every course row through these models, so a shape that doesn't match the data fails CI.

## Claims (`claims.csv` → `cms.ClaimRecord`), 20 rows

| Field | Type | Notes |
|---|---|---|
| `claim_id` | `CLM-YYYY-NNNN` | primary key |
| `policy_id` | `POL-AAA-NNNNN` | join to policy |
| `vehicle.vin` / `year` / `make` / `model` | VIN (17 chars), int, str, str | VIN cross-checked against the policy in code |
| `vehicle.acv_usd` | Decimal | actual cash value; total-loss ratio denominator |
| `incident_date` | date | in-force check (code) |
| `incident_type`, `incident_description`, `damage_description` | str | **untrusted** free text, read by the model |
| `repair_estimate_usd` | Decimal | money (code) |
| `injuries_reported`, `police_report_filed` | bool | CSV `Yes`/`No` |
| `assigned_adjuster` | user id | entitlement source |
| `prior_claims_12mo` | int ≥ 0 | |
| `fraud_risk_score` | Decimal 0–1 | existing score; an input, not a verdict |
| `claim_status` | enum: Pending Review, Under Investigation, Escalated, Approved | the co-pilot never writes this |
| `created_at` | UTC timestamp | |

## Policies (`policies.csv` → `pas.PolicyRecord`), 15 rows

| Field | Type | Notes |
|---|---|---|
| `policy_id` | `POL-AAA-NNNNN` | |
| `holder_first`, `holder_last` | — | **dropped at load.** Not needed for any decision |
| `vehicle_vin`, `vehicle_acv_usd` | VIN, Decimal | |
| `coverage_type` | enum: Full Coverage, Liability Only | |
| `collision_coverage`, `comprehensive_coverage` | bool | |
| `collision_deductible_usd`, `comprehensive_deductible_usd` | Decimal or `None` | CSV `N/A` → `None`; must be present iff covered |
| `liability_limit` | `{per_person_usd, per_accident_usd}` | parsed from `300000/100000` |
| `medpay_limit_usd` | Decimal | |
| `policy_status` | enum: Active, Expired | **display only.** CLM-2024-2822 says Active but the loss is 3 days after `policy_end` |
| `policy_start`, `policy_end` | date | end date inclusive (assumption, charter Q3) |
| `policy_form_id` | str, default `TXA-PAP-2023` | *added:* selects the clause set |

## Documents (`documents.csv` → `docstore.DocumentMeta`), 74 rows

| Field | Type | Notes |
|---|---|---|
| `document_id` | `DOC-NNNNN` | |
| `claim_id` | `CLM-YYYY-NNNN` | join; checked on every text fetch |
| `document_type` | enum (7): FNOL_FORM, DAMAGE_PHOTOS, REPAIR_ESTIMATE, WITNESS_STATEMENT, MEDICAL_REPORT, RENTAL_RECEIPT, POLICE_REPORT | |
| `description`, `upload_date`, `page_count`, `uploaded_by` | str, date, int, user id | |
| `ocr_status` | enum: Completed (64), Pending (10) | Pending = missing evidence → no APPROVE |

## What the course data is missing, and what we added

The course CSVs have no document text, no policy wording and no user list. The co-pilot needs all three, so we added synthetic versions with the same keys.

| File | Shape | Rows | Why |
|---|---|---|---|
| `document_texts.jsonl` | `docstore.DocumentText`: `document_id`, `claim_id`, `ocr_status`, `text` (or null), `sha256`, `injection_flags` | 6 samples now; one per completed document in Week 3 | The model reads narratives. Samples include the 1873 contradiction (FNOL says alone, EMS says a passenger left) and a **prompt injection** in DOC-00066. |
| `policy_clauses.jsonl` | `pas.ClauseHit`: `clause_id`, `policy_form_id`, `kind`, `title`, `text` | 14 | Retrieval corpus. Coverage must cite these IDs. |
| `users.csv` | `user_id`, `display_name`, `roles`, `notes` | 8 | Two-user access test (M4) and refusal cases. `mallory` is assigned to nothing. |

## Joins (done in code)

```
claim.policy_id ──► policy.policy_id      (and claim.vehicle.vin == policy.vehicle_vin)
claim.claim_id  ◄── document.claim_id     (74 docs → 20 claims)
document.document_id ──► document_text.document_id
policy.policy_form_id ──► clause.policy_form_id
claim.assigned_adjuster ──► users.user_id (entitlement)
```

Verified by `tests/test_contracts.py::test_joins_resolve`: every claim's policy exists and every VIN matches.
