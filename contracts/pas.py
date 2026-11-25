"""Policy Administration System (PAS) contract. READ ONLY.

Data minimisation: the PAS stores the policyholder's name. The co-pilot does not need it to
decide coverage, so holder_first / holder_last are dropped at the access layer and never reach
a prompt, a log or the model provider. (Security questionnaire item 2.)

Two reads:
  GetPolicy      -> structured policy terms. Dates and money come from here and are used
                    by code only (in-force check, deductible, limits).
  SearchClauses  -> the policy clause corpus for retrieval. Coverage judgments may cite ONLY
                    clause_ids returned by this call (enforced in cms.Recommendation).
"""
from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import Field, model_validator

from .common import ClauseId, PolicyId, RequestMeta, Strict, Usd, Vin


class CoverageType(str, Enum):
    FULL = "Full Coverage"
    LIABILITY_ONLY = "Liability Only"


class PolicyStatus(str, Enum):
    ACTIVE = "Active"
    EXPIRED = "Expired"


class GetPolicyRequest(Strict):
    meta: RequestMeta
    policy_id: PolicyId


class LiabilityLimit(Strict):
    per_person_usd: Usd
    per_accident_usd: Usd


class PolicyRecord(Strict):
    policy_id: PolicyId
    vehicle_vin: Vin
    vehicle_acv_usd: Usd
    coverage_type: CoverageType
    collision_coverage: bool
    comprehensive_coverage: bool
    collision_deductible_usd: Usd | None = Field(description="None when not covered (CSV 'N/A')")
    comprehensive_deductible_usd: Usd | None
    liability_limit: LiabilityLimit
    medpay_limit_usd: Usd
    policy_status: PolicyStatus = Field(
        description="Display field only. NEVER used to decide coverage: code uses the dates "
        "(claim CLM-2024-2822 says Active but the loss is after policy_end)."
    )
    policy_start: date
    policy_end: date = Field(description="Inclusive (working assumption, charter open question 3)")
    policy_form_id: str = Field(default="TXA-PAP-2023", description="Which clause set applies")

    @model_validator(mode="after")
    def _dates(self) -> "PolicyRecord":
        if self.policy_end < self.policy_start:
            raise ValueError("policy_end before policy_start")
        if self.collision_coverage != (self.collision_deductible_usd is not None):
            raise ValueError("collision deductible must exist iff collision is covered")
        if self.comprehensive_coverage != (self.comprehensive_deductible_usd is not None):
            raise ValueError("comprehensive deductible must exist iff comprehensive is covered")
        return self

    def in_force_on(self, loss_date: date) -> bool:
        """Deterministic in-force check. Lives in code, never in a prompt."""
        return self.policy_start <= loss_date <= self.policy_end


class GetPolicyResponse(Strict):
    policy: PolicyRecord
    etag: str


class SearchClausesRequest(Strict):
    meta: RequestMeta
    policy_form_id: str
    query: str = Field(min_length=3, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)


class ClauseKind(str, Enum):
    INSURING = "insuring"
    EXCLUSION = "exclusion"
    CONDITION = "condition"
    DEFINITION = "definition"


class ClauseHit(Strict):
    clause_id: ClauseId
    policy_form_id: str
    kind: ClauseKind
    title: str
    text: str
    score: float = Field(ge=0)


class SearchClausesResponse(Strict):
    hits: tuple[ClauseHit, ...]
    index_version: str = Field(description="Corpus version; part of input_digest")
