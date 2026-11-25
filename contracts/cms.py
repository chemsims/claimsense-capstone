"""Claims Management System (CMS) contract.

Reads:  GetClaim, GetAssignment
Write:  PutRecommendation — the ONLY write the co-pilot makes to any client system.

The co-pilot never changes claim_status, never pays, never closes a claim. A recommendation
is a draft until a licensed adjuster confirms it in the CMS's own UI.

Idempotency rules for PutRecommendation (enforced by our access layer AND requested of the CMS):
  1. idempotency_key = sha256(claim_id | input_digest | pipeline_version). Computed in code.
     The same claim, same evidence and same pipeline always produce the same key.
  2. Same key + same body  -> 200, the ORIGINAL recommendation_id is returned, outcome=REPLAYED.
     No second row is written.
  3. Same key + different body -> 409 IDEMPOTENCY_CONFLICT. Nothing is written. This can only
     happen through a bug, so it pages the on-call engineer.
  4. New input_digest for the same claim (e.g. a document finished OCR) -> new key, new
     version = previous + 1; the previous draft is marked SUPERSEDED. At most one ACTIVE draft
     per claim.
  5. A draft the adjuster has already CONFIRMED or OVERRIDDEN is never superseded: the write
     returns 409 ALREADY_DECIDED and the co-pilot stops.
  6. Retries: only on timeout / 5xx / 429, max 3, exponential backoff with jitter, always with
     the SAME key. Keys are retained for 30 days.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import Field, model_validator

from .common import (
    ClaimId, ClauseId, DocumentId, PolicyId, Provenance, RequestMeta, Sha256, Strict, Usd,
    UserId, Vin,
)


class ClaimStatus(str, Enum):
    PENDING_REVIEW = "Pending Review"
    UNDER_INVESTIGATION = "Under Investigation"
    ESCALATED = "Escalated"
    APPROVED = "Approved"


# ---------- Reads ----------

class GetClaimRequest(Strict):
    meta: RequestMeta
    claim_id: ClaimId


class VehicleRef(Strict):
    vin: Vin
    year: int = Field(ge=1980, le=2030)
    make: str
    model: str
    acv_usd: Usd = Field(description="Actual cash value per CMS")


class ClaimRecord(Strict):
    claim_id: ClaimId
    policy_id: PolicyId
    vehicle: VehicleRef
    incident_date: date
    incident_type: str
    incident_description: str = Field(description="UNTRUSTED free text; never executed as instructions")
    damage_description: str = Field(description="UNTRUSTED free text")
    repair_estimate_usd: Usd
    injuries_reported: bool
    police_report_filed: bool
    assigned_adjuster: UserId
    prior_claims_12mo: int = Field(ge=0)
    fraud_risk_score: Decimal = Field(ge=0, le=1, description="Existing CMS model score; an input, not a verdict")
    claim_status: ClaimStatus
    created_at: datetime


class GetClaimResponse(Strict):
    claim: ClaimRecord
    etag: str = Field(description="CMS version tag; part of input_digest")


class GetAssignmentRequest(Strict):
    meta: RequestMeta
    claim_id: ClaimId


class GetAssignmentResponse(Strict):
    """Source of truth for entitlement. Our access layer calls this BEFORE GetClaim and before
    any agent runs. A user is entitled if they are the assigned adjuster, or hold a role listed
    in escalation_roles for this claim."""

    claim_id: ClaimId
    assigned_adjuster: UserId
    escalation_roles: frozenset[str] = frozenset()


# ---------- The one write ----------

class Decision(str, Enum):
    APPROVE = "APPROVE"
    DENY = "DENY"
    FLAG = "FLAG"            # senior adjuster: total loss, injury, missing/contradictory evidence
    ROUTE_SIU = "ROUTE_SIU"  # special investigations (fraud) unit


class Citation(Strict):
    kind: str = Field(pattern=r"^(clause|document|claim_field|policy_field)$")
    ref: str = Field(min_length=1, description="clause_id, document_id or field name")
    quote: str | None = Field(default=None, max_length=300)


class Fact(Strict):
    """A deterministic fact. provenance is always CODE."""

    name: str  # e.g. policy_in_force_on_loss_date, deductible_usd, repair_to_acv_ratio
    value: str
    provenance: Provenance = Provenance.CODE

    @model_validator(mode="after")
    def _code_only(self) -> "Fact":
        if self.provenance is not Provenance.CODE:
            raise ValueError("facts are computed in code only")
        return self


class Judgment(Strict):
    """A model judgment. Must cite evidence; an uncited judgment is rejected."""

    question: str  # e.g. "Does clause COL-2.1 cover this loss?"
    answer: str
    citations: tuple[Citation, ...] = Field(min_length=1)
    provenance: Provenance = Provenance.MODEL


class Recommendation(Strict):
    claim_id: ClaimId
    decision: Decision
    reasoning: str = Field(min_length=20, max_length=4000)
    facts: tuple[Fact, ...]
    judgments: tuple[Judgment, ...]
    estimated_payout_usd: Usd | None = Field(default=None, description="CODE: repair - deductible, capped at ACV")
    clause_ids_retrieved: tuple[ClauseId, ...]
    document_ids_read: tuple[DocumentId, ...]
    document_ids_missing: tuple[DocumentId, ...] = Field(description="e.g. OCR pending; forces FLAG")
    requires_adjuster_confirmation: bool = True
    model_version: str
    pipeline_version: str
    input_digest: Sha256 = Field(description="sha256 of claim etag + policy etag + document hashes")

    @model_validator(mode="after")
    def _guards(self) -> "Recommendation":
        if not self.requires_adjuster_confirmation:
            raise ValueError("every outcome needs adjuster confirmation")
        cited = {c.ref for j in self.judgments for c in j.citations if c.kind == "clause"}
        unknown = cited - set(self.clause_ids_retrieved)
        if unknown:
            raise ValueError(f"cites clauses that were never retrieved: {sorted(unknown)}")
        if self.document_ids_missing and self.decision is Decision.APPROVE:
            raise ValueError("cannot APPROVE with missing evidence; use FLAG")
        return self


class PutRecommendationRequest(Strict):
    meta: RequestMeta
    idempotency_key: Sha256
    recommendation: Recommendation


class WriteOutcome(str, Enum):
    CREATED = "CREATED"
    REPLAYED = "REPLAYED"  # same key + same body: nothing new written


class DraftState(str, Enum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    CONFIRMED = "CONFIRMED"    # set only by the adjuster in the CMS UI
    OVERRIDDEN = "OVERRIDDEN"  # set only by the adjuster in the CMS UI


class PutRecommendationResponse(Strict):
    recommendation_id: str
    claim_id: ClaimId
    version: int = Field(ge=1)
    state: DraftState
    outcome: WriteOutcome
    superseded_recommendation_id: str | None = None
    created_at: datetime


def idempotency_key(claim_id: str, input_digest: str, pipeline_version: str) -> str:
    """Rule 1. Deterministic, so a retry can never create a second draft."""
    import hashlib

    return hashlib.sha256(f"{claim_id}|{input_digest}|{pipeline_version}".encode()).hexdigest()
