# ClaimSense AI — Capstone Engagement Repo

FDE capstone (Interview Kickstart Applied Agentic AI). Claims adjudication co-pilot for a motor insurer: given a claim, return a first decision, the reasoning, and the evidence it rests on, with a licensed adjuster confirming every outcome.

## Milestone 1 — Discovery and scoping (Week 1) ✅

| # | Deliverable | File |
|---|---|---|
| 1 | Engagement charter (three systems + integration points) | [`charter/engagement-charter.md`](charter/engagement-charter.md) |
| 2 | Stakeholder map and RACI | [`charter/stakeholders.md`](charter/stakeholders.md) |
| 3 | Four quantified success criteria | [`charter/success-criteria.md`](charter/success-criteria.md) |
| 4 | Architectural decisions log (D-001 to D-006) | [`DECISIONS.md`](DECISIONS.md) |
| 5 | 20 seed evaluation cases, all four outcomes + adversarial | [`evals/README.md`](evals/README.md), [`evals/seed_cases.jsonl`](evals/seed_cases.jsonl) |


## Milestone 2 — SoW, pricing and architecture (Week 2) ✅

| # | Deliverable | File |
|---|---|---|
| 1 | Statement of work, 2 pages | [`docs/SOW.md`](docs/SOW.md) · [`docs/SOW.pdf`](docs/SOW.pdf) |
| 2 | Architecture diagram, every flow labelled (F1–F24), code/model boundary marked | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) · [`docs/diagrams/architecture.svg`](docs/diagrams/architecture.svg) |
| 3 | Pricing model with assumptions | [`docs/PRICING.md`](docs/PRICING.md) · [`pricing/pricing_model.py`](pricing/pricing_model.py) |
| 4 | Risk register, 5 risks | [`docs/RISKS.md`](docs/RISKS.md) |
| 5 | Typed contracts for CMS, PAS, Document Store + idempotency rules | [`docs/CONTRACTS.md`](docs/CONTRACTS.md) · [`contracts/`](contracts) · [`data/schemas/`](data/schemas) |
| 6 | Synthetic data shapes: claims, policies, documents | [`docs/DATA_SHAPES.md`](docs/DATA_SHAPES.md) · [`data/synthetic/`](data/synthetic) |
| 7 | Cloud environment provisioned | [`infra/claimsense-env.yaml`](infra/claimsense-env.yaml) · [`infra/README.md`](infra/README.md) |
| — | Decisions D-007 to D-011 | [`DECISIONS.md`](DECISIONS.md) |

## Run the checks

```bash
pip install -r requirements.txt
python -m pytest -q                 # contracts load all course data; guards hold
python evals/build_seed_cases.py    # rebuild the 20 seed cases
python pricing/pricing_model.py     # every number in docs/PRICING.md
```

## Layout

```
DECISIONS.md            why we chose what we chose, dated
charter/                engagement charter, stakeholders/RACI, success criteria
evals/                  seed eval cases + the script that computes their facts
docs/                   SoW, architecture, pricing, risks, contracts, data shapes
contracts/              typed contracts (Pydantic) for the three client systems + audit
pricing/                pricing model script
infra/                  CloudFormation for the AWS environment
tests/                  contract tests against the course data
data/course/            course-supplied synthetic data (unchanged)
data/synthetic/         our additions: clause corpus, users, document text samples
data/schemas/           JSON Schema for every contract
```

All data is synthetic. No production or personal data is used at any stage.
