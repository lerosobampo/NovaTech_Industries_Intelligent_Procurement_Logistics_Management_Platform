# NovaTech Industries — Checkpoint 2.11
## Point-in-Time Validation and Audit Controls

**Status:** Implementation exercise | **Source baseline:** `evaluate_suppliers_v2.py` | **New engine:** `evaluate_suppliers_v3.py`

### 1. Objective
Prevent look-ahead bias when comparing historical supplier quotations. Preserve the Checkpoint 2.9 engine and its 13 passing tests. Generate a separate v3 evaluation report with the cutoff date, evidence counts, review reasons, and approval restrictions.

### 2. What we found in v2
The original engine loads `supplier_performance_metrics.csv` and `supplier_category_compliance.csv` as precomputed snapshots. It compares the requisition request date to `report_as_of`, but this cannot establish whether each inspection, delivery, or compliance approval existed on the earlier date. Its cost/delivery normalization and weighted ranking logic are retained in v3.

### 3. Point-in-time design
- **Cutoff proxy:** For each requisition, use the latest quotation date in that requisition's evaluated set. This creates a consistent comparison cutoff. It is **not** proof of the actual decision timestamp.
- **Quality:** Include only inspections in the preceding 365 days and on or before the cutoff. `100 × accepted / inspected`.
- **Reliability:** Include only completed/delivered shipments whose **actual delivery date** is in the preceding 365 days and on or before the cutoff. `100 × on-time / completed`.
- **Evidence thresholds:** At least 100 inspected units and 10 completed deliveries. These remain proposed, configurable business policies.
- **Compliance:** A valid-until date and present approval status alone cannot prove historical approval. Without `approved_on` and `status_as_of`, mark `REVIEW_REQUIRED`.
- **Preliminary eligibility:** The v2 quotation eligibility output lacks historical provenance for supplier status, inventory, and quote-state checks. V3 flags `PRELIMINARY_ELIGIBILITY_PROVENANCE_MISSING`, even for quotations that were previously pending review.
- **No silent approval:** Only `ELIGIBLE_FOR_ANALYSIS` quotations can be normalized and ranked; `REVIEW_REQUIRED` and `BLOCKED` are not ranked. No purchase order is authorized automatically.

### 4. Project files

```text
src/analysis/evaluate_suppliers_v2.py       # unchanged baseline
src/analysis/evaluate_suppliers_v3.py       # new engine
tests/test_supplier_evaluation_v2.py        # unchanged 13-test baseline
tests/test_point_in_time_v3.py              # 8 new unit tests
data/analysis/v3/supplier_evaluation_results.csv  # new report
```

### 5. Installation
1. Copy `evaluate_suppliers_v3.py` to `src/analysis/`.
2. Copy `test_point_in_time_v3.py` to `tests/`.
3. Save this guide and its PDF to `docs/data/`.

```bash
cd ~/Documents/Projects/ai-procurement-platform
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 src/analysis/evaluate_suppliers_v3.py
head -n 3 data/analysis/v3/supplier_evaluation_results.csv
```

The new eight tests should pass in addition to the previous thirteen, assuming those files are unchanged. The script prints counts derived from **your** datasets; do not assume v2's 10 eligible and five top-ranked results will recur. The conservative v3 rules may produce zero eligible or top-ranked quotations until historical evidence is added. This is an expected safety behavior, not a software failure.

### 6. Validation exercises
1. Inspect one supplier's `inspected_units` and `completed_deliveries` at the cutoff; compare with its later v2 performance snapshot.
2. Confirm no inspection or completed delivery after `evaluation_as_of` affects the historical scores.
3. Confirm expired compliance is blocked; approved compliance with missing start-date provenance requires review.
4. Confirm no quotation marked `REVIEW_REQUIRED` receives a weighted score or `TOP_RANKED_PENDING_HUMAN_APPROVAL`.
5. Confirm the original v2 results and thirteen tests are unchanged.

### 7. Known limitations and next checkpoint
This implementation uses a **latest quotation date proxy** because there is no authoritative procurement evaluation event timestamp. It also cannot reconstruct historical supplier status, stock, or quotation changes from current-state datasets. Compliance fields `approved_on` and `status_as_of` are optional future extensions; the existing v2 CSV does not contain them. `status_as_of` should eventually come from a real dated compliance event log, not a current snapshot. Future work: introduce an immutable procurement decision event, effective-dated supplier/compliance histories, and historically versioned quotation eligibility; then remove the blanket provenance-review flag only when the evidence is truly available.

**Learning takeaway:** A calculation can be mathematically correct yet historically invalid. A safe decision engine must establish what was knowable at the time, and flag missing evidence instead of inventing certainty.
