"""Audit log contract (our own store, DynamoDB table claimsense-audit). APPEND ONLY.

Not a client system, but it is a write, so it has idempotency rules too:
  1. Primary key = request_id (UUID4 from RequestMeta). One request -> one audit record.
  2. Write is a conditional put (attribute_not_exists(request_id)). A retry of the same request
     is a no-op that returns the stored record. Records are never updated or deleted.
  3. Every call is recorded, granted OR denied, with user, action and resource (brief M4.5).
  4. The record is written BEFORE the response leaves the service. If the audit write fails,
     the request fails closed (no claim data is returned).
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from .common import RequestMeta, Strict, UserId


class AuditAction(str, Enum):
    GET_DECISION = "get_decision"
    GET_CLAIM = "cms.get_claim"
    GET_ASSIGNMENT = "cms.get_assignment"
    PUT_RECOMMENDATION = "cms.put_recommendation"
    GET_POLICY = "pas.get_policy"
    SEARCH_CLAUSES = "pas.search_clauses"
    LIST_DOCUMENTS = "docstore.list_documents"
    GET_DOCUMENT_TEXT = "docstore.get_document_text"


class AccessResult(str, Enum):
    GRANTED = "granted"
    DENIED = "denied"
    ERROR = "error"


class AuditRecord(Strict):
    request_id: str
    at: datetime
    user_id: UserId
    action: AuditAction
    resource: str  # e.g. "claim:CLM-2024-1873", "document:DOC-00004"
    result: AccessResult
    reason: str | None = None  # e.g. "not assigned adjuster"
    pipeline_version: str


class PutAuditRequest(Strict):
    meta: RequestMeta
    record: AuditRecord
