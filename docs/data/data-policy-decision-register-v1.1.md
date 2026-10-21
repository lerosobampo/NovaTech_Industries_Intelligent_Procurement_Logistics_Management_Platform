# NovaTech Industries — Supplier Evaluation Policy Decision Register

**Checkpoint:** 2.5 | **Document ID:** NT-DATA-025A | **Version:** 1.1  
**Date:** 21 October 2026 | **Status:** Partial approval; remaining policies proposed  
**Scope:** Supplier Recommendation Engine (FR-005)  
**Case study:** Fictional organization and synthetic data

---

## 1. Purpose

This register records policy decisions for the supplier recommendation engine and separates confirmed decisions from recommendations requiring business approval. It supplements `data-policy-and-synthetic-dataset-design.md` (v1.0), rather than silently replacing it.

## 2. Confirmed decisions

| Policy | Decision | Status | Consequence |
|---|---|---|---|
| Evaluation method | Eligibility screening followed by weighted scoring: cost 40%, delivery 25%, quality 20%, reliability 15% | Confirmed | Save weights and scoring version with each evaluation |
| DP-006 — Insufficient supplier history | Require manual Procurement Manager review; do not fabricate quality or reliability scores | Approved by project owner | Supplier is marked `REVIEW_REQUIRED`; no automatic final recommendation or purchase order |
| Purchase-order control | Human approval before issuing a purchase order | Previously established requirement; implementation detail pending | Scoring produces advice, not a binding purchase |

A supplier with insufficient history may be shown as an *unscored candidate* for manual review; it must not be represented as a scored winner. The manager may request further evidence or authorize a documented exception. An exception must not be interpreted as a fabricated performance score.

## 3. Remaining decisions for approval

| ID | Topic | Recommended development baseline | Status |
|---|---|---|---|
| DP-001 | Comparison currency | EUR; retain original currency, exchange rate, rate source and date | Proposed |
| DP-002 | Comparable cost | Unit price × requested quantity + attributable freight + duties + nonrecoverable fees; avoid double-counting | Proposed |
| DP-003 | Historical lookback | Rolling 12 months as of evaluation date | Proposed |
| DP-004 | Quality sample | At least 100 inspected units for automated quality scoring | Proposed |
| DP-005 | Reliability sample | At least 10 completed deliveries for automated reliability scoring | Proposed |
| DP-007 | Same-day delivery | Allow zero days; score 100 for zero-day offers, 0 for positive-day offers when fastest is zero | Proposed; revisit steep discontinuity |
| DP-008 | Score ties | Lower comparable cost, then shorter lead time, then quotation ID | Proposed |
| DP-009 | Weights | Nonnegative and total exactly 100%; version and archive configuration | Proposed |
| DP-010 | Approval | No automatic order issuance without human authorization | Proposed implementation policy |
| DP-011 | Missing mandatory quotation data | Block automated ranking for that quotation and log reason | Proposed |
| DP-012 | Missing currency rate | Block automated ranking until a valid dated rate is available | Proposed |

## 4. Additional implementation clarifications

- **Eligibility versus manual review:** Mandatory failures (`INELIGIBLE`) remain distinct from missing-history cases (`REVIEW_REQUIRED`). Only `ELIGIBLE` quotations with complete evidence receive an automatic final score.
- **Sample counts:** Thresholds are based on completed deliveries and inspected units, not merely supplier age. A 12-month window with fewer observations triggers review.
- **Price precision:** Store currency amounts using decimal arithmetic; avoid floating-point rounding for financial values.
- **Quotation linkage:** Each quotation must be associated with a purchase requisition or equivalent evaluation context. Without this link, quantity and deadline constraints cannot be validated.
- **Evaluation reproducibility:** Persist comparison-set IDs, inputs, rate snapshots, weights, policy version, and evaluation timestamp.
- **No simulated approvals:** Synthetic records may represent approval outcomes, but test data must be explicitly marked as synthetic.

## 5. Proposed decision package

The recommended starting point is to adopt DP-001 through DP-005 and DP-008 through DP-012 as listed above. DP-007 deserves a separate review because its zero-day rule can sharply penalize next-day delivery. The development team can initially generate positive lead times (1–45 days), preserving same-day cases as a dedicated edge-case fixture until the scoring policy is approved.

**Approval request:** Confirm the recommended baseline for DP-001–DP-005 and DP-008–DP-012, and either accept the DP-007 zero-day rule or defer it to a later checkpoint.

## 6. Decision log

| Date | Decision | Decision maker | Status |
|---|---|---|---|
| 21 October 2026 | Use weighted supplier evaluation | Project owner | Confirmed |
| 21 October 2026 | Manual review for insufficient history | Project owner | Approved |
| 21 October 2026 | Other DP policies listed above | Pending | Awaiting confirmation |

## 7. Next action

Begin Checkpoint 2.6 with a limited, policy-neutral task: create the directory structure and three foundational reference datasets (`suppliers`, `products`, `supplier_products`). Do not implement automated quotation scoring until the remaining policies are approved.
