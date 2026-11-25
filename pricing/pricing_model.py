"""ClaimSense pilot pricing model. Stdlib only. Run: python pricing/pricing_model.py

Method follows the Week 14 class notebook: T-shirt size -> day range, a risk buffer per risk
class applied to the high end, cost = days x blended rate + fixed overhead, then four pricing
wrappers and a margin check. Every input below is an ASSUMPTION and is listed in PRICING.md.
"""
from __future__ import annotations

from dataclasses import dataclass

TSHIRT = {"S": (3, 5), "M": (8, 12), "L": (15, 25), "XL": (30, 50)}      # class notebook
RISK_BUFFER = {"low": 1.10, "integration": 1.35, "access_politics": 1.80, "novel": 1.50}

BLENDED_DAY_RATE = 1600     # A1: $200/hr blended across FDE lead, engineer, eval engineer
FIXED_OVERHEAD = 12000      # A2: tooling, PM, eval-set authoring, cloud during build (class default)


@dataclass(frozen=True)
class Milestone:
    name: str
    size: str
    risk: str
    why: str


MILESTONES = [
    Milestone("M1 Discovery & scoping", "S", "low", "done; charter, RACI, 20 seed cases"),
    Milestone("M2 SoW, architecture, AWS env", "S", "low", "paper + one CloudFormation stack"),
    Milestone("Controls review / data access gate", "M", "access_politics", "CISO sign-off on synthetic-only build and data annex"),
    Milestone("M3 Agents, retrieval, CI eval gate", "L", "novel", "4 typed agents, clause RAG, gate that blocks image push"),
    Milestone("M4 Access boundary + audit", "M", "integration", "OBO auth, entitlement before agents, two-user test"),
    Milestone("M5 150 evals, dashboard, drill, handover", "L", "integration", "adversarial families, alarm, incident drill, runbook"),
]

# Run costs (pass-through to client at cost, NOT in the fee)
TOKENS_IN_PER_CLAIM = 12_000      # A6: claim + policy + ~4 docs + 5 clauses across 4 agent calls
TOKENS_OUT_PER_CLAIM = 1_500
PRICE_IN_PER_M, PRICE_OUT_PER_M = 0.15, 0.60   # A7: gpt-4o-mini list price per 1M tokens
EVAL_CASES = 150


def estimate():
    rows, lo, ex, hi = [], 0.0, 0.0, 0.0
    for m in MILESTONES:
        a, b = TSHIRT[m.size]
        e, h = (a + b) / 2, b * RISK_BUFFER[m.risk]
        rows.append((m, a, e, h))
        lo, ex, hi = lo + a, ex + e, hi + h
    return rows, lo, ex, hi


def cost(days: float) -> float:
    return days * BLENDED_DAY_RATE + FIXED_OVERHEAD


def main() -> dict:
    rows, lo, ex, hi = estimate()
    c_lo, c_ex, c_hi = cost(lo), cost(ex), cost(hi)

    tm_price = c_ex * 1.35
    tm_cap = tm_price * 1.25
    fixed = c_ex / (1 - 0.30)
    floor = c_ex / (1 - 0.20)
    bonus_each, criteria = 7_500, 4                # A9: $7.5k per acceptance criterion met
    bonus_expected = 3 * bonus_each                 # A10: plan for 3 of 4 met
    floor_exp, floor_max = floor + bonus_expected, floor + criteria * bonus_each

    fte = ex / 25                                   # 5 weeks x 5 working days
    rev_lo, rev_hi = fte * 5 / 52 * 600_000, fte * 5 / 52 * 1_000_000
    per_claim = TOKENS_IN_PER_CLAIM / 1e6 * PRICE_IN_PER_M + TOKENS_OUT_PER_CLAIM / 1e6 * PRICE_OUT_PER_M

    print("ESTIMATE (days)")
    for m, a, e, h in rows:
        print(f"  {m.name:<42} {m.size:>2} {m.risk:<16} {a:>4.0f} {e:>5.1f} {h:>6.1f}")
    print(f"  {'TOTAL':<42} {'':>2} {'':<16} {lo:>4.0f} {ex:>5.1f} {hi:>6.1f}")
    print(f"COST low/exp/high: ${c_lo:,.0f} / ${c_ex:,.0f} / ${c_hi:,.0f}")
    print(f"Team implied by expected days over 5 weeks: {fte:.1f} FTE")
    print("PRICING OPTIONS")
    print(f"  T&M with cap   expected ${tm_price:,.0f}  cap ${tm_cap:,.0f}  margin {(tm_price-c_ex)/tm_price:.0%}")
    print(f"  Fixed price    ${fixed:,.0f}  margin {(fixed-c_ex)/fixed:.0%}; if 25% overrun margin ${fixed-c_ex*1.25:,.0f}")
    print("  Outcome-based  not priceable: the pilot runs on synthetic data, so there are no real resolved claims to count")
    print(f"  RECOMMENDED floor + gate bonus: floor ${floor:,.0f}; expected ${floor_exp:,.0f}; max ${floor_max:,.0f}")
    print(f"    expected margin {(floor_exp-c_ex)/floor_exp:.0%}; margin at floor only {(floor-c_ex)/floor:.0%}")
    print(f"    margin if 25% overrun, expected bonus: ${floor_exp-c_ex*1.25:,.0f}")
    print(f"MARGIN CHECK revenue/engineer band for {fte:.1f} FTE x 5 wks: ${rev_lo:,.0f} - ${rev_hi:,.0f}")
    print(f"RUN COST model per claim ${per_claim:.4f}; per 150-case eval run ${per_claim*EVAL_CASES:.2f}; "
          f"at 4x token price ${per_claim*4:.4f}/claim")
    return dict(lo=lo, ex=ex, hi=hi, c_ex=c_ex, floor=floor, floor_exp=floor_exp, floor_max=floor_max)


if __name__ == "__main__":
    main()
