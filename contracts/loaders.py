"""Adapters from the course CSVs (and our synthetic extensions) to the typed contracts.

These are the synthetic stand-ins for the three client systems. In Week 3 the fake CMS / PAS /
Document Store services serve exactly these objects, so the contracts are tested on real
course data from day one.
"""
from __future__ import annotations

import csv
import json
from decimal import Decimal
from pathlib import Path

from .cms import ClaimRecord, ClaimStatus, VehicleRef
from .docstore import DocumentMeta, DocumentText
from .pas import ClauseHit, LiabilityLimit, PolicyRecord

ROOT = Path(__file__).resolve().parents[1] / "data"


def _yes(v: str) -> bool:
    if v not in ("Yes", "No"):
        raise ValueError(f"expected Yes/No, got {v!r}")
    return v == "Yes"


def _usd_or_none(v: str) -> Decimal | None:
    return None if v == "N/A" else Decimal(v)


def load_claims(path: Path = ROOT / "course" / "claims.csv") -> dict[str, ClaimRecord]:
    out = {}
    for r in csv.DictReader(path.open(encoding="utf-8")):
        out[r["claim_id"]] = ClaimRecord(
            claim_id=r["claim_id"],
            policy_id=r["policy_id"],
            vehicle=VehicleRef(
                vin=r["vehicle_vin"], year=int(r["vehicle_year"]), make=r["vehicle_make"],
                model=r["vehicle_model"], acv_usd=Decimal(r["vehicle_acv_usd"]),
            ),
            incident_date=r["incident_date"],
            incident_type=r["incident_type"],
            incident_description=r["incident_description"],
            damage_description=r["damage_description"],
            repair_estimate_usd=Decimal(r["repair_estimate_usd"]),
            injuries_reported=_yes(r["injuries_reported"]),
            police_report_filed=_yes(r["police_report_filed"]),
            assigned_adjuster=r["assigned_adjuster"],
            prior_claims_12mo=int(r["prior_claims_12mo"]),
            fraud_risk_score=Decimal(r["fraud_risk_score"]),
            claim_status=ClaimStatus(r["claim_status"]),
            created_at=r["created_at"],
        )
    return out


def load_policies(path: Path = ROOT / "course" / "policies.csv") -> dict[str, PolicyRecord]:
    out = {}
    for r in csv.DictReader(path.open(encoding="utf-8")):
        per_person, per_accident = r["liability_limit"].split("/")
        # holder_first / holder_last are deliberately dropped here (data minimisation).
        out[r["policy_id"]] = PolicyRecord(
            policy_id=r["policy_id"],
            vehicle_vin=r["vehicle_vin"],
            vehicle_acv_usd=Decimal(r["vehicle_acv_usd"]),
            coverage_type=r["coverage_type"],
            collision_coverage=_yes(r["collision_coverage"]),
            comprehensive_coverage=_yes(r["comprehensive_coverage"]),
            collision_deductible_usd=_usd_or_none(r["collision_deductible_usd"]),
            comprehensive_deductible_usd=_usd_or_none(r["comprehensive_deductible_usd"]),
            liability_limit=LiabilityLimit(
                per_person_usd=Decimal(per_person), per_accident_usd=Decimal(per_accident)
            ),
            medpay_limit_usd=Decimal(r["medpay_limit_usd"]),
            policy_status=r["policy_status"],
            policy_start=r["policy_start"],
            policy_end=r["policy_end"],
        )
    return out


def load_documents(path: Path = ROOT / "course" / "documents.csv") -> dict[str, DocumentMeta]:
    out = {}
    for r in csv.DictReader(path.open(encoding="utf-8")):
        out[r["document_id"]] = DocumentMeta(**{**r, "page_count": int(r["page_count"])})
    return out


def load_document_texts(path: Path = ROOT / "synthetic" / "document_texts.jsonl") -> dict[str, DocumentText]:
    return {
        d.document_id: d
        for d in (DocumentText(**json.loads(line)) for line in path.open() if line.strip())
    }


def load_clauses(path: Path = ROOT / "synthetic" / "policy_clauses.jsonl") -> dict[str, ClauseHit]:
    return {
        c.clause_id: c
        for c in (ClauseHit(**json.loads(line), score=0.0) for line in path.open() if line.strip())
    }
