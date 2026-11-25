"""Shared types for every ClaimSense contract.

Rules that apply to all three client systems:
- IDs are validated by pattern at the boundary. A malformed ID never reaches a client system.
- Money is Decimal (never float) and always US dollars with 2 decimal places.
- Dates are ISO dates (no time); timestamps are UTC.
- Every response the co-pilot returns marks each value as CODE (computed deterministically)
  or MODEL (a judgment by the model, which must carry citations).
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

ClaimId = Annotated[str, StringConstraints(pattern=r"^CLM-\d{4}-\d{4}$")]
PolicyId = Annotated[str, StringConstraints(pattern=r"^POL-[A-Z]{3}-\d{5}$")]
DocumentId = Annotated[str, StringConstraints(pattern=r"^DOC-\d{5}$")]
ClauseId = Annotated[str, StringConstraints(pattern=r"^[A-Z]{2,5}-\d{1,2}(\.\d{1,2})?$")]
Vin = Annotated[str, StringConstraints(pattern=r"^[A-HJ-NPR-Z0-9]{17}$")]
UserId = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_.-]{1,31}$")]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
Usd = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)]


class Strict(BaseModel):
    """Base for every contract model: unknown fields are rejected, values are immutable."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class Role(str, Enum):
    ADJUSTER = "adjuster"
    SENIOR_ADJUSTER = "senior_adjuster"
    SIU_INVESTIGATOR = "siu_investigator"
    CLAIMS_SUPERVISOR = "claims_supervisor"


class ActingUser(Strict):
    """Identity of the human the call is made on behalf of (OAuth2 on-behalf-of).

    Comes from the verified token, never from the request body or the model.
    """

    user_id: UserId
    roles: frozenset[Role]
    token_subject: str = Field(min_length=1, description="'sub' claim of the verified token")


class Provenance(str, Enum):
    CODE = "code"    # deterministic: identity, access, dates, money, joins
    MODEL = "model"  # judgment: clause interpretation, narrative consistency, drafting


class ErrorCode(str, Enum):
    NOT_FOUND = "not_found"
    FORBIDDEN = "forbidden"              # entitlement check failed (no data returned)
    INVALID_REQUEST = "invalid_request"
    IDEMPOTENCY_CONFLICT = "idempotency_conflict"
    ALREADY_DECIDED = "already_decided"  # adjuster already confirmed/overrode; no write
    UPSTREAM_UNAVAILABLE = "upstream_unavailable"  # retryable
    RATE_LIMITED = "rate_limited"        # retryable after retry_after_s


class ErrorResponse(Strict):
    code: ErrorCode
    message: str
    retryable: bool
    retry_after_s: int | None = None
    request_id: str


class RequestMeta(Strict):
    """Carried on every call to a client system, for tracing and the audit record."""

    request_id: str = Field(min_length=8, description="UUID4 generated per call")
    acting_user: ActingUser
    sent_at: datetime
