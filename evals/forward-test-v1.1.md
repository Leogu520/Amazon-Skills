# v1.1 Fresh-Agent Forward Test

Date: 2026-07-21

## Protocol

- Dataset: `evals/rewrite_quality.json`, 10 category cases.
- Blind input: generated with `scripts/export_blind_eval.py`.
- Hidden from the test agent: required phrases, forbidden phrases, expected migrations, reference titles, reference Item Highlights, expected review statuses, rubric, and scores.
- Visible to the test agent: product context, current title, structured facts, keyword priorities, verified claim IDs, and referenced brands.
- The fresh agent generated each candidate and ran the bundled validator before the main process compared results with held-out fields.

The first forward pass exposed three validator gaps: charging adapters, baby carriers, and unsupported educational/STEM positioning were not deterministic manual-review triggers. The implementation was hardened and covered by regression tests before the strict blind run.

## Blind Results

Scores use five dimensions at 0-2 points each: character compliance, anti-misbuy attribute retention, keyword tradeoffs, claim evidence, and field migration.

| Case | Character | Anti-misbuy | Keywords | Claims | Migration | Total |
|---|---:|---:|---:|---:|---:|---:|
| Consumer goods: water bottle | 2 | 2 | 2 | 2 | 2 | 10/10 |
| Automotive: wheel hub | 2 | 2 | 2 | 2 | 2 | 10/10 |
| Industrial: hex bolts | 2 | 2 | 2 | 2 | 2 | 10/10 |
| Electronics: USB-C charger | 2 | 2 | 2 | 2 | 2 | 10/10 |
| Beauty: face moisturizer | 2 | 2 | 2 | 2 | 2 | 10/10 |
| Baby: carrier | 2 | 2 | 2 | 2 | 2 | 10/10 |
| Apparel: parent jacket | 2 | 2 | 2 | 2 | 2 | 10/10 |
| Apparel: child jacket | 2 | 1 | 2 | 2 | 2 | 9/10 |
| Toys: magnetic tiles | 2 | 2 | 2 | 2 | 2 | 10/10 |
| Bundle: kitchen utensils | 2 | 2 | 2 | 2 | 2 | 10/10 |

Overall: **99/100 (9.9/10)**.

All 10 titles stayed within 75 characters and all Item Highlights stayed within 125 characters. Unsupported clinical, hypoallergenic, safety, educational, ranking, and promotional claims were removed or held for verification. Compatibility wording, age grade, weight range, counts, fitment, and parent-child variation data were retained.

The only scoring deduction was the child apparel title using `M` instead of the clearer held-out requirement `Size M`. The size value remained present, but the anti-misbuy expression was less explicit.

## Status Review

- Charging adapter: agent and validator both returned `MANUAL_REVIEW` with `SAFETY_SENSITIVE_PRODUCT_TYPE`.
- Baby carrier: agent and validator both returned `MANUAL_REVIEW` with `SAFETY_SENSITIVE_PRODUCT_TYPE`.
- The agent conservatively returned `MANUAL_REVIEW` for automotive fitment, incomplete industrial procurement data, parent/child rendering uncertainty, and incomplete bundle composition while the deterministic validator returned `READY`.
- These five agent-validator differences are conservative semantic escalations, not cases where a hard violation or unverified sensitive claim was marked ready.

No release-blocking forward-test defect remained after hardening.
