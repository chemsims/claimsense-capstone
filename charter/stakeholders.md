# Stakeholder Map and RACI (Milestone 1)

The brief names roles, not people. Names are TBD until the client confirms them. The synthetic data names five adjusters (alice, bob, carol, david, eve); they stand in for the daily users.

## The four roles the brief asks for

| Role the brief asks for | Who | Why them |
|---|---|---|
| **Approver** | VP Claims (sponsor) | Owns the budget and the go-live call. Accountable for the engagement. |
| **Reviewer of co-pilot output** | Claims Supervisor / senior licensed adjuster | Signs off that the co-pilot's reasoning is sound before adjusters rely on it; owns the golden-set labels. |
| **Daily user** | Front-line licensed adjusters (alice, bob, carol, david, eve) | Run the co-pilot on every claim and confirm or override each outcome. |
| **Who can block rollout** | CISO (hard veto) — plus Compliance, SIU lead and the adjusters themselves (quiet vetoes) | See power map below. |

## Power map — who can say no

| Person | Formal role | Real power over the pilot | What they need to say yes |
|---|---|---|---|
| VP Claims | Sponsor | **Sets timeline.** Wants a demo; not a daily blocker. | A number that moves: first-pass time, consistency. |
| CISO | Security | **HARD VETO.** No system access until controls pass. | Access control in code before any agent, audit on every call, synthetic data only. |
| Compliance / Legal | Regulatory | **HARD VETO on go-live.** Unfair-claims-practice exposure if denials are wrong or unexplained. | Every denial cites a clause; a human confirms every outcome. |
| Claims Supervisor | Reviews output | **QUIET VETO.** If they distrust the reasoning, adjusters will too. | Readable reasons, citations they can click, override is easy. |
| Front-line adjusters | Daily users | **QUIET VETO.** They route around a tool that makes their day worse. | Faster than doing it by hand; never auto-decides for them. |
| SIU lead | Receives fraud referrals | **QUIET VETO.** Floods of false referrals get the feature switched off. | Fewer, better referrals with the contradiction spelled out. |
| System owners (CMS, PAS, document store IT) | Data owners | **BANDWIDTH VETO.** Anything needing them waits. | Read-only access for MVP; one small, idempotent write to CMS. |

**Most dangerous veto:** the CISO, because nothing runs without access. **Most likely to quietly kill it:** the adjusters, if the confirmation step adds work instead of removing it.

## RACI

R = Responsible (does it) · A = Accountable (one person, signs off) · C = Consulted · I = Informed

| Decision / activity | VP Claims | CISO | Compliance | Claims Supervisor | Adjusters | SIU lead | System owners | FDE |
|---|---|---|---|---|---|---|---|---|
| Engagement charter and success criteria | **A** | C | C | C | C | C | I | **R** |
| Access to client systems (CMS, PAS, doc store) | I | **A** | C | I | I | I | R | R |
| Access-control and audit design | I | **A** | C | I | I | I | C | **R** |
| Coverage logic and clause corpus | I | I | **A** | C | C | I | C | **R** |
| Golden-set labels (expected outcomes) | I | I | C | **A** | R | C (fraud cases) | I | R |
| Fraud routing rules (ROUTE_SIU) | I | I | C | C | C | **A** | I | **R** |
| Confirming each co-pilot outcome | I | I | I | C | **A/R** | I | I | I |
| Go / no-go for rollout | **A** | C (veto) | C (veto) | C | C | C | I | R |
| Incident response and rollback | I | C | I | I | I | I | C | **A/R** |
