
"""
NovaTech Industries
Logistics Intelligence — Shipment Monitoring Tests

Tests:
- Active shipment monitoring
- Overdue shipment detection
- On-time and late delivery performance
- Carrier-level performance
- Shipment exceptions and alerts
- Data-quality safeguards
- Simulation governance
- Empty datasets
- Database loader integration (mocked)

No PostgreSQL records are created or modified.
"""

import unittest
from datetime import date, datetime
from unittest.mock import patch

from src.analysis.shipment_monitoring import (
    calculate_shipment_monitoring,
    generate_shipment_monitoring,
)


AS_OF_DATE = date(2026, 10, 21)


def make_shipment(
    shipment_id,
    status="CREATED",
    carrier="Demo Carrier",
    estimated_delivery=date(2026, 10, 25),
    actual_delivery=None,
    dispatch_date=None,
    supplier_id="SUP001",
    **overrides,
):
    """Build a synthetic shipment with valid governance metadata."""

    shipment = {
        "shipment_id": shipment_id,
        "supplier_id": supplier_id,
        "tracking_number": f"TRACK-{shipment_id}",
        "carrier_name": carrier,
        "transport_mode": "ROAD",
        "origin_location": "Rotterdam",
        "destination_location": "The Hague",
        "dispatch_date": dispatch_date,
        "estimated_delivery_date": estimated_delivery,
        "actual_delivery_date": actual_delivery,
        "shipment_status": status,
        "simulation_mode": "SIMULATION",
        "evidence_classification": "SYNTHETIC_UNVERIFIED",
        "authorization_status": "NOT_AUTHORIZED",
    }

    shipment.update(overrides)
    return shipment


class TestShipmentMonitoring(unittest.TestCase):

    def test_empty_dataset(self):
        result = calculate_shipment_monitoring(
            [],
            as_of_date=AS_OF_DATE,
        )

        self.assertEqual(result["kpis"]["total_shipments"], 0)
        self.assertEqual(result["kpis"]["active_shipments"], 0)
        self.assertEqual(result["kpis"]["overdue_shipments"], 0)
        self.assertEqual(result["kpis"]["evaluated_deliveries"], 0)
        self.assertEqual(result["kpis"]["data_quality_issues"], 0)
        self.assertEqual(result["carrier_performance"], [])

    def test_active_shipments(self):
        shipments = [
            make_shipment(
                "SHP001",
                status="DISPATCHED",
                dispatch_date=date(2026, 10, 20),
            ),
            make_shipment(
                "SHP002",
                status="IN_TRANSIT",
                dispatch_date=date(2026, 10, 20),
            ),
            make_shipment("SHP003", status="CREATED"),
        ]

        result = calculate_shipment_monitoring(
            shipments,
            as_of_date=AS_OF_DATE,
        )

        self.assertEqual(result["kpis"]["total_shipments"], 3)
        self.assertEqual(result["kpis"]["active_shipments"], 2)
        self.assertEqual(result["kpis"]["open_shipments"], 3)
        self.assertEqual(len(result["active_shipments"]), 2)

    def test_overdue_shipments(self):
        shipments = [
            make_shipment(
                "SHP001",
                status="IN_TRANSIT",
                estimated_delivery=date(2026, 10, 18),
                dispatch_date=date(2026, 10, 15),
            ),
            make_shipment(
                "SHP002",
                status="CREATED",
                estimated_delivery=date(2026, 10, 20),
            ),
            make_shipment(
                "SHP003",
                status="IN_TRANSIT",
                estimated_delivery=date(2026, 10, 25),
                dispatch_date=date(2026, 10, 20),
            ),
        ]

        result = calculate_shipment_monitoring(
            shipments,
            as_of_date=AS_OF_DATE,
        )

        self.assertEqual(result["kpis"]["overdue_shipments"], 2)

        overdue = result["overdue_shipments"]

        self.assertEqual(overdue[0]["shipment_id"], "SHP001")
        self.assertEqual(overdue[0]["days_overdue"], 3)
        self.assertEqual(overdue[1]["days_overdue"], 1)

        self.assertEqual(result["kpis"]["operational_alerts"], 2)

    def test_on_time_delivery(self):
        shipments = [
            make_shipment(
                "SHP001",
                status="DELIVERED",
                estimated_delivery=date(2026, 10, 20),
                actual_delivery=date(2026, 10, 20),
                dispatch_date=date(2026, 10, 18),
            ),
            make_shipment(
                "SHP002",
                status="DELIVERED",
                estimated_delivery=date(2026, 10, 20),
                actual_delivery=date(2026, 10, 19),
                dispatch_date=date(2026, 10, 17),
            ),
        ]

        result = calculate_shipment_monitoring(
            shipments,
            as_of_date=AS_OF_DATE,
        )

        kpis = result["kpis"]

        self.assertEqual(kpis["delivered_shipments"], 2)
        self.assertEqual(kpis["evaluated_deliveries"], 2)
        self.assertEqual(kpis["on_time_deliveries"], 2)
        self.assertEqual(kpis["late_deliveries"], 0)
        self.assertEqual(kpis["on_time_delivery_rate_pct"], 100.0)
        self.assertEqual(kpis["average_delay_days"], 0.0)

    def test_late_delivery(self):
        shipments = [
            make_shipment(
                "SHP001",
                status="DELIVERED",
                estimated_delivery=date(2026, 10, 18),
                actual_delivery=date(2026, 10, 21),
                dispatch_date=date(2026, 10, 15),
            ),
            make_shipment(
                "SHP002",
                status="DELIVERED",
                estimated_delivery=date(2026, 10, 20),
                actual_delivery=date(2026, 10, 20),
                dispatch_date=date(2026, 10, 18),
            ),
        ]

        result = calculate_shipment_monitoring(
            shipments,
            as_of_date=AS_OF_DATE,
        )

        kpis = result["kpis"]

        self.assertEqual(kpis["on_time_deliveries"], 1)
        self.assertEqual(kpis["late_deliveries"], 1)
        self.assertEqual(kpis["on_time_delivery_rate_pct"], 50.0)
        self.assertEqual(kpis["average_delay_days"], 1.5)

    def test_carrier_performance(self):
        shipments = [
            make_shipment(
                "SHP001",
                status="DELIVERED",
                carrier="Carrier A",
                estimated_delivery=date(2026, 10, 20),
                actual_delivery=date(2026, 10, 20),
                dispatch_date=date(2026, 10, 18),
            ),
            make_shipment(
                "SHP002",
                status="DELIVERED",
                carrier="Carrier A",
                estimated_delivery=date(2026, 10, 19),
                actual_delivery=date(2026, 10, 21),
                dispatch_date=date(2026, 10, 17),
            ),
            make_shipment(
                "SHP003",
                status="IN_TRANSIT",
                carrier="Carrier B",
                dispatch_date=date(2026, 10, 20),
            ),
        ]

        result = calculate_shipment_monitoring(
            shipments,
            as_of_date=AS_OF_DATE,
        )

        carriers = {
            item["carrier_name"]: item
            for item in result["carrier_performance"]
        }

        self.assertEqual(
            carriers["Carrier A"]["completed_deliveries"],
            2,
        )
        self.assertEqual(
            carriers["Carrier A"]["on_time_rate_pct"],
            50.0,
        )
        self.assertEqual(
            carriers["Carrier A"]["average_delay_days"],
            1.0,
        )
        self.assertEqual(
            carriers["Carrier B"]["active_shipments"],
            1,
        )
        self.assertEqual(
            carriers["Carrier B"]["evaluated_deliveries"],
            0,
        )

    def test_exception_alert(self):
        shipments = [
            make_shipment(
                "SHP001",
                status="EXCEPTION",
                dispatch_date=date(2026, 10, 19),
            ),
        ]

        result = calculate_shipment_monitoring(
            shipments,
            as_of_date=AS_OF_DATE,
        )

        self.assertEqual(result["kpis"]["exception_shipments"], 1)
        self.assertEqual(result["kpis"]["operational_alerts"], 1)
        self.assertEqual(
            result["alerts"][0]["alert_type"],
            "SHIPMENT_EXCEPTION",
        )

    def test_overdue_exception_generates_two_alerts(self):
        shipments = [
            make_shipment(
                "SHP001",
                status="EXCEPTION",
                estimated_delivery=date(2026, 10, 18),
                dispatch_date=date(2026, 10, 15),
            ),
        ]

        result = calculate_shipment_monitoring(
            shipments,
            as_of_date=AS_OF_DATE,
        )

        self.assertEqual(result["kpis"]["overdue_shipments"], 1)
        self.assertEqual(result["kpis"]["exception_shipments"], 1)
        self.assertEqual(result["kpis"]["operational_alerts"], 2)

    def test_missing_dispatch_date(self):
        shipments = [
            make_shipment(
                "SHP001",
                status="IN_TRANSIT",
                dispatch_date=None,
            ),
        ]

        result = calculate_shipment_monitoring(
            shipments,
            as_of_date=AS_OF_DATE,
        )

        issues = result["data_quality_issues"]

        self.assertEqual(len(issues), 1)
        self.assertEqual(
            issues[0]["issue_type"],
            "MISSING_DISPATCH_DATE",
        )

    def test_missing_delivery_date(self):
        shipments = [
            make_shipment(
                "SHP001",
                status="DELIVERED",
                actual_delivery=None,
                dispatch_date=date(2026, 10, 18),
            ),
        ]

        result = calculate_shipment_monitoring(
            shipments,
            as_of_date=AS_OF_DATE,
        )

        issue_types = {
            item["issue_type"]
            for item in result["data_quality_issues"]
        }

        self.assertIn("MISSING_ACTUAL_DELIVERY", issue_types)
        self.assertEqual(
            result["kpis"]["evaluated_deliveries"],
            0,
        )

    def test_governance_mismatch(self):
        shipments = [
            make_shipment(
                "SHP001",
                authorization_status="AUTHORIZED",
            ),
        ]

        result = calculate_shipment_monitoring(
            shipments,
            as_of_date=AS_OF_DATE,
        )

        issues = result["data_quality_issues"]

        self.assertEqual(len(issues), 1)
        self.assertEqual(
            issues[0]["issue_type"],
            "GOVERNANCE_MISMATCH",
        )

    def test_invalid_delivery_sequence(self):
        shipments = [
            make_shipment(
                "SHP001",
                status="DELIVERED",
                dispatch_date=date(2026, 10, 20),
                estimated_delivery=date(2026, 10, 25),
                actual_delivery=date(2026, 10, 19),
            ),
        ]

        result = calculate_shipment_monitoring(
            shipments,
            as_of_date=AS_OF_DATE,
        )

        issue_types = {
            item["issue_type"]
            for item in result["data_quality_issues"]
        }

        self.assertIn("INVALID_DELIVERY_SEQUENCE", issue_types)

    def test_cancelled_shipments_not_overdue(self):
        shipments = [
            make_shipment(
                "SHP001",
                status="CANCELLED",
                estimated_delivery=date(2026, 10, 15),
            ),
        ]

        result = calculate_shipment_monitoring(
            shipments,
            as_of_date=AS_OF_DATE,
        )

        self.assertEqual(result["kpis"]["cancelled_shipments"], 1)
        self.assertEqual(result["kpis"]["overdue_shipments"], 0)

    def test_as_of_date_validation(self):
        with self.assertRaises(ValueError):
            calculate_shipment_monitoring(
                [],
                as_of_date="2026-10-21",
            )

        with self.assertRaises(ValueError):
            calculate_shipment_monitoring(
                [],
                as_of_date=datetime(2026, 10, 21, 12, 0),
            )

    def test_generate_monitoring_uses_database_loader(self):
        shipments = [
            make_shipment(
                "SHP001",
                status="IN_TRANSIT",
                dispatch_date=date(2026, 10, 20),
            ),
        ]

        with patch(
            "src.analysis.shipment_monitoring.list_shipments",
            return_value=shipments,
        ) as mocked_loader:
            result = generate_shipment_monitoring(
                as_of_date=AS_OF_DATE,
            )

        mocked_loader.assert_called_once_with()
        self.assertEqual(result["kpis"]["total_shipments"], 1)
        self.assertEqual(result["kpis"]["active_shipments"], 1)


if __name__ == "__main__":
    unittest.main()
