# NovaTech Industries
## Checkpoint 2.6 — Step 4: Quotation Eligibility & Purchasing Cost Analysis

**Document ID:** NT-DATA-2.6-04  
**Version:** 1.0  
**Status:** Training implementation — preliminary validation  
**Date:** 21 October 2026  
**Related requirements:** FR-004, FR-005; BR-001 to BR-006; DV-001 to DV-010

> **Case-study note:** NovaTech Industries, its transactions, and its suppliers are fictional. This document describes a reproducible local training exercise, not a production-ready purchasing approval system.

## 1. Objective

Analyze the existing six connected `v2` CSV datasets, calculate comparable EUR purchasing costs, and identify quotations blocked by business constraints. **Do not select or approve a supplier yet.** The historical quality, reliability, category approval, and compliance evidence required for full FR-005 eligibility are not yet available.

## 2. Inputs and output

| Input dataset | Role |
|---|---|
| `suppliers.csv` | Supplier identity and active status |
| `products.csv` | Product master data (used upstream to create valid relationships) |
| `supplier_products.csv` | Supplier/product relationship, MOQ, and available stock |
| `purchase_requisitions.csv` | Requested quantity, request date, required delivery date |
| `quotations.csv` | Supplier, requisition, currency, quotation validity, status |
| `quotation_items.csv` | Quoted quantity, unit price, freight, duties, fees, lead time |

**Generated output:** `data/analysis/v2/quotation_eligibility_results.csv` (14 rows; one per quotation).

## 3. Business logic for this checkpoint

**Comparable purchasing cost (EUR):**

`total_cost_eur = (quoted_quantity × unit_price_eur) + freight_eur + duties_eur + other_fees_eur`

The cost is calculated for the **quoted quantity**, which may exceed the requested quantity because of minimum order requirements. It is not yet a full landed-cost or inventory-optimization model. Every `v2` quotation uses EUR; the script explicitly rejects other currencies until exchange-rate data is implemented.

**Expected delivery date:**

`expected_delivery_date = requisition.request_date + quotation_item.lead_time_days`

For this training dataset, lead times are interpreted as **calendar days from the requisition request date**. A production system should instead use an explicitly defined order-placement/acceptance date and shipping terms.

**Blocking checks implemented:**

1. Supplier status is `ACTIVE`.
2. Quotation status is `RECEIVED`.
3. Quotation `valid_until` is on or after the requisition `request_date` (the fixed simulation evaluation date).
4. Quoted quantity covers the requested quantity.
5. Quoted quantity satisfies the supplier's minimum order quantity.
6. Quoted quantity does not exceed the supplier's recorded available quantity.
7. Expected delivery date is on or before the required delivery date.
8. Currency is EUR, with nonnegative finite monetary amounts and positive quantities and lead times.

**Preliminary statuses:**

- `BLOCKED`: At least one implemented constraint fails; the output lists all detected reasons.
- `PENDING_REVIEW`: The implemented checks pass, but category authorization, compliance, and supplier performance are not verified. **This does not mean eligible, approved, or recommended.**

## 4. Why use `Decimal` instead of `float`?

Python's `float` uses binary floating-point and can introduce tiny rounding differences in financial calculations. `decimal.Decimal` represents decimal amounts precisely. We use it for quotation prices and fees; later we will establish explicit currency rounding policies.

## 5. Practical implementation

### Step A — Save the script

Download `analyze_quotation_eligibility_v2.py` and save it as:

`src/analysis/analyze_quotation_eligibility_v2.py`

Create the directory if necessary:

```bash
cd ~/Documents/Projects/ai-procurement-platform
mkdir -p src/analysis
```

The script loads existing `v2` CSVs, checks the relationships, computes costs and delivery dates, writes a new analysis CSV, and prints a summary. **It does not overwrite the six source datasets.**

### Step B — Run the analysis

```bash
python3 src/analysis/analyze_quotation_eligibility_v2.py
```

Expected output for the fixed synthetic `v2` generator:

```text
Analyzed quotations: 14
Blocked by available checks: 4
Pending manual/compliance review: 10
Created data/analysis/v2/quotation_eligibility_results.csv
No supplier recommendation issued: weighted scoring and full eligibility are not implemented.
```

### Step C — Inspect the output

```bash
head -n 6 data/analysis/v2/quotation_eligibility_results.csv
```

Locate `QUO001`: it must be blocked with `EXPIRED_QUOTATION`. Inspect another blocked quotation and explain the reason code.

## 6. Output schema

| Field | Meaning |
|---|---|
| `quotation_id` | Quotation identifier |
| `requisition_id` | Linked purchase requisition |
| `supplier_id` | Supplier identifier |
| `product_id` | Product identifier |
| `requested_quantity` | Quantity needed by NovaTech |
| `quoted_quantity` | Quantity covered by the quotation |
| `unit_price_eur` | Unit price in EUR |
| `total_cost_eur` | Calculated total for quoted quantity |
| `expected_delivery_date` | Simulated delivery date |
| `required_delivery_date` | Requisition deadline |
| `preliminary_status` | `BLOCKED` or `PENDING_REVIEW` |
| `reasons` | Semicolon-separated blocking reasons or pending-review explanation |

## 7. Limitations and deferred decisions

- **No weighted scores yet.** Quality and reliability data are not generated, so FR-005 supplier ranking remains deferred.
- **No category approval or compliance verification yet.** These must be modeled before calling any quotation fully eligible.
- **No foreign exchange conversion yet.** EUR-only analysis is deliberate and enforced.
- **No approval workflow yet.** `PENDING_REVIEW` is a flag for human assessment, not authorization to purchase.
- **Dates are fixed for reproducibility.** The generator uses 15 October 2026 as its simulation request/evaluation date. Do not substitute today's date when interpreting the CSV.
- **One quotation item per quotation.** The current dataset is simplified; multi-line quotations will require a grouped cost calculation.
- **No supplier-specific delivery calendar or incoterm treatment.** These are future extensions.

## 8. Acceptance tests

- [ ] All six `v2` input CSVs exist.
- [ ] Script completes without an exception.
- [ ] Output contains exactly 14 rows.
- [ ] `QUO001` is blocked because it expired.
- [ ] Every output record has a valid requisition, supplier, and product reference.
- [ ] Costs are nonnegative and computed from the quoted quantity and fees.
- [ ] Output contains only `BLOCKED` and `PENDING_REVIEW`, never `APPROVED`.
- [ ] Source `v2` datasets remain unchanged.

## 9. Review questions

1. Why does the system calculate cost using `quoted_quantity` rather than `requested_quantity`?
2. Why is a quotation that passes the implemented checks still labeled `PENDING_REVIEW`?
3. What could go wrong if we evaluated quotation expiry against the computer's current date rather than the simulation date?
4. What additional datasets would be needed to complete weighted scoring under FR-005?

## 10. Next checkpoint

**Checkpoint 2.7 — Supplier Performance & Full Eligibility Data.** Generate quality inspection history, completed delivery history, category approvals, and compliance indicators; calculate evidence-based quality and reliability scores; then complete eligibility before introducing the weighted recommendation engine.
