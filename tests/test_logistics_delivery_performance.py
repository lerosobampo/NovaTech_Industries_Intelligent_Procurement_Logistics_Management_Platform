
"""
NovaTech Industries
Logistics Intelligence — Delivery Performance Unit Tests

Tests the delivery performance calculation engine using
controlled synthetic records.

No PostgreSQL connection required.
No database modifications.
"""

import unittest
from datetime import date

from src.analysis.logistics_delivery_performance import (
    calculate_delivery_performance,
)


def make_delivery(
    delivery_id,
    supplier_id,
    planned_date,
    actual_date,
    on_time,
    status="COMPLETED",
):
    """Create a synthetic delivery record."""

    return {
        "delivery_id": delivery_id,
        "supplier_id": supplier_id,
        "planned_delivery_date": planned_date,
        "actual_delivery_date": actual_date,
        "on_time": on_time,
        "status": status,
    }


class TestLogisticsDeliveryPerformance(unittest.TestCase):

    def test_on_time_and_late_deliveries(self):
        deliveries = [
            make_delivery(
                "D001", "SUP001",
                date(2026, 5, 10),
                date(2026, 5, 10),
                True,
            ),
            make_delivery(
                "D002", "SUP001",
                date(2026, 5, 10),
                date(2026, 5, 12),
                False,
            ),
            make_delivery(
                "D003", "SUP001",
                date(2026, 5, 10),
                date(2026, 5, 9),
                True,
            ),
        ]

        results = calculate_delivery_performance(deliveries)
        supplier = results[0]

        self.assertEqual(supplier["completed_deliveries"], 3)
        self.assertEqual(supplier["on_time_deliveries"], 2)
        self.assertEqual(supplier["late_deliveries"], 1)
        self.assertAlmostEqual(
            supplier["on_time_delivery_rate_pct"],
            66.67,
            places=2,
        )
        self.assertAlmostEqual(
            supplier["average_delay_days"],
            0.67,
            places=2,
        )
        self.assertEqual(supplier["maximum_delay_days"], 2)

    def test_early_delivery_has_zero_delay(self):
        deliveries = [
            make_delivery(
                "D004", "SUP002",
                date(2026, 6, 15),
                date(2026, 6, 12),
                True,
            ),
        ]

        supplier = calculate_delivery_performance(deliveries)[0]

        self.assertEqual(supplier["on_time_deliveries"], 1)
        self.assertEqual(supplier["late_deliveries"], 0)
        self.assertEqual(supplier["average_delay_days"], 0)
        self.assertEqual(supplier["maximum_delay_days"], 0)

    def test_inconsistent_on_time_flag(self):
        deliveries = [
            make_delivery(
                "D005", "SUP003",
                date(2026, 7, 10),
                date(2026, 7, 13),
                True,
            ),
            make_delivery(
                "D006", "SUP003",
                date(2026, 7, 10),
                date(2026, 7, 9),
                False,
            ),
        ]

        supplier = calculate_delivery_performance(deliveries)[0]

        self.assertEqual(
            supplier["on_time_flag_mismatches"],
            2,
        )
        self.assertEqual(supplier["on_time_deliveries"], 1)
        self.assertEqual(supplier["late_deliveries"], 1)

    def test_missing_actual_date_excluded(self):
        deliveries = [
            make_delivery(
                "D007", "SUP004",
                date(2026, 8, 10),
                None,
                None,
                "PENDING",
            ),
        ]

        supplier = calculate_delivery_performance(deliveries)[0]

        self.assertEqual(supplier["total_delivery_records"], 1)
        self.assertEqual(supplier["completed_deliveries"], 0)
        self.assertIsNone(
            supplier["on_time_delivery_rate_pct"]
        )
        self.assertIsNone(supplier["average_delay_days"])
        self.assertIsNone(supplier["maximum_delay_days"])

    def test_incomplete_records_not_counted(self):
        deliveries = [
            make_delivery(
                "D008", "SUP005",
                date(2026, 9, 10),
                date(2026, 9, 12),
                False,
                "CANCELLED",
            ),
            make_delivery(
                "D009", "SUP005",
                date(2026, 9, 10),
                date(2026, 9, 10),
                True,
                "COMPLETED",
            ),
        ]

        supplier = calculate_delivery_performance(deliveries)[0]

        self.assertEqual(supplier["total_delivery_records"], 2)
        self.assertEqual(supplier["completed_deliveries"], 1)
        self.assertEqual(supplier["on_time_deliveries"], 1)
        self.assertEqual(supplier["late_deliveries"], 0)

    def test_multiple_suppliers_are_separated(self):
        deliveries = [
            make_delivery(
                "D010", "SUP002",
                date(2026, 10, 10),
                date(2026, 10, 11),
                False,
            ),
            make_delivery(
                "D011", "SUP001",
                date(2026, 10, 10),
                date(2026, 10, 10),
                True,
            ),
        ]

        results = calculate_delivery_performance(deliveries)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["supplier_id"], "SUP001")
        self.assertEqual(results[1]["supplier_id"], "SUP002")
        self.assertEqual(
            results[0]["on_time_delivery_rate_pct"],
            100,
        )
        self.assertEqual(
            results[1]["on_time_delivery_rate_pct"],
            0,
        )

    def test_empty_delivery_list(self):
        results = calculate_delivery_performance([])
        self.assertEqual(results, [])

    def test_missing_flag_not_treated_as_mismatch(self):
        deliveries = [
            make_delivery(
                "D012", "SUP006",
                date(2026, 11, 10),
                date(2026, 11, 10),
                None,
            ),
        ]

        supplier = calculate_delivery_performance(deliveries)[0]

        self.assertEqual(
            supplier["on_time_flag_mismatches"],
            0,
        )
        self.assertEqual(supplier["on_time_deliveries"], 1)

    def test_governance_classification(self):
        deliveries = [
            make_delivery(
                "D013", "SUP007",
                date(2026, 12, 10),
                date(2026, 12, 10),
                True,
            ),
        ]

        supplier = calculate_delivery_performance(deliveries)[0]

        self.assertEqual(
            supplier["evidence_classification"],
            "SYNTHETIC_UNVERIFIED",
        )


if __name__ == "__main__":
    unittest.main()
