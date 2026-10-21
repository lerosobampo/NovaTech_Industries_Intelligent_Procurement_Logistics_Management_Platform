"""Checkpoint 2.10: isolated integration tests for the Checkpoint 2.9 engine.
Run: python3 -m unittest discover -s tests -p 'test_*.py' -v
"""
import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
ENGINE_FILE = ROOT / 'src' / 'analysis' / 'evaluate_suppliers_v2.py'
spec = importlib.util.spec_from_file_location('supplier_engine_under_test', ENGINE_FILE)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)


def save_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class SupplierEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.data = self.root / 'data' / 'synthetic' / 'v2'
        self.analysis = self.root / 'data' / 'analysis' / 'v2'
        self.patches = [patch.object(engine, 'ROOT', self.root), patch.object(engine, 'DATA', self.data), patch.object(engine, 'ANALYSIS', self.analysis)]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)
        self.quotes = [
            dict(quotation_id='Q1', requisition_id='R1', supplier_id='S1', product_id='P1', total_cost_eur='120', preliminary_status='PENDING_REVIEW', reasons=''),
            dict(quotation_id='Q2', requisition_id='R1', supplier_id='S2', product_id='P1', total_cost_eur='100', preliminary_status='PENDING_REVIEW', reasons=''),
        ]
        self.perf = [
            dict(supplier_id='S1', quality_score='98', reliability_score='96', evidence_status='EVIDENCE_SUFFICIENT', report_as_of='2026-10-21'),
            dict(supplier_id='S2', quality_score='92', reliability_score='84', evidence_status='EVIDENCE_SUFFICIENT', report_as_of='2026-10-21'),
        ]
        self.comp = [
            dict(supplier_id='S1', category='Electrical', compliance_status='VALID', report_as_of='2026-10-21'),
            dict(supplier_id='S2', category='Electrical', compliance_status='VALID', report_as_of='2026-10-21'),
        ]
        self.items = [dict(quotation_id='Q1', lead_time_days='5'), dict(quotation_id='Q2', lead_time_days='10')]
        self.requests = [dict(requisition_id='R1', request_date='2026-10-15')]
        self.flush()

    def flush(self):
        save_csv(self.analysis / 'quotation_eligibility_results.csv', self.quotes)
        save_csv(self.analysis / 'supplier_performance_metrics.csv', self.perf)
        save_csv(self.analysis / 'supplier_category_compliance.csv', self.comp)
        save_csv(self.data / 'products.csv', [dict(product_id='P1', category='Electrical')])
        save_csv(self.data / 'quotation_items.csv', self.items)
        save_csv(self.data / 'purchase_requisitions.csv', self.requests)

    def run_engine(self):
        self.flush()
        engine.main()
        with (self.analysis / 'supplier_evaluation_results.csv').open(newline='', encoding='utf-8') as f:
            return {r['quotation_id']: r for r in csv.DictReader(f)}

    def test_eligible_quotes_and_ranking(self):
        result = self.run_engine()
        self.assertEqual(len(result), 2)
        self.assertTrue(all(r['evaluation_status'] == 'ELIGIBLE_FOR_ANALYSIS' for r in result.values()))
        self.assertEqual(result['Q1']['recommendation_status'], 'TOP_RANKED_PENDING_HUMAN_APPROVAL')
        self.assertEqual(result['Q2']['recommendation_status'], 'RANKED_ALTERNATIVE')

    def test_weighted_scores_and_normalization(self):
        result = self.run_engine()
        # Q1: cost 100*100/120, lead 100; Q2: cost 100, lead 50.
        self.assertAlmostEqual(float(result['Q1']['cost_score']), 83.33, places=2)
        self.assertEqual(result['Q1']['delivery_score'], '100.00')
        self.assertAlmostEqual(float(result['Q1']['weighted_score']), 92.33, places=2)
        self.assertAlmostEqual(float(result['Q2']['weighted_score']), 83.50, places=2)

    def test_expired_or_other_preliminary_block(self):
        self.quotes[0]['preliminary_status'] = 'BLOCKED'
        self.quotes[0]['reasons'] = 'QUOTATION_EXPIRED'
        result = self.run_engine()
        self.assertEqual(result['Q1']['evaluation_status'], 'BLOCKED')
        self.assertIn('QUOTATION_EXPIRED', result['Q1']['reasons'])
        self.assertEqual(result['Q1']['weighted_score'], '')

    def test_invalid_compliance_blocks(self):
        self.comp[0]['compliance_status'] = 'EXPIRED'
        result = self.run_engine()
        self.assertEqual(result['Q1']['evaluation_status'], 'BLOCKED')
        self.assertIn('CATEGORY_COMPLIANCE_NOT_VALID', result['Q1']['reasons'])

    def test_insufficient_history_requires_review(self):
        self.perf[0]['evidence_status'] = 'REVIEW_REQUIRED'
        self.perf[0]['quality_score'] = ''
        self.perf[0]['reliability_score'] = ''
        result = self.run_engine()
        self.assertEqual(result['Q1']['evaluation_status'], 'REVIEW_REQUIRED')
        self.assertIn('INSUFFICIENT_PERFORMANCE_HISTORY', result['Q1']['reasons'])
        self.assertEqual(result['Q1']['weighted_score'], '')

    def test_missing_supplier_performance_fails(self):
        self.perf.pop(0)
        with self.assertRaisesRegex(ValueError, 'missing required foreign key'):
            self.run_engine()

    def test_duplicate_quotation_id_fails(self):
        self.quotes.append(self.quotes[0].copy())
        with self.assertRaisesRegex(ValueError, 'duplicate key'):
            self.run_engine()

    def test_invalid_cost_fails(self):
        self.quotes[0]['total_cost_eur'] = '0'
        with self.assertRaisesRegex(ValueError, 'out of range'):
            self.run_engine()

    def test_invalid_quality_fails(self):
        self.perf[0]['quality_score'] = '105'
        with self.assertRaisesRegex(ValueError, 'exceeds 100'):
            self.run_engine()

    def test_reporting_date_mismatch_fails(self):
        self.comp[0]['report_as_of'] = '2026-10-20'
        with self.assertRaisesRegex(ValueError, 'incompatible'):
            self.run_engine()

    def test_report_before_request_blocks(self):
        self.requests[0]['request_date'] = '2026-10-22'
        result = self.run_engine()
        self.assertTrue(all(r['evaluation_status'] == 'BLOCKED' for r in result.values()))
        self.assertIn('PERFORMANCE_REPORT_PREDATES_REQUEST', result['Q1']['reasons'])

    def test_exact_tie_uses_quote_id(self):
        self.quotes[1]['total_cost_eur'] = self.quotes[0]['total_cost_eur']
        self.items[1]['lead_time_days'] = self.items[0]['lead_time_days']
        self.perf[1]['quality_score'] = self.perf[0]['quality_score']
        self.perf[1]['reliability_score'] = self.perf[0]['reliability_score']
        result = self.run_engine()
        self.assertEqual(result['Q1']['recommendation_status'], 'TOP_RANKED_PENDING_HUMAN_APPROVAL')

    def test_no_automatic_approval(self):
        result = self.run_engine()
        self.assertNotIn('APPROVED', {r['recommendation_status'] for r in result.values()})


if __name__ == '__main__':
    unittest.main()
