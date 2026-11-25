# Typed contracts for the three client systems

Code: [`contracts/`](../contracts) (Pydantic v2, `extra="forbid"`, frozen). JSON Schema: [`data/schemas/`](../data/schemas). Tests: [`tests/test_contracts.py`](../tests/test_contracts.py), run against the course CSVs.

Every call carries `RequestMeta`: a `request_id`, the **acting user** taken from the verified token (OAuth2 on-behalf-of), and a timestamp. The model never supplies identity.

## Summary

| System | Operation | Input | Output | R/W | Who calls it |
|---|---|---|---|---|---|
| Claims Management (CMS) | `GetAssignment` | `claim_id` | `assigned_adjuster`, `escalation_roles` | R | Access layer, **before any agent runs** |
| CMS | `GetClaim` | `claim_id` | `ClaimRecord` + `etag` | R | Access layer, after entitlement passes |
| CMS | `PutRecommendation` | `idempotency_key`, `Recommendation` | `recommendation_id`, `version`, `state`, `outcome` | **W** | Access layer, after schema checks |
| Policy Admin (PAS) | `GetPolicy` | `policy_id` | `PolicyRecord` + `etag` (holder name removed) | R | Access layer |
| PAS | `SearchClauses` | `policy_form_id`, `query`, `top_k` | `ClauseHit[]` + `index_version` | R | Coverage agent, through the access layer |
| Document Store | `ListDocuments` | `claim_id` | `DocumentMeta[]` | R | Access layer |
| Document Store | `GetDocumentText` | `document_id`, `expected_claim_id` | `DocumentText` (text or `None` if OCR pending) | R | Access layer |
| Audit log (ours) | `PutAudit` | `AuditRecord` | stored record | **W** | Access layer, every call |

Agents never call a client system directly. Every call goes through one access layer that checks entitlement, strips fields the model does not need, and writes the audit record.

## Errors (all systems)

`ErrorResponse{code, message, retryable, retry_after_s, request_id}`

| Code | Retry? | Meaning |
|---|---|---|
| `forbidden` | No | Not entitled. **No claim data in the body.** Audited as `denied`. |
| `not_found` | No | Unknown ID. Same body shape as `forbidden` to a non-entitled user, so IDs can't be probed. |
| `invalid_request` | No | Failed schema validation at our boundary. |
| `idempotency_conflict` | No | Same key, different body. A bug. Pages on-call. |
| `already_decided` | No | Adjuster already confirmed or overrode the draft. Co-pilot stops. |
| `upstream_unavailable` / `rate_limited` | Yes | Max 3 retries, exponential backoff with jitter, **same idempotency key**. |

## Write operations and idempotency

The co-pilot makes **one** write to a client system: a draft recommendation in the CMS. It never changes `claim_status`, never pays and never closes a claim.

**`CMS.PutRecommendation`**

1. `idempotency_key = sha256(claim_id | input_digest | pipeline_version)`, computed in code. `input_digest` hashes the claim `etag`, policy `etag`, clause `index_version` and each document's text hash.
2. Same key and same body: returns `200` with the **original** `recommendation_id` and `outcome=REPLAYED`. No new row.
3. Same key, different body: `409 idempotency_conflict`. Nothing written.
4. New evidence (say a pending document finishes OCR) gives a new digest and a new key. The new draft gets `version = previous + 1`, and the old one becomes `SUPERSEDED`. At most one `ACTIVE` draft per claim.
5. If the adjuster has already `CONFIRMED` or `OVERRIDDEN` the draft: `409 already_decided`. The co-pilot never overwrites a human decision.
6. Keys are kept 30 days.

**`Audit.PutAudit`**: the primary key is `request_id`, written with a conditional put (`attribute_not_exists`). A retry is a no-op. Records are never updated or deleted. If the audit write fails, the request fails closed and no claim data is returned.

## Guards built into the types (so they can't be skipped)

| Guard | Where |
|---|---|
| A `Fact` (date, money, entitlement) can only have provenance `code` | `cms.Fact` |
| A `Judgment` must have at least one citation | `cms.Judgment` |
| Coverage may cite only clause IDs actually returned by `SearchClauses` | `cms.Recommendation` |
| `APPROVE` is impossible when any document is missing or OCR is pending | `cms.Recommendation` |
| `requires_adjuster_confirmation` cannot be false | `cms.Recommendation` |
| `policy_status` is display-only; in-force uses dates (`in_force_on`) | `pas.PolicyRecord` |
| Deductible exists only if that coverage exists | `pas.PolicyRecord` |
| Pending OCR has no text; text always has a hash | `docstore.DocumentText` |
| Document fetch is rejected if it belongs to another claim | `docstore.GetDocumentTextRequest.expected_claim_id` |
| Document and claim free text are labelled UNTRUSTED | field descriptions; input guardrail in Week 3 |
