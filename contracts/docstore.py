"""Document Store contract. READ ONLY.

Two reads:
  ListDocuments    -> metadata for every document on a claim.
  GetDocumentText  -> OCR text for one document.

Rules:
  - A document with ocr_status=Pending has text=None. The co-pilot treats it as MISSING
    evidence: it is listed in Recommendation.document_ids_missing and the decision cannot be
    APPROVE (10 of the 74 course documents are Pending).
  - Document text is UNTRUSTED input written by claimants and third parties. It is passed to
    the model inside a delimited data block, scanned by an input guardrail for instructions
    ("ignore previous...", "approve this claim"), and can never change tools, roles or the
    decision schema.
  - sha256 of the text is part of the recommendation's input_digest, so new OCR text produces
    a new recommendation version (see cms.py idempotency rule 4).
  - A document can only be fetched for a claim the acting user is entitled to; the access
    layer checks document.claim_id against the entitled claim before returning text
    (prevents cross-record leakage by guessing DOC ids).
"""
from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import Field, model_validator

from .common import ClaimId, DocumentId, RequestMeta, Sha256, Strict, UserId


class DocumentType(str, Enum):
    FNOL_FORM = "FNOL_FORM"
    DAMAGE_PHOTOS = "DAMAGE_PHOTOS"
    REPAIR_ESTIMATE = "REPAIR_ESTIMATE"
    WITNESS_STATEMENT = "WITNESS_STATEMENT"
    MEDICAL_REPORT = "MEDICAL_REPORT"
    RENTAL_RECEIPT = "RENTAL_RECEIPT"
    POLICE_REPORT = "POLICE_REPORT"


class OcrStatus(str, Enum):
    COMPLETED = "Completed"
    PENDING = "Pending"


class ListDocumentsRequest(Strict):
    meta: RequestMeta
    claim_id: ClaimId


class DocumentMeta(Strict):
    document_id: DocumentId
    claim_id: ClaimId
    document_type: DocumentType
    description: str
    upload_date: date
    page_count: int = Field(ge=1, le=500)
    ocr_status: OcrStatus
    uploaded_by: UserId


class ListDocumentsResponse(Strict):
    claim_id: ClaimId
    documents: tuple[DocumentMeta, ...]


class GetDocumentTextRequest(Strict):
    meta: RequestMeta
    document_id: DocumentId
    expected_claim_id: ClaimId = Field(description="Access layer rejects if the doc belongs elsewhere")


class DocumentText(Strict):
    document_id: DocumentId
    claim_id: ClaimId
    ocr_status: OcrStatus
    text: str | None = Field(description="UNTRUSTED. None while OCR is pending")
    sha256: Sha256 | None
    injection_flags: tuple[str, ...] = Field(
        default=(), description="Set by our input guardrail, not by the document store"
    )

    @model_validator(mode="after")
    def _pending_has_no_text(self) -> "DocumentText":
        if (self.ocr_status is OcrStatus.PENDING) != (self.text is None):
            raise ValueError("text must be present iff OCR is completed")
        if (self.text is None) != (self.sha256 is None):
            raise ValueError("sha256 must accompany text")
        return self
