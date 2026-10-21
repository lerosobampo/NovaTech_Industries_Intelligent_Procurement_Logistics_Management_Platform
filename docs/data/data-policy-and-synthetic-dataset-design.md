# NovaTech Industries — Data Policy Approval & Synthetic Dataset Design

**Checkpoint:** 2.5  
**Document ID:** NT-DATA-025  
**Version:** 1.0  
**Status:** Proposed for business review — not approved  
**Date:** 21 October 2026  
**Related requirements:** FR-005, BR-001–BR-006, DV-001–DV-010  
**Classification:** Internal training case study; company and data are fictional

---

## 1. Purpose and decision context

This document defines proposed operational policies and the synthetic-data plan for the NovaTech Industries Supplier Recommendation Engine. It translates the Business Requirements Document, Supplier Evaluation Requirements, Score Normalization specification, and Supplier Evaluation Data Dictionary into testable data-generation rules.

**Previously agreed:** Eligible quotations are ranked using a weighted score: total purchasing cost 40%, delivery lead time 25%, product quality 20%, and supplier reliability 15%. Mandatory eligibility rules are evaluated before scoring. The Procurement Officer reviews the recommendation before an order is issued.

**Not yet approved:** Rules for insufficient historical performance, comparison currencies, minimum observation counts, same-day delivery, score ties, and approval thresholds. This document proposes defaults; none should be treated as approved business policy until confirmed.

## 2. Policy decisions requiring approval

| ID | Policy area | Proposed policy | Rationale | Status |
|---|---|---|---|---|
| DP-001 | Evaluation currency | Compare all quotations in EUR; retain original currency, source, rate, and effective date | Reproducible cross-border comparisons | Proposed |
| DP-002 | Total cost | Unit price × requested quantity + attributable freight + duties + nonrecoverable fees; avoid double-counting | Comparable landed-cost proxy | Proposed |
| DP-003 | Historical window | Use the 12 months preceding evaluation date | Consistent recent performance | Proposed |
| DP-004 | Quality sample | Require at least 100 inspected units for automated quality scoring | Avoid unstable rates from tiny samples | Proposed |
| DP-005 | Reliability sample | Require at least 10 completed deliveries for automated reliability scoring | Avoid unstable rates from tiny samples | Proposed |
| DP-006 | Insufficient history | Mark as `REVIEW_REQUIRED`; do not fabricate scores or automatically recommend | Prevent unsupported comparisons | Proposed |
| DP-007 | Same-day lead time | Accept zero days, award delivery score 100 if shortest; otherwise use positive-day ratio | Avoid division by zero | Proposed |
| DP-008 | Equal scores | Tie-break by lower total cost, then shorter lead time, then stable quotation ID | Deterministic output | Proposed |
| DP-009 | Weight configuration | Weights must be nonnegative and total exactly 100%; save version with evaluation | Auditability | Proposed |
| DP-010 | Human approval | A recommendation never creates or sends a purchase order without approval | Maintain control over spending | Proposed |
| DP-011 | Missing required quotation fields | Exclude incomplete quotation from automated ranking and record reason | Data integrity | Proposed |
| DP-012 | Missing exchange rate | Do not score quotation until a valid rate is available | Prevent misleading cost rankings | Proposed |

### 2.1 Scoring definitions

For each eligible, sufficiently documented quotation:

- `cost_score = 100 × minimum_eligible_total_cost / quotation_total_cost` (strictly positive cost).
- `delivery_score = 100` for a zero-day offer when it is the minimum; otherwise `100 × minimum_eligible_lead_time / quotation_lead_time` when all compared lead times are positive. If the minimum is zero, zero-day offers receive 100 and positive-day offers receive 0; this edge-case rule is **proposed** and subject to review.
- `quality_score = 100 × accepted_units / inspected_units`, provided the quality sample threshold is met.
- `reliability_score = 100 × on_time_deliveries / completed_deliveries`, provided the reliability sample threshold is met.
- `weighted_score = 0.40 × cost_score + 0.25 × delivery_score + 0.20 × quality_score + 0.15 × reliability_score`.

**Important:** The relative cost and delivery scores depend on the comparison set. Save the set of eligible quotation IDs, raw values, exchange rates, criteria weights, and calculation version with every completed evaluation.

## 3. Initial synthetic dataset scope

The first release deliberately uses a small dataset that is easy to inspect manually and run on an 8 GB Intel Mac. It is a subset of the larger enterprise simulation.

| Dataset | Initial target | Grain (one row represents) | Key fields |
|---|---:|---|---|
| `suppliers.csv` | 12 | One supplier | `supplier_id`, `name`, `country`, `status`, `approved_categories` |
| `products.csv` | 20 | One product | `product_id`, `sku`, `category`, `unit_of_measure` |
| `supplier_products.csv` | 45 | One supplier-product offering | `supplier_id`, `product_id`, `min_order_qty`, `available_qty` |
| `purchase_requisitions.csv` | 15 | One requisition header | `requisition_id`, `request_date`, `required_date`, `status` |
| `requisition_items.csv` | 25 | One requested product line | `requisition_item_id`, `requisition_id`, `product_id`, `quantity` |
| `quotations.csv` | 35 | One supplier quotation header | `quotation_id`, `supplier_id`, `issued_date`, `valid_until`, `currency` |
| `quotation_items.csv` | 55 | One quotation product line | `quotation_item_id`, `quotation_id`, `product_id`, `quantity`, `unit_price`, `lead_time_days` |
| `supplier_performance.csv` | 12 | One supplier's 12-month metrics | `supplier_id`, `inspected_units`, `accepted_units`, `completed_deliveries`, `on_time_deliveries` |
| `exchange_rates.csv` | 8 | One dated currency conversion | `currency`, `rate_to_eur`, `effective_date`, `source` |
| `evaluation_criteria.csv` | 4 | One criterion and weight | `criterion`, `weight_pct`, `policy_version` |

**Initial target total:** 231 records across 10 CSV files. Targets are provisional and may change to preserve referential integrity. The larger 12-table evaluation schema and wider procurement/logistics datasets remain future phases.

## 4. Data-generation principles

1. **Deterministic:** Use a fixed random seed (proposed: `42`) so test datasets can be reproduced.
2. **Fictional:** Generate synthetic suppliers, products, quotations, and transactions. Do not use real supplier personal data or confidential business records.
3. **Referentially valid:** Every foreign key must refer to an existing parent record; no orphan quotation items.
4. **Chronologically valid:** Request dates precede required dates; quotation issue dates precede expiry; evaluations use rates and performance available as of evaluation time.
5. **Commercially plausible:** Prices, minimum quantities, lead times, and available quantities vary by product category and supplier region.
6. **Consistent units:** Quantities use each product's unit of measure; lead times use calendar days; money uses explicit currency codes.
7. **Separated data quality:** Keep the clean reference dataset separate from deliberately corrupted test fixtures.
8. **Documented assumptions:** Record generator version, seed, row counts, scenario flags, and any simplifications in a manifest.

## 5. Required test scenarios

| Scenario ID | Business scenario | Expected outcome |
|---|---|---|
| SC-001 | Multiple eligible quotations | Rank by weighted score |
| SC-002 | Cheapest supplier has slower delivery | Weighted score may favor another supplier |
| SC-003 | Supplier inactive | Exclude and record reason |
| SC-004 | Quotation expired | Exclude and record reason |
| SC-005 | Quantity unavailable or below minimum | Exclude and record reason |
| SC-006 | Delivery misses required date | Exclude and record reason |
| SC-007 | Supplier lacks sufficient quality history | Require manual review |
| SC-008 | Supplier lacks sufficient delivery history | Require manual review |
| SC-009 | Two quotations tie on weighted score | Apply deterministic tie-break |
| SC-010 | Quotation in USD with recorded EUR rate | Convert and retain conversion evidence |
| SC-011 | Exchange rate unavailable | Block automated scoring |
| SC-012 | No eligible quotations | Return clear no-recommendation outcome |
| SC-013 | Invalid negative price or lead time | Reject during validation |
| SC-014 | Same-day delivery | Apply approved zero-day scoring rule |

## 6. Dataset storage conventions

```text
ai-procurement-platform/
├── docs/
│   └── data/
│       ├── supplier-evaluation-data-dictionary.md
│       └── data-policy-and-synthetic-dataset-design.md
├── data/
│   ├── synthetic/
│   │   └── v1/
│   │       ├── suppliers.csv
│   │       ├── products.csv
│   │       └── ...
│   └── fixtures/
│       └── invalid/
└── src/
    └── data_generation/
```

**Conventions:** UTF-8 encoded CSV; ISO dates (`YYYY-MM-DD`); ISO 4217 currency codes; dot decimal separator; stable string identifiers (`SUP001`, `PRD001`, `QUO001`); snake_case field names; blank values only where explicitly allowed. Avoid storing generated secrets or personally identifying information in Git.

## 7. Quality gates before coding FR-005

- All IDs unique within their entity and all foreign keys resolve.
- No duplicate supplier-product pairs in the initial catalog.
- Valid date sequences and quotation status/expiry rules.
- Price, quantity, lead time, and exchange-rate validations pass.
- Quality and reliability numerators never exceed denominators.
- Weight percentages total exactly 100.
- All 14 test scenarios are represented and have expected results.
- Running the generator twice with the same seed produces identical outputs.
- A data manifest records version, seed, assumptions, and file row counts.

## 8. Decisions and sign-off

**Recommended starting policy:** Approve DP-001 through DP-012 as a *development baseline*, with particular review of DP-004/DP-005 (sample sizes), DP-006 (new suppliers), and DP-007 (same-day scoring). These are design proposals, not facts about an actual company.

**Business owner:** Procurement Manager (role in simulated organization)  
**Technical owner:** Business Transformation & Analytics Team  
**Approval status:** Pending user confirmation

## 9. Next checkpoint

**Checkpoint 2.6 — Synthetic Data Generator, Part 1:** After policy approval, create the directory structure and a small reproducible Python generator for `suppliers.csv`, `products.csv`, and `supplier_products.csv`. Validate keys and inspect outputs before adding quotations and evaluations.
