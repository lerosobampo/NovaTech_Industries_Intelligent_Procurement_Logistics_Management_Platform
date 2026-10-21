# NovaTech Industries — Checkpoint 2.10
## Automated Testing & Quality Assurance

**Project:** Intelligent Procurement & Logistics Management Platform  
**Phase:** Supplier Evaluation Engine — Quality Assurance  
**Target environment:** Python 3.12; standard library only

### Objective
Verify the Checkpoint 2.9 evaluation engine with isolated, repeatable tests. The test suite creates temporary CSV fixtures, calls the real evaluation module, and checks outputs. It never changes the project's `data/synthetic/v2/` or `data/analysis/v2/` files.

### Installation
1. Save `test_supplier_evaluation_v2.py` in the project's `tests/` directory.
2. Confirm `src/analysis/evaluate_suppliers_v2.py` is the Checkpoint 2.9 engine.
3. From the project root, run:

```bash
mkdir -p tests
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

**Reference validation:** 13 tests executed successfully against the Checkpoint 2.9 script in an isolated environment. Your results may differ if you modified the engine.

### Tests included

| Test | Purpose |
|---|---|
| Eligible quotes and ranking | Check eligible status and top-ranked result |
| Weighted scores and normalization | Verify 40/25/20/15 weights and group-relative cost/lead normalization |
| Preliminary block | Preserve upstream block reason, e.g. quotation expired |
| Invalid compliance | Block nonvalid category compliance |
| Insufficient history | Require review; leave score empty |
| Missing performance record | Reject broken foreign key |
| Duplicate quotation ID | Reject duplicate identifiers |
| Invalid total cost | Reject zero/nonpositive cost |
| Invalid quality | Reject score above 100 |
| Reporting-date mismatch | Reject inconsistent performance/compliance snapshot dates |
| Report predates request | Verify current engine's explicit block rule |
| Exact tie | Deterministic tie-break on quotation ID |
| No automatic approval | Verify ranking never authorizes a purchase |

### How the test harness works
- `unittest.TestCase.setUp` builds an independent temporary project directory.
- CSV fixtures represent two suppliers quoting the same requisition.
- `unittest.mock.patch.object` points the imported engine at those temporary files.
- Each test changes only its own fixture and calls `engine.main()`.
- Assertions check output rows or expected validation errors.

### Example score calculation
Supplier S1: cost EUR 120, lead time 5 days, quality 98, reliability 96.  
Supplier S2: cost EUR 100, lead time 10 days, quality 92, reliability 84.

For S1, cost score = 100 × 100/120 = 83.333..., delivery score = 100.  
Weighted score = 0.40 × 83.333... + 0.25 × 100 + 0.20 × 98 + 0.15 × 96 = **92.33**.

For S2, cost score = 100, delivery score = 50.  
Weighted score = 0.40 × 100 + 0.25 × 50 + 0.20 × 92 + 0.15 × 84 = **83.50**.

The recommendation remains **pending human approval**.

### Important limitations and next improvements
1. **Point-in-time evidence:** The existing engine checks whether a performance report predates a requisition, but this does not guarantee that all source events were known by the procurement decision date. A production system needs event-level cutoff logic and an explicit evaluation timestamp.
2. **Upstream checks:** Expiry and inactive-supplier rules are implemented upstream. This suite tests that the evaluation engine respects an upstream `BLOCKED` result; it does not independently retest the upstream eligibility module.
3. **Policy approval:** Evidence thresholds, tie-breaking, and evaluation date rules must be formally approved before production use.
4. **Synthetic data:** Tests use controlled fixtures, not actual suppliers or transactions.
5. **Data persistence:** The current workflow uses CSV files. Later phases should introduce database constraints, transactional updates, and audit logs.

### Practical exercise
1. Run the 13 tests and record the output.
2. Change the S1 quality score in `test_weighted_scores_and_normalization`'s fixture (not in production data) and see which assertion fails.
3. Restore the original value and rerun the suite.
4. Explain why an expired quotation cannot win even if its weighted score would be highest.

### Acceptance criteria
- All 13 tests pass.
- Existing project CSV files remain unchanged.
- A quotation with insufficient history is marked `REVIEW_REQUIRED` with no weighted score.
- A blocked quotation is never ranked.
- No quotation is automatically approved.

**Next checkpoint:** 2.11 — Point-in-Time Evidence Controls & Expanded Integration Testing.
