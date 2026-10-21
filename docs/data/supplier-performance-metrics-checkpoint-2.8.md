# NovaTech Industries — Checkpoint 2.8
## Supplier Performance Metrics & Category Compliance

**Status:** Implementation exercise | **Data version:** v2 | **Reporting date:** 2026-10-21

### Learning objectives
- Aggregate historical transactions into supplier-level quality and reliability indicators.
- Use a fixed 12-month reporting window and explicit denominators.
- Flag insufficient evidence instead of inventing scores.
- Keep category-specific compliance separate from supplier-wide performance.
- Validate input data and produce auditable CSV outputs.

### Confirmed source schemas
- `suppliers.csv`: `supplier_id, supplier_name, country, status` (12 rows)
- `products.csv`: `product_id, sku, product_name, category, unit_of_measure` (20 rows)
- `supplier_products.csv`: `supplier_id, product_id, minimum_order_quantity, available_quantity` (45 rows)
- `supplier_deliveries.csv`: `delivery_id, supplier_id, planned_delivery_date, actual_delivery_date, on_time, status` (177 rows)
- `supplier_quality_inspections.csv`: `inspection_id, supplier_id, inspection_date, inspected_units, accepted_units, rejected_units` (66 rows)
- `supplier_compliance.csv`: `supplier_id, category, approval_status, valid_until` (26 rows)

### Metric definitions
Only events dated between **2025-10-21 and 2026-10-21**, inclusive, count. Completed deliveries use **actual delivery date**; inspections use **inspection date**.

- **Quality (%)** = 100 × accepted units / inspected units.
- **Reliability (%)** = 100 × on-time completed deliveries / completed deliveries.
- **On time** = actual delivery date on or before planned delivery date.
- **Proposed evidence policy:** at least 100 inspected units AND at least 10 completed deliveries. These are *proposed, configurable thresholds*, not yet formally approved.
- **Evidence status:** `EVIDENCE_SUFFICIENT` or `REVIEW_REQUIRED`. Missing-evidence scores are blank rather than estimated. Each score is independently withheld when its own evidence threshold is unmet.
- **Compliance:** evaluate the supplier for each product category it actually supplies. `VALID` means an approved/active compliance record with an unexpired `valid_until`; otherwise `REVIEW_REQUIRED` or `MISSING`. A compliance status is **not** a purchasing authorization.

### Save and execute
1. Save `analyze_supplier_performance_v2.py` to `src/analysis/analyze_supplier_performance_v2.py`.
2. From the project root, run:

```bash
mkdir -p src/analysis
python3 src/analysis/analyze_supplier_performance_v2.py
```

The script reads from `data/synthetic/v2/` and writes to `data/analysis/v2/`:
- `supplier_performance_metrics.csv`: one row per supplier (expected **12**).
- `supplier_category_compliance.csv`: one row per supplier-category combination, count dependent on actual relationships.

The input datasets are never overwritten. The generator is deterministic for a fixed input and reporting date.

### Validation exercise
```bash
python3 - <<'PY'
import csv
from pathlib import Path
base = Path('data/analysis/v2')
for filename in ['supplier_performance_metrics.csv', 'supplier_category_compliance.csv']:
    with (base / filename).open(newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    print(filename, 'rows:', len(rows))
    print('first record:', rows[0] if rows else '(empty)')
PY
```

Check `SUP012` for low-history behavior. Confirm that scores are blank when evidence is insufficient. Inspect the category compliance output: missing, expired, or pending approval must not be labeled valid.

### Important design limits
- **No full quotation eligibility or weighted ranking yet.** This checkpoint creates evidence used by a later integration step.
- Status values are normalized case-insensitively. Completed deliveries are identified by `completed` or `delivered`; other statuses are excluded.
- The script checks that reported on-time flags agree with actual/planned dates; inconsistent synthetic records raise an explicit error for investigation.
- The category compliance logic recognizes `approved` or `active` as affirmative approval values. Verify this assumption against the generator's actual statuses before relying on results.
- A supplier may have adequate history yet still be inactive or noncompliant. Those checks must remain separate.

### Next checkpoint
**2.9 — Integrate supplier performance, category compliance, and quotation eligibility**, then implement cost and lead-time normalization and the 40/25/20/15 scoring formula only for fully eligible offers.
