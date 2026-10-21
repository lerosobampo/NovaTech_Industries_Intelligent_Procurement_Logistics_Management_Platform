# NovaTech Industries — Checkpoint 2.7
## Supplier Performance & Compliance Data Generation

**Project:** Intelligent Procurement & Logistics Management Platform  
**Status:** Implementation exercise  
**Version:** Synthetic dataset v2  
**Reporting date:** 2026-10-21 (fixed for reproducibility)  
**Seed:** 2028

## 1. Objective

Extend the six validated reference and procurement datasets with historical delivery, quality, and supplier-category compliance evidence. This checkpoint **generates evidence only**: it does not approve quotations, compute final weighted supplier scores, or authorize purchase orders.

## 2. Input and output contracts

The generator reads these existing files from `data/synthetic/v2/`:

| Input | Required columns |
|---|---|
| `suppliers.csv` | `supplier_id`, `status` |
| `products.csv` | `product_id`, `category` |
| `supplier_products.csv` | `supplier_id`, `product_id` |

It writes three new files to the **same** directory without modifying the six existing datasets:

| Output | Fields | Expected rows in current v2 |
|---|---|---:|
| `supplier_deliveries.csv` | `delivery_id`, `supplier_id`, `planned_delivery_date`, `actual_delivery_date`, `on_time`, `status` | 177 |
| `supplier_quality_inspections.csv` | `inspection_id`, `supplier_id`, `inspection_date`, `inspected_units`, `accepted_units`, `rejected_units` | 66 |
| `supplier_compliance.csv` | `supplier_id`, `category`, `approval_status`, `valid_until` | 26 |

Compliance has one row per **supplier/category combination** present in `supplier_products.csv`, not one row per supplier.

## 3. Core business concepts

### Reliability

Reliability measures the percentage of completed deliveries arriving on or before their promised date:

`reliability_score = 100 * on_time_completed_deliveries / completed_deliveries`

The generator stores both planned and actual dates, plus a derived `on_time` flag. Future scoring should recompute this flag from dates and check consistency.

### Quality

Quality measures the accepted proportion of inspected units:

`quality_score = 100 * sum(accepted_units) / sum(inspected_units)`

For every inspection, `accepted_units + rejected_units = inspected_units` and all quantities must be nonnegative.

### Compliance

A supplier's approval is **category-specific**. A quotation for a product category requires a matching supplier/category compliance record that is `APPROVED` and unexpired on the evaluation date. A supplier's `ACTIVE` status alone is not sufficient.

### Insufficient history

NovaTech's confirmed policy `DP-006` is to flag insufficient evidence as `REVIEW_REQUIRED` for a Procurement Manager, not to invent quality or reliability scores. For later implementation, proposed (not yet formally approved) thresholds are **100 inspected units** and **10 completed deliveries** within the trailing 12 months. The generator intentionally gives `SUP012` only three deliveries and one small inspection to test this policy.

## 4. Implementation

Save the accompanying Python file at:

`src/data_generation/generate_supplier_performance_v2.py`

From the project root, run:

```bash
python3 src/data_generation/generate_supplier_performance_v2.py
```

Expected output with the existing 12-supplier v2 dataset:

```text
Created supplier_deliveries.csv: 177 records
Created supplier_quality_inspections.csv: 66 records
Created supplier_compliance.csv: 26 records
Validation passed: identifiers, foreign keys, dates, quantities, and compliance categories.
Seed: 2028; reporting date: 2026-10-21; intentional low-history supplier: SUP012
Note: performance and compliance evidence is generated; no supplier score or PO approval is issued.
```

## 5. Practical validation

Check the files:

```bash
ls -lh data/synthetic/v2/supplier_*.csv
head -n 4 data/synthetic/v2/supplier_deliveries.csv
head -n 4 data/synthetic/v2/supplier_quality_inspections.csv
head -n 4 data/synthetic/v2/supplier_compliance.csv
```

Run the generator a second time: because the random seed and reporting date are fixed, the output should be identical.

**Exercise A:** Explain why `supplier_compliance.csv` has more than 12 rows.  
**Exercise B:** Find `SUP012` in deliveries and inspections. Why must it be manually reviewed?  
**Exercise C:** Explain why a supplier can be `ACTIVE` yet not eligible for a particular quotation.  
**Exercise D:** Identify the validation that checks `accepted + rejected = inspected`.

## 6. Quality and limitations

- All generated records are fictional and not evidence of real supplier performance.
- Dates fall in a fixed 12-month reporting window ending 2026-10-21.
- Compliance edge cases include `PENDING` and `EXPIRED` statuses.
- The `on_time` field is derived from dates, not independently sampled.
- The generator validates identifiers, relationships, date ranges, and inspection totals before writing outputs.
- It does not create procurement-specific delivery evidence, exchange-rate evidence, or an audit-ready approval workflow; those belong in later checkpoints.
- The thresholds above are recommendations awaiting a policy decision, not an approved business rule.

## 7. Next checkpoint

**Checkpoint 2.8 — Supplier Performance Metrics & Eligibility Integration:** aggregate trailing-12-month quality/reliability metrics, enforce manual-review flags, and join compliance status with quotation eligibility. Only after validation will we implement the full 40/25/20/15 weighted recommendation model.
