# NovaTech Industries
## Supplier Evaluation Business Rules — FR-005

**Project:** Intelligent Procurement & Logistics Management Platform  
**Document ID:** NVT-BRD-FR005  
**Version:** 1.0  
**Status:** Draft for business review  
**Date:** October 2026  
**Business owner:** Procurement Manager  
**Document classification:** Internal — simulated project

> **Project note:** NovaTech Industries, the supplier names, and the illustrative figures in this document are fictional. This document is part of a synthetic-data software development project.

---

## 1. Purpose and Scope

This document defines the supplier evaluation and recommendation requirements for **FR-005**. The platform shall assess supplier eligibility, compare eligible quotations using a weighted scoring model, explain the resulting ranking, and present a recommendation for human review.

**Business objective:** Improve purchasing decisions by balancing total acquisition cost, delivery performance, product quality, and supplier reliability.

**In scope:** Mandatory eligibility rules, scoring criteria and weights, quotation ranking, data inputs, recommendation output, traceability, and preliminary acceptance criteria.

**Out of scope for this version:** Automated purchase order approval, predictive demand planning, autonomous purchasing, and final normalization formulas (to be defined in Checkpoint 2.3).

## 2. Requirement Definition

| Field | Definition |
|---|---|
| Requirement ID | FR-005 |
| Requirement name | Weighted Supplier Evaluation and Recommendation |
| Business owner | Procurement Manager |
| Primary user | Procurement Officer |
| Requirement priority | Must |
| Decision authority | Procurement Officer / authorized approver |

**Requirement statement:** The system shall evaluate eligible supplier quotations using a configurable weighted scoring model and recommend the most suitable purchasing option, subject to applicable business constraints and human approval.

### 2.1 End-to-End Decision Process

1. **Eligibility assessment:** Apply mandatory supplier and quotation constraints.
2. **Weighted evaluation:** Calculate normalized criterion scores for eligible quotations.
3. **Ranking:** Sort eligible quotations by final weighted score.
4. **Recommendation:** Present the highest-ranked quotation, its component scores, and an explanation.
5. **Human approval:** Require an authorized user to review the recommendation before a purchase order is issued.

## 3. Stage 1 — Mandatory Eligibility Rules

A quotation must satisfy **all** mandatory conditions before receiving a final evaluation score.

| Rule ID | Mandatory condition | Expected system behavior |
|---|---|---|
| BR-001 | Supplier has active status | Exclude inactive suppliers |
| BR-002 | Supplier is approved for the product category | Exclude unapproved suppliers |
| BR-003 | Quotation is valid on the evaluation date | Exclude expired or not-yet-valid quotations |
| BR-004 | Supplier can fulfill requested quantity and minimum order conditions | Exclude infeasible quotations |
| BR-005 | Quoted delivery meets required delivery date | Exclude quotations that cannot meet the mandatory deadline |
| BR-006 | Supplier meets applicable quality and compliance requirements | Exclude noncompliant suppliers |

**Policy:** An ineligible quotation cannot be recommended, even if it offers the lowest price. The system must record the specific exclusion reason(s).

## 4. Stage 2 — Weighted Supplier Evaluation

The initial evaluation policy uses four criteria. Weights are proposed configuration values and require business approval before production use.

| Criterion | Code | Weight | Preferred direction |
|---|---|---:|---|
| Total purchasing cost | C | 40% | Lower is better |
| Delivery lead time | D | 25% | Shorter is better |
| Product quality | Q | 20% | Higher is better |
| Supplier reliability | R | 15% | Higher is better |
| **Total** | | **100%** | |

Each criterion is normalized to a score from **0 to 100** before aggregation.

**Weighted score formula:**

`S = 0.40 × C + 0.25 × D + 0.20 × Q + 0.15 × R`

Where `C`, `D`, `Q`, and `R` are normalized criterion scores. The highest-scoring **eligible** quotation becomes the recommended option.

### 4.1 Configuration Controls

- Configured weights must sum to **100%**; invalid configurations must not be activated.
- Weight changes must be versioned, dated, and attributable to an authorized user.
- Evaluation results must retain the weight configuration and underlying data used at the time of scoring.
- Tie-breaking rules will be defined before implementation; the system must not silently choose an arbitrary winner.

## 5. Illustrative Supplier Comparison

The following scores are already normalized. **All three quotations are assumed eligible**. They are examples only, not observed supplier performance.

| Supplier | Cost C | Delivery D | Quality Q | Reliability R | Weighted score |
|---|---:|---:|---:|---:|---:|
| EuroParts GmbH | 80 | 95 | 92 | 96 | **88.55** |
| Shenzhen Components | 100 | 65 | 85 | 84 | **85.85** |
| Nordic Industrial AB | 72 | 90 | 98 | 95 | **85.15** |

**Calculation example — EuroParts GmbH:**

`S = (0.40 × 80) + (0.25 × 95) + (0.20 × 92) + (0.15 × 96) = 88.55`

**Illustrative recommendation:** EuroParts GmbH ranks first under the initial weight configuration. A lower-cost quotation does not necessarily produce the highest overall score because delivery, quality, and reliability also contribute.

## 6. Data Requirements

The following datasets and fields are needed to support FR-005. The final schema, keys, data types, and validation rules will be documented in the Data Dictionary.

| Dataset | Minimum required fields | Purpose |
|---|---|---|
| `suppliers` | supplier_id, supplier_name, status, approval_status | Supplier eligibility |
| `products` | product_id, category_id, description | Product/category identification |
| `supplier_products` | supplier_id, product_id, minimum_order_quantity, available_quantity | Supply feasibility |
| `purchase_requisitions` | requisition_id, required_delivery_date, evaluation_currency | Purchasing constraints |
| `requisition_items` | requisition_id, product_id, requested_quantity | Requested products and volumes |
| `quotations` | quotation_id, supplier_id, valid_from, valid_until, currency | Quotation eligibility and currency |
| `quotation_items` | quotation_id, product_id, quoted_quantity, unit_price, lead_time_days | Commercial comparison |
| `supplier_performance` | supplier_id, evaluation_period, quality_score, on_time_delivery_rate, sample_size | Historical performance |
| `evaluation_criteria` | criteria_version, criterion_code, weight, normalization_method | Scoring configuration |
| `supplier_evaluations` | evaluation_id, quotation_id, criteria_version, component_scores, final_score, evaluation_timestamp, eligibility_result | Auditability and results |

**Additional data considerations:** Freight costs, duties, exchange rates and their effective dates, compliance requirements, quotation-specific delivery dates, and approval records may require separate fields or tables. The data dictionary will resolve these details.

## 7. Business Policy Considerations

### 7.1 Total Purchasing Cost

Comparisons should use a consistent **total purchasing cost** rather than unit price alone. Depending on purchasing terms and data availability, this may include merchandise cost, freight, duties, and other directly attributable acquisition charges. The precise cost boundary must be documented.

### 7.2 Currency Conversion

Quotations in different currencies must be converted to a common evaluation currency using a recorded exchange rate, rate date, and source. Comparisons must not mix raw amounts denominated in different currencies.

### 7.3 Score Normalization

Raw measures (such as EUR and days) must be transformed into comparable scores between 0 and 100. The normalization methodology, treatment of outliers, and sensitivity to the set of quotations will be specified in **Checkpoint 2.3**.

### 7.4 Historical Supplier Performance

Quality and reliability scores must be derived from defined performance measures and an explicit observation period. Missing or insufficient history requires a documented policy; the system must not assume an unverified perfect score.

### 7.5 Explainability and Human Oversight

The recommendation interface must display eligibility decisions, criterion scores, configured weights, final rankings, and supporting data. Recommendation does not constitute purchasing approval.

## 8. Functional Acceptance Criteria

FR-005 is ready for acceptance testing when the system can demonstrate that it:

1. Excludes inactive suppliers.
2. Excludes suppliers not approved for the relevant product category.
3. Excludes quotations that are not valid on the evaluation date.
4. Rejects quotations that do not satisfy quantity and minimum-order constraints.
5. Enforces mandatory delivery-date constraints.
6. Applies applicable quality and compliance requirements.
7. Calculates comparable purchasing costs in the selected evaluation currency.
8. Normalizes the four evaluation criteria according to the approved method.
9. Validates that active weights total exactly 100%.
10. Ranks eligible quotations by weighted score.
11. Explains the recommended supplier and the reasons for exclusions.
12. Handles no-eligible-supplier and incomplete-data cases without issuing a recommendation.
13. Preserves an auditable record of inputs, scoring configuration, results, and reviewer decision.
14. Requires authorized human review before a purchase order is issued.

## 9. Open Decisions and Next Checkpoint

| Decision | Status | Next action |
|---|---|---|
| Evaluation strategy | **Approved for project design: weighted score** | Implement after data model is finalized |
| Initial weights (40/25/20/15) | Proposed | Validate with procurement stakeholders |
| Normalization formulas | Open | Define in Checkpoint 2.3 |
| Missing-data policy | Open | Define in Checkpoint 2.3 |
| Tie-breaking logic | Open | Define before implementation |
| Cost inclusion rules | Open | Define before database implementation |
| Performance observation period | Open | Define before data generation |

**Next checkpoint:** **2.3 — Score Normalization & Data Validation.** Define the conversion of raw business measures to normalized scores, input validation, missing-data policies, and edge-case handling. The approved outcomes will then be incorporated into the broader Business Requirements Document (`docs/business/business-requirements.md`).
