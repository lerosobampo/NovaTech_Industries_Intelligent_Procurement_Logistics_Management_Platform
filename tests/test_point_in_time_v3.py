"""Unit tests for Checkpoint 2.11. Run with unittest discovery."""
import importlib.util
import unittest
from datetime import date
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'src' / 'analysis' / 'evaluate_suppliers_v3.py'
spec = importlib.util.spec_from_file_location('evaluation_v3', SCRIPT)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)


class PointInTimeTests(unittest.TestCase):
    def test_future_inspection_excluded(self):
        rows = [{'supplier_id':'SUP001','inspection_id':'I1','inspection_date':'2026-10-20',
                 'inspected_units':'200','accepted_units':'198','rejected_units':'2'}]
        m = engine.performance_at('SUP001', date(2026,10,15), [], rows)
        self.assertEqual(m['inspected_units'], 0)
        self.assertIsNone(m['quality_score'])

    def test_inspection_at_cutoff_included(self):
        rows = [{'supplier_id':'SUP001','inspection_id':'I1','inspection_date':'2026-10-15',
                 'inspected_units':'100','accepted_units':'95','rejected_units':'5'}]
        m = engine.performance_at('SUP001', date(2026,10,15), [], rows)
        self.assertEqual(m['inspected_units'], 100)
        self.assertEqual(m['quality_score'], 95)

    def test_future_delivery_excluded(self):
        rows = [{'supplier_id':'SUP001','delivery_id':'D1','planned_delivery_date':'2026-10-19',
                 'actual_delivery_date':'2026-10-20','on_time':'false','status':'COMPLETED'}]
        m = engine.performance_at('SUP001', date(2026,10,15), rows, [])
        self.assertEqual(m['completed_deliveries'], 0)

    def test_missing_compliance_start_requires_review(self):
        row = {'approval_status':'APPROVED','valid_until':'2027-01-01'}
        self.assertEqual(engine.compliance_at(row, date(2026,10,15))[0], 'REVIEW_REQUIRED')

    def test_expired_compliance_blocked(self):
        row = {'approval_status':'APPROVED','valid_until':'2026-10-14'}
        self.assertEqual(engine.compliance_at(row, date(2026,10,15))[0], 'BLOCKED')

    def test_valid_provenance(self):
        row = {'approval_status':'APPROVED','valid_until':'2027-01-01',
               'approved_on':'2026-01-01','status_as_of':'2026-10-15'}
        self.assertEqual(engine.compliance_at(row, date(2026,10,15))[0], 'VALID')

    def test_future_provenance_requires_review(self):
        row = {'approval_status':'APPROVED','valid_until':'2027-01-01',
               'approved_on':'2026-10-16','status_as_of':'2026-10-16'}
        self.assertEqual(engine.compliance_at(row, date(2026,10,15))[0], 'REVIEW_REQUIRED')

    def test_inconsistent_inspection_rejected(self):
        rows = [{'supplier_id':'SUP001','inspection_id':'I1','inspection_date':'2026-10-15',
                 'inspected_units':'100','accepted_units':'90','rejected_units':'9'}]
        with self.assertRaises(ValueError):
            engine.performance_at('SUP001', date(2026,10,15), [], rows)


if __name__ == '__main__':
    unittest.main()
