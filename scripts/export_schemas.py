"""Write JSON Schema for every contract and data shape to data/schemas/. Re-run after edits."""
import json
from pathlib import Path

from contracts import audit, cms, docstore, pas

OUT = Path(__file__).resolve().parents[1] / "data" / "schemas"
MODELS = {
    "claim": cms.ClaimRecord, "policy": pas.PolicyRecord, "document": docstore.DocumentMeta,
    "document_text": docstore.DocumentText, "policy_clause": pas.ClauseHit,
    "cms.get_claim.request": cms.GetClaimRequest, "cms.get_claim.response": cms.GetClaimResponse,
    "cms.get_assignment.response": cms.GetAssignmentResponse,
    "cms.put_recommendation.request": cms.PutRecommendationRequest,
    "cms.put_recommendation.response": cms.PutRecommendationResponse,
    "pas.get_policy.response": pas.GetPolicyResponse,
    "pas.search_clauses.request": pas.SearchClausesRequest,
    "pas.search_clauses.response": pas.SearchClausesResponse,
    "docstore.list_documents.response": docstore.ListDocumentsResponse,
    "docstore.get_document_text.request": docstore.GetDocumentTextRequest,
    "audit.record": audit.AuditRecord,
}
OUT.mkdir(parents=True, exist_ok=True)
for name, m in MODELS.items():
    (OUT / f"{name}.schema.json").write_text(json.dumps(m.model_json_schema(), indent=2))
print(f"wrote {len(MODELS)} schemas to {OUT}")
