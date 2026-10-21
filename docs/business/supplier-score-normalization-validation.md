# NovaTech Industries
## FR-005 — Supplier Score Normalization & Data Validation

**Document ID:** NVT-BRD-FR005-02  
**Version:** 1.0  
**Status:** Proposed business rules — pending approval  
**Date:** 21 October 2026  
**Business Owner:** Procurement Manager  
**Related Requirement:** FR-005 — Supplier Recommendation  
**Project:** Intelligent Procurement & Logistics Management Platform

> **Case-study note:** NovaTech Industries, supplier names, transaction figures, and performance values are fictional. The policies in this document are proposed for the simulated organization and are not yet implemented.

---

## 1. Purpose and Scope

Define how eligible supplier quotations are converted into comparable scores, ranked, validated, and recorded. This document expands FR-005 and supports the future data dictionary, Python evaluation engine, and database implementation.

The process follows two stages: (1) mandatory eligibility screening and (2) weighted scoring of eligible quotations. A recommendation is subject to procurement review and does not automatically authorize a purchase order.

## 2. Supplier Evaluation Policy

| Criterion | Weight | Direction | Score range |
|---|---:|---|---|
| Total comparable purchasing cost | 40% | Lower is better | 0–100 |
| Quoted delivery lead time | 25% | Shorter is better | 0–100 |
| Historical product quality | 20% | Higher is better | 0–100 |
| Historical delivery reliability | 15% | Higher is better | 0–100 |
| **Total** | **100%** | | |

**Weighted score:** `S = 0.40 × C + 0.25 × D + 0.20 × Q + 0.15 × R`.

All four component scores must be valid and normalized to a 0–100 scale before calculation. A higher weighted score indicates a stronger overall quotation under the configured policy.

## 3. Eligibility Screening (Before Scoring)

| Rule | Requirement |
|---|---|
| BR-001 | Supplier status is active. |
| BR-002 | Supplier is approved for the requested product category. |
| BR-003 | Quotation has not expired on the evaluation date. |
| BR-004 | Quoted capacity and minimum order quantity accommodate the requested quantity. |
| BR-005 | Quoted delivery meets the required delivery date. |
| BR-006 | Applicable quality and compliance requirements are met. |

**Policy:** A quotation failing any mandatory rule is marked *ineligible* and is not assigned a recommendation rank. The system records the specific rejection reason(s).

## 4. Normalization Formulas

### 4.1 Cost score (C)

`C_i = 100 × (minimum eligible comparable total cost / supplier i comparable total cost)`

The cheapest eligible quotation scores 100. All compared totals must use the same currency, quantity basis, and defined cost components. Cost must be strictly positive. Freight, duties, and other acquisition charges should be included when known and applicable; otherwise the evaluation must disclose the excluded components.

### 4.2 Delivery score (D)

`D_i = 100 × (minimum eligible lead time / supplier i lead time)`

The fastest eligible quotation scores 100. Lead times must be positive calendar days, measured from a consistent start event. Same-day delivery (`0` days) is an unresolved edge case requiring a separate approved rule; it must not be processed using this ratio.

### 4.3 Quality score (Q)

`Q_i = 100 × (accepted inspected units / total inspected units)`

Calculate over a rolling 12-month period. The inspected-unit denominator must be positive. The metric is an acceptance rate, not a subjective supplier rating.

### 4.4 Reliability score (R)

`R_i = 100 × (on-time completed deliveries / total completed deliveries)`

Calculate over a rolling 12-month period. The completed-delivery denominator must be positive. Define *on time* consistently using the contractual or confirmed delivery date.

### 4.5 Weighted score and ranking

`S_i = 0.40 × C_i + 0.25 × D_i + 0.20 × Q_i + 0.15 × R_i`

Rank eligible quotations by descending `S_i`. Preserve unrounded precision during calculations and round only for display. A tie-breaking policy is not yet approved; equal scores must be flagged for procurement review rather than resolved arbitrarily.

## 5. Worked Evaluation Example

All three illustrative quotations have passed eligibility screening and quote for the same quantity. Monetary amounts are comparable totals in EUR.

| Supplier | Total cost (EUR) | Lead time (days) | Quality (%) | Reliability (%) |
|---|---:|---:|---:|---:|
| EuroParts GmbH | 12,000 | 5 | 98 | 96 |
| Shenzhen Components | 10,000 | 12 | 92 | 84 |
| Nordic Industrial AB | 11,500 | 7 | 99 | 95 |

The minimum eligible cost is EUR 10,000 and the minimum lead time is 5 days.

| Supplier | Cost score | Delivery score | Quality score | Reliability score | Weighted score |
|---|---:|---:|---:|---:|---:|
| EuroParts GmbH | 83.33 | 100.00 | 98.00 | 96.00 | **92.33** |
| Shenzhen Components | 100.00 | 41.67 | 92.00 | 84.00 | **81.42** |
| Nordic Industrial AB | 86.96 | 71.43 | 99.00 | 95.00 | **86.69** |

**Recommended supplier: EuroParts GmbH (92.33/100).** It achieves the highest weighted score, despite not being the lowest-cost option. The recommendation requires Procurement Officer review before purchase order creation.

## 6. Data Validation Rules

| ID | Validation | System response |
|---|---|---|
| DV-001 | Comparable total cost is greater than zero. | Reject invalid input. |
| DV-002 | Lead time is valid and non-negative; ratio requires positive value. | Flag zero-day case; reject negative values. |
| DV-003 | Quality score is within 0–100. | Reject out-of-range value. |
| DV-004 | Reliability score is within 0–100. | Reject out-of-range value. |
| DV-005 | Supplier identifier exists and references the correct supplier. | Reject broken reference. |
| DV-006 | Quotation is valid, eligible, and comparable. | Exclude or flag with reason. |
| DV-007 | Currency conversion uses a stored exchange rate and effective date. | Hold evaluation if conversion unavailable. |
| DV-008 | Configured weights total exactly 100%. | Reject configuration. |
| DV-009 | Quality/reliability denominators are positive. | Mark history insufficient or unavailable. |
| DV-010 | Evaluation inputs, rules, and results are auditable. | Save an evaluation snapshot. |

## 7. Missing and Insufficient Data

- **Missing price or lead time:** Hold the quotation for completion; do not calculate a score.
- **Missing quality or reliability history:** Flag for manual review; do not assume either zero or 100.
- **Small historical sample:** Flag low confidence and require Procurement Manager review. A minimum sample threshold will be defined in the next policy revision.
- **Missing currency rate:** Hold the evaluation until a dated rate is available.
- **No eligible quotations:** Return an explicit *no eligible suppliers* result and list exclusion reasons.

## 8. Data Requirements

| Dataset | Fields needed for FR-005 |
|---|---|
| `suppliers` | `supplier_id`, `name`, `status`, `approval_status` |
| `products` | `product_id`, `category_id`, `description` |
| `supplier_products` | `supplier_id`, `product_id`, `minimum_order_quantity`, `available_quantity` |
| `purchase_requisitions` / items | requested product, quantity, required delivery date |
| `quotations` | `quotation_id`, `supplier_id`, `valid_until`, currency |
| `quotation_items` | product, quantity, unit price, lead time, relevant charges |
| `supplier_performance` | accepted/inspected units, on-time/completed deliveries, measurement window |
| `evaluation_criteria` | criterion, weight, formula version, effective date |
| `supplier_evaluations` | quotation IDs, raw values, normalized scores, weights, rank, status, timestamp |
| `exchange_rates` | currency pair, rate, effective date, source |

Dataset names are provisional until the full data dictionary and relational schema are approved.

## 9. Auditability and Reproducibility

Store the eligible quotation set, exclusions and reasons, source currency amounts, conversion rates, cost components, raw lead times, performance numerators and denominators, normalization baselines, weights, formula version, calculation timestamp, and approval status. Because cost and delivery scores depend on the eligible comparison set, a saved score without its context is not reproducible.

## 10. Acceptance Criteria

1. Only eligible quotations enter the ranking.
2. Cost and lead-time scores are calculated using the eligible comparison set.
3. Quality and reliability are calculated from valid 12-month historical records.
4. Weights are validated to total exactly 100%.
5. Invalid or missing mandatory data cannot silently produce a recommendation.
6. Rankings and individual component scores are visible to procurement users.
7. All recommendations preserve the inputs and policy version used.
8. Ties, insufficient history, and no-eligible-supplier cases are surfaced for human review.

## 11. Open Policy Decisions

- Define minimum sample sizes for quality and reliability metrics.
- Finalize the full comparable-cost definition and treatment of missing freight/duty data.
- Define a rule for same-day (`0` day) lead time.
- Define a deterministic tie-breaker, if desired.
- Determine how to evaluate new suppliers without sufficient history.
- Establish the exchange-rate source and effective-date policy.

## 12. Next Checkpoint

**Checkpoint 2.4 — Supplier Evaluation Data Dictionary:** Specify field names, data types, keys, constraints, relationships, and representative synthetic records for FR-005.
