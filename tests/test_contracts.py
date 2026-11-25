"""Contracts are tested against the real course data, plus the rules that matter most:
idempotency, no uncited judgments, no approve with missing evidence, status-field trap."""
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from contracts.cms import (
    Citation, Decision, Fact, Judgment, PutRecommendationRequest, Recommendation, idempotency_key,
)
from contracts.common import ActingUser, Provenance, RequestMeta, Role
from contracts.docstore import DocumentText, OcrStatus
from contracts.loaders import (
    load_claims, load_clauses, load_document_texts, load_documents, load_policies,
)

CLAIMS, POLICIES, DOCS = load_claims(), load_policies(), load_documents()
DIGEST = "a" * 64


def test_course_data_loads_completely():
    assert (len(CLAIMS), len(POLICIES), len(DOCS)) == (20, 15, 74)
    assert len(load_clauses()) == 14 and len(load_document_texts()) == 6


def test_joins_resolve():
    for c in CLAIMS.values():
        p = POLICIES[c.policy_id]                    # claim -> policy
        assert p.vehicle_vin == c.vehicle.vin        # VIN cross-check
    assert {d.claim_id for d in DOCS.values()} <= set(CLAIMS)  # doc -> claim


def test_pii_is_dropped():
    assert "holder_first" not in POLICIES["POL-TXA-88000"].model_dump()


def test_status_field_trap_2822():
    c = CLAIMS["CLM-2024-2822"]
    p = POLICIES[c.policy_id]
    assert p.policy_status.value == "Active"
    assert not p.in_force_on(c.incident_date)        # dates win, not the status label


def test_pending_ocr_counted():
    assert sum(d.ocr_status is OcrStatus.PENDING for d in DOCS.values()) == 10


def _rec(**over):
    base = dict(
        claim_id="CLM-2024-1800", decision=Decision.APPROVE,
        reasoning="Third party admitted fault; collision covered under COL-1.",
        facts=(Fact(name="policy_in_force_on_loss_date", value="true"),),
        judgments=(Judgment(question="Is the loss covered?", answer="Yes, collision.",
                            citations=(Citation(kind="clause", ref="COL-1"),)),),
        estimated_payout_usd=Decimal("2700.00"),
        clause_ids_retrieved=("COL-1", "DEF-1"),
        document_ids_read=("DOC-00001",), document_ids_missing=(),
        model_version="gpt-4o-mini-2024-07-18", pipeline_version="0.1.0", input_digest=DIGEST,
    )
    base.update(over)
    return Recommendation(**base)


def test_valid_recommendation():
    assert _rec().decision is Decision.APPROVE


def test_uncited_judgment_rejected():
    with pytest.raises(ValidationError):
        Judgment(question="q", answer="a", citations=())


def test_cannot_cite_unretrieved_clause():
    with pytest.raises(ValidationError, match="never retrieved"):
        _rec(clause_ids_retrieved=("DEF-1",))


def test_cannot_approve_with_missing_evidence():
    with pytest.raises(ValidationError, match="missing evidence"):
        _rec(document_ids_missing=("DOC-00007",))
    assert _rec(decision=Decision.FLAG, document_ids_missing=("DOC-00007",))


def test_no_auto_decision():
    with pytest.raises(ValidationError):
        _rec(requires_adjuster_confirmation=False)


def test_facts_are_code_only():
    with pytest.raises(ValidationError):
        Fact(name="deductible_usd", value="500", provenance=Provenance.MODEL)


def test_idempotency_key_is_deterministic_and_input_sensitive():
    k1 = idempotency_key("CLM-2024-1873", DIGEST, "0.1.0")
    assert k1 == idempotency_key("CLM-2024-1873", DIGEST, "0.1.0")      # retry -> same key
    assert k1 != idempotency_key("CLM-2024-1873", "b" * 64, "0.1.0")    # new evidence -> new version
    user = ActingUser(user_id="alice", roles=frozenset({Role.ADJUSTER}), token_subject="u-1")
    meta = RequestMeta(request_id="0b8f5c1e-1", acting_user=user, sent_at=datetime.now(timezone.utc))
    PutRecommendationRequest(meta=meta, idempotency_key=k1, recommendation=_rec())


def test_unknown_fields_rejected():
    with pytest.raises(ValidationError):
        _rec(auto_pay=True)


def test_pending_document_has_no_text():
    with pytest.raises(ValidationError):
        DocumentText(document_id="DOC-00007", claim_id="CLM-2024-1873",
                     ocr_status=OcrStatus.PENDING, text="x", sha256="c" * 64)
