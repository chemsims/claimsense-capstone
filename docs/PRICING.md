# Pricing model

**Recommendation: fixed floor of $151,000, plus a $7,500 bonus for each of the 4 acceptance criteria met on the held-out eval set (max $30,000). Expected $173,500, max $181,000.** Model and cloud run costs are passed through at cost.

Numbers come from [`pricing/pricing_model.py`](../pricing/pricing_model.py). Change an assumption, re-run, and every figure below updates. It uses the Week 14 class method: T-shirt size, day range, per-risk buffer on the high end, cost, four pricing options, margin check.

## 1. Estimate (cost basis)

| Milestone | Size | Risk class (buffer) | Days low / expected / high |
|---|---|---|---|
| M1 Discovery & scoping | S | low (1.10) | 3 / 4 / 5.5 |
| M2 SoW, architecture, AWS environment | S | low (1.10) | 3 / 4 / 5.5 |
| Controls review / data-access gate | M | access politics (1.80) | 8 / 10 / 21.6 |
| M3 Agents, retrieval, CI eval gate | L | novel (1.50) | 15 / 20 / 37.5 |
| M4 Access boundary + audit | M | integration (1.35) | 8 / 10 / 16.2 |
| M5 150 evals, dashboard, drill, handover | L | integration (1.35) | 15 / 20 / 33.8 |
| **Total** | | | **52 / 68 / 120** |

**Cost = days × $1,600 + $12,000 overhead = $95,200 / $120,800 / $204,080.**

68 expected days over 5 weeks is a team of 2.7 FTE: FDE lead (1.0), engineer (1.0), eval/data engineer (0.7).

The high case (120 days) does not fit in 5 weeks. If it happens, the timeline slips; the team does not grow. The biggest buffer is on the controls-review line, because getting security sign-off usually takes longer than writing the code.

## 2. Four options for the same scope

| Model | Price | Margin | Who carries the risk | Fit here |
|---|---|---|---|---|
| T&M with cap | $163,080 expected, cap $203,850 | 26% | Shared | Scope is already clear after discovery, so T&M gives the client less certainty than they need. |
| Fixed price | $172,571 | 30%, falls to $21,571 on a 25% overrun | Vendor | Good scoping, but a slow controls review puts all the overrun on us. |
| Outcome-based (per claim) | — | — | Shared | **Can't be priced in the pilot.** It runs on synthetic data only, so there are no real claims to count. |
| **Fixed floor + acceptance bonus** | **$151,000 floor; $173,500 expected; $181,000 max** | 20% at floor, 30% expected; $22,500 on a 25% overrun | Mostly vendor, capped | **Recommended** |

**Why this one, in the client's terms:** procurement gets a hard ceiling ($181,000). The VP of Claims gets a vendor paid more only when the four numbers they care about are met: accuracy, latency, confirmation rate and fraud routing. The floor keeps us whole while the controls review runs.

**The bonus is measurable without real claims.** Each criterion is checked on the 150-case held-out set (Week 5) using the thresholds in the SoW. The client's Claims Supervisor confirms the labels, so neither side counts its own score.

**Payment schedule:** 30% ($45,300) when the M2 SoW is signed, 40% ($60,400) when M4 is accepted (two-user access test passes), 30% ($45,300) plus any bonus when M5 is accepted.

## 3. Margin check

The class benchmark is $0.6–1.0M revenue per engineer per year. For 2.7 FTE over 5 weeks that gives **$156,923 to $261,538**. Expected revenue of $173,500 is inside the band, near the low end. That's acceptable for a land-and-expand pilot. If the pilot couldn't clear cost plus buffer plus margin, the fix would be a smaller scope, not a lower price.

## 4. Run costs (pass-through, not in the fee)

| Item | Estimate | Basis |
|---|---|---|
| Model cost per claim | **$0.0027** | 12,000 input + 1,500 output tokens at $0.15 / $0.60 per 1M (gpt-4o-mini list price) |
| One 150-case eval run in CI | **$0.41** | 150 × per-claim cost |
| Same at 4× token price | $0.011 per claim | sensitivity, in case the price differs or a bigger model is needed |
| AWS during the pilot | ~$50/month | small Fargate service, load balancer, DynamoDB on demand, logs. **Not verified with the AWS calculator yet.** |

Model cost is not a pricing risk. Even at 4× it's about a cent per claim. People's time is the cost that matters.

## 5. After the pilot (expansion, priced later)

Once the system runs on real claims, a per-claim price becomes possible: **price per adjuster-confirmed first pass**. We don't quote that number yet because it depends on today's minutes per first pass and the client's claim volume (charter open question 1). Making up those numbers would undercut the pilot's credibility.

## Assumptions (all of them)

| # | Assumption | What changes if it's wrong |
|---|---|---|
| A1 | Blended rate $1,600/day ($200/hr) | Cost scales linearly |
| A2 | $12,000 fixed overhead (class default) | ± directly |
| A3 | T-shirt day ranges and risk buffers from the class notebook | Sizes are the main lever on cost |
| A4 | Synthetic data only for the whole pilot (CISO memo) | Production access would add a second, longer controls review |
| A5 | Client gives AWS sandbox and clause wording within Week 2 | Each week of delay moves M3 a week |
| A6 | ~12k input / 1.5k output tokens per claim | Run cost only |
| A7 | gpt-4o-mini at $0.15 / $0.60 per 1M tokens. Most trackers show this; one shows double. Check [OpenAI pricing](https://developers.openai.com/api/docs/pricing) before signing | Run cost only |
| A8 | Margin targets 20% floor, 30% fixed | Price |
| A9 | Bonus $7,500 per criterion, 4 criteria | Upside only |
| A10 | Plan for 3 of 4 criteria met | Expected revenue ± $7,500 |
