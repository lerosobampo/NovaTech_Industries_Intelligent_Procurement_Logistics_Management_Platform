"""Checkpoint 2.12 unit tests. Run with unittest discovery."""
import importlib.util
import unittest
from datetime import date
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "src" / "analysis" / "evaluate_suppliers_v4.py"
spec = importlib.util.spec_from_file_location("evaluate_suppliers_v4", MODULE)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)


def record(**updates):
    base = {"effective_from": "2026-01-01", "effective_to": "",
            "recorded_at": "2026-01-02",
            "evidence_source": "SYNTHETIC_ASSUMPTION_FROM_V3_SNAPSHOT"}
    base.update(updates)
    return base


class HistoricalEvidenceTests(unittest.TestCase):
    def test_synthetic_record_is_not_verified(self):
        row, reason = engine.history_at([record()], date(2026, 10, 16), "SUP001", "STATUS")
        self.assertIsNotNone(row)
        self.assertEqual(reason, "STATUS_SYNTHETIC_OR_UNVERIFIED")

    def test_not_yet_effective(self):
        row, reason = engine.history_at([record(effective_from="2026-11-01")],
                                        date(2026, 10, 16), "SUP001", "STATUS")
        self.assertIsNone(row)
        self.assertEqual(reason, "STATUS_HISTORY_MISSING")

    def test_not_yet_recorded(self):
        row, reason = engine.history_at([record(recorded_at="2026-11-01")],
                                        date(2026, 10, 16), "SUP001", "STATUS")
        self.assertIsNone(row)
        self.assertEqual(reason, "STATUS_HISTORY_MISSING")

    def test_effective_to_is_exclusive(self):
        row, _ = engine.history_at([record(effective_to="2026-10-16")],
                                   date(2026, 10, 16), "SUP001", "STATUS")
        self.assertIsNone(row)

    def test_latest_record_wins(self):
        old = record(status="ACTIVE")
        new = record(status="SUSPENDED", effective_from="2026-10-01",
                     recorded_at="2026-10-02")
        row, _ = engine.history_at([old, new], date(2026, 10, 16), "SUP001", "STATUS")
        self.assertEqual(row["status"], "SUSPENDED")

    def test_ambiguous_history_fails(self):
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            engine.history_at([record(), record()], date(2026, 10, 16), "SUP001", "STATUS")

    def test_bad_effective_interval_fails(self):
        with self.assertRaisesRegex(ValueError, "invalid effective interval"):
            engine.history_at([record(effective_to="2026-01-01")],
                              date(2026, 10, 16), "SUP001", "STATUS")

    def test_non_synthetic_label_not_auto_verified(self):
        row, reason = engine.history_at(
            [record(evidence_source="ERP_EXPORT")], date(2026, 10, 16), "SUP001", "STATUS")
        self.assertIsNotNone(row)
        self.assertEqual(reason, "STATUS_SOURCE_NOT_INDEPENDENTLY_VERIFIED")


if __name__ == "__main__":
    unittest.main()
