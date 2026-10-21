
"""
NovaTech Industries
Logistics Intelligence — Shipment Tracking Service Tests

Tests shipment lifecycle rules, input validation,
database operations, and transaction safeguards.

All database connections are mocked.
No PostgreSQL records are created or modified.
"""

import unittest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

from psycopg.errors import UniqueViolation

from src.database.shipment_tracking_service import (
    ALLOWED_TRANSITIONS,
    ShipmentTrackingError,
    _validate_date,
    _validate_timestamp,
    create_shipment,
    get_shipment,
    get_shipment_events,
    list_shipments,
    update_shipment_status,
)


class FakeDatabase:
    """Mock a PostgreSQL connection and cursor."""

    def __init__(self):
        self.connection = MagicMock()
        self.cursor = MagicMock()

        self.connection.__enter__.return_value = self.connection
        self.connection.cursor.return_value.__enter__.return_value = (
            self.cursor
        )

        self.cursor.description = [
            MagicMock(name=column)
            for column in (
                "shipment_id",
                "supplier_id",
                "delivery_id",
                "tracking_number",
                "carrier_name",
                "transport_mode",
                "origin_location",
                "destination_location",
                "dispatch_date",
                "estimated_delivery_date",
                "actual_delivery_date",
                "shipment_status",
                "simulation_mode",
                "evidence_classification",
                "authorization_status",
                "created_at",
                "updated_at",
            )
        ]

        for description, name in zip(
            self.cursor.description,
            (
                "shipment_id",
                "supplier_id",
                "delivery_id",
                "tracking_number",
                "carrier_name",
                "transport_mode",
                "origin_location",
                "destination_location",
                "dispatch_date",
                "estimated_delivery_date",
                "actual_delivery_date",
                "shipment_status",
                "simulation_mode",
                "evidence_classification",
                "authorization_status",
                "created_at",
                "updated_at",
            ),
        ):
            description.name = name

    def patch_connection(self):
        return patch(
            "src.database.shipment_tracking_service.get_connection",
            return_value=self.connection,
        )


class TestShipmentTrackingService(unittest.TestCase):

    def setUp(self):
        self.db = FakeDatabase()

        self.created_at = datetime(2026, 10, 20, 9, 0)
        self.dispatched_at = datetime(2026, 10, 21, 10, 0)
        self.transit_at = datetime(2026, 10, 22, 11, 0)
        self.delivered_at = datetime(2026, 10, 25, 15, 0)

        self.shipment = {
            "shipment_id": "TEST-SHP-001",
            "supplier_id": "SUP001",
            "delivery_id": None,
            "tracking_number": "TEST-TRACK-001",
            "carrier_name": "Synthetic Carrier",
            "transport_mode": "ROAD",
            "origin_location": "Rotterdam",
            "destination_location": "The Hague",
            "dispatch_date": None,
            "estimated_delivery_date": date(2026, 10, 26),
            "actual_delivery_date": None,
            "shipment_status": "CREATED",
            "simulation_mode": "SIMULATION",
            "evidence_classification": "SYNTHETIC_UNVERIFIED",
            "authorization_status": "NOT_AUTHORIZED",
            "created_at": self.created_at,
            "updated_at": self.created_at,
        }

    def mock_shipment_lookup(self, shipment):
        """Configure a mock shipment SELECT response."""

        columns = list(shipment.keys())

        self.db.cursor.description = [
            MagicMock(name=column)
            for column in columns
        ]

        for item, column in zip(
            self.db.cursor.description,
            columns,
        ):
            item.name = column

        self.db.cursor.fetchone.return_value = tuple(
            shipment[column] for column in columns
        )

    def test_valid_lifecycle_transitions(self):
        self.assertIn(
            "DISPATCHED",
            ALLOWED_TRANSITIONS["CREATED"],
        )
        self.assertIn(
            "IN_TRANSIT",
            ALLOWED_TRANSITIONS["DISPATCHED"],
        )
        self.assertIn(
            "DELIVERED",
            ALLOWED_TRANSITIONS["IN_TRANSIT"],
        )

    def test_invalid_lifecycle_transitions(self):
        self.assertNotIn(
            "DELIVERED",
            ALLOWED_TRANSITIONS["CREATED"],
        )
        self.assertNotIn(
            "IN_TRANSIT",
            ALLOWED_TRANSITIONS["DELIVERED"],
        )
        self.assertEqual(
            ALLOWED_TRANSITIONS["CANCELLED"],
            set(),
        )

    def test_invalid_transport_mode(self):
        with self.assertRaises(ShipmentTrackingError):
            create_shipment(
                supplier_id="SUP001",
                carrier_name="Test Carrier",
                transport_mode="SPACE",
                origin_location="Rotterdam",
                destination_location="The Hague",
                estimated_delivery_date=date(2026, 10, 26),
            )

    def test_invalid_estimated_delivery_date(self):
        with self.assertRaises(ShipmentTrackingError):
            create_shipment(
                supplier_id="SUP001",
                carrier_name="Test Carrier",
                transport_mode="ROAD",
                origin_location="Rotterdam",
                destination_location="The Hague",
                estimated_delivery_date="2026-10-26",
            )

    def test_timestamp_must_be_datetime(self):
        with self.assertRaises(ShipmentTrackingError):
            _validate_timestamp(date(2026, 10, 20))

    def test_date_must_not_be_datetime(self):
        with self.assertRaises(ShipmentTrackingError):
            _validate_date(
                datetime(2026, 10, 20, 9, 0),
                "test_date",
            )

    def test_create_shipment(self):
        self.db.cursor.fetchone.return_value = (1,)

        with self.db.patch_connection():
            shipment_id = create_shipment(
                shipment_id="TEST-SHP-001",
                supplier_id="SUP001",
                carrier_name="Synthetic Carrier",
                transport_mode="ROAD",
                origin_location="Rotterdam",
                destination_location="The Hague",
                estimated_delivery_date=date(2026, 10, 26),
                event_timestamp=self.created_at,
            )

        self.assertEqual(shipment_id, "TEST-SHP-001")
        self.assertEqual(self.db.cursor.execute.call_count, 3)

        sql_statements = [
            call.args[0]
            for call in self.db.cursor.execute.call_args_list
        ]

        self.assertTrue(
            any(
                "INSERT INTO logistics.shipments" in sql
                for sql in sql_statements
            )
        )
        self.assertTrue(
            any(
                "INSERT INTO logistics.shipment_events" in sql
                for sql in sql_statements
            )
        )

    def test_unknown_supplier_rejected(self):
        self.db.cursor.fetchone.return_value = None

        with self.db.patch_connection():
            with self.assertRaisesRegex(
                ShipmentTrackingError,
                "Unknown supplier",
            ):
                create_shipment(
                    supplier_id="UNKNOWN",
                    carrier_name="Synthetic Carrier",
                    transport_mode="ROAD",
                    origin_location="Rotterdam",
                    destination_location="The Hague",
                    estimated_delivery_date=date(2026, 10, 26),
                    event_timestamp=self.created_at,
                )

        self.assertEqual(self.db.cursor.execute.call_count, 1)

    def test_duplicate_shipment_rejected(self):
        self.db.cursor.fetchone.return_value = (1,)

        def execute_with_duplicate(sql, params=None):
            if "INSERT INTO logistics.shipments" in sql:
                raise UniqueViolation("Duplicate shipment")

        self.db.cursor.execute.side_effect = execute_with_duplicate

        with self.db.patch_connection():
            with self.assertRaisesRegex(
                ShipmentTrackingError,
                "already exists",
            ):
                create_shipment(
                    shipment_id="TEST-SHP-001",
                    supplier_id="SUP001",
                    carrier_name="Synthetic Carrier",
                    transport_mode="ROAD",
                    origin_location="Rotterdam",
                    destination_location="The Hague",
                    estimated_delivery_date=date(2026, 10, 26),
                    event_timestamp=self.created_at,
                )

    def test_invalid_transition_rejected(self):
        self.mock_shipment_lookup(self.shipment)

        with patch(
            "src.database.shipment_tracking_service._fetch_shipment",
            return_value=self.shipment,
        ):
            with self.db.patch_connection():
                with self.assertRaisesRegex(
                    ShipmentTrackingError,
                    "Invalid transition",
                ):
                    update_shipment_status(
                        shipment_id="TEST-SHP-001",
                        new_status="DELIVERED",
                        event_timestamp=self.delivered_at,
                        event_location="The Hague",
                        event_description="Invalid direct delivery",
                    )

        sql_statements = [
            call.args[0]
            for call in self.db.cursor.execute.call_args_list
        ]

        self.assertFalse(
            any(
                "UPDATE logistics.shipments" in sql
                for sql in sql_statements
            )
        )

    def test_valid_dispatch_transition(self):
        self.db.cursor.fetchone.return_value = (
            self.created_at,
        )

        with patch(
            "src.database.shipment_tracking_service._fetch_shipment",
            return_value=self.shipment,
        ):
            with self.db.patch_connection():
                result = update_shipment_status(
                    shipment_id="TEST-SHP-001",
                    new_status="DISPATCHED",
                    event_timestamp=self.dispatched_at,
                    event_location="Rotterdam",
                    event_description="Shipment dispatched",
                )

        self.assertEqual(result, "DISPATCHED")

        sql_statements = [
            call.args[0]
            for call in self.db.cursor.execute.call_args_list
        ]

        self.assertTrue(
            any(
                "UPDATE logistics.shipments" in sql
                for sql in sql_statements
            )
        )
        self.assertTrue(
            any(
                "INSERT INTO logistics.shipment_events" in sql
                for sql in sql_statements
            )
        )

    def test_out_of_order_event_rejected(self):
        self.db.cursor.fetchone.return_value = (
            self.dispatched_at,
        )

        with patch(
            "src.database.shipment_tracking_service._fetch_shipment",
            return_value=self.shipment,
        ):
            with self.db.patch_connection():
                with self.assertRaisesRegex(
                    ShipmentTrackingError,
                    "later than the previous event",
                ):
                    update_shipment_status(
                        shipment_id="TEST-SHP-001",
                        new_status="DISPATCHED",
                        event_timestamp=self.created_at,
                        event_location="Rotterdam",
                        event_description="Out-of-order event",
                    )

    def test_unknown_shipment_rejected(self):
        with patch(
            "src.database.shipment_tracking_service._fetch_shipment",
            return_value=None,
        ):
            with self.db.patch_connection():
                with self.assertRaisesRegex(
                    ShipmentTrackingError,
                    "Unknown shipment",
                ):
                    update_shipment_status(
                        shipment_id="UNKNOWN",
                        new_status="DISPATCHED",
                        event_timestamp=self.dispatched_at,
                        event_location="Rotterdam",
                        event_description="Shipment dispatched",
                    )

    def test_transaction_rollback_on_event_failure(self):
        self.db.cursor.fetchone.return_value = (
            self.created_at,
        )

        def execute_with_event_failure(sql, params=None):
            if "INSERT INTO logistics.shipment_events" in sql:
                raise UniqueViolation("Duplicate event")

        self.db.cursor.execute.side_effect = (
            execute_with_event_failure
        )

        with patch(
            "src.database.shipment_tracking_service._fetch_shipment",
            return_value=self.shipment,
        ):
            with self.db.patch_connection():
                with self.assertRaisesRegex(
                    ShipmentTrackingError,
                    "Duplicate shipment tracking event",
                ):
                    update_shipment_status(
                        shipment_id="TEST-SHP-001",
                        new_status="DISPATCHED",
                        event_timestamp=self.dispatched_at,
                        event_location="Rotterdam",
                        event_description="Shipment dispatched",
                    )

        self.assertTrue(
            any(
                "UPDATE logistics.shipments" in call.args[0]
                for call in self.db.cursor.execute.call_args_list
            )
        )

        # Mock verifies exception propagation. Actual rollback
        # behavior is supplied by psycopg's connection context.

    def test_invalid_status_rejected(self):
        with self.assertRaises(ShipmentTrackingError):
            update_shipment_status(
                shipment_id="TEST-SHP-001",
                new_status="UNKNOWN",
                event_timestamp=self.dispatched_at,
                event_location="Rotterdam",
                event_description="Invalid status",
            )

    def test_list_shipments_invalid_filter(self):
        with self.assertRaises(ShipmentTrackingError):
            list_shipments(status="UNKNOWN")

    def test_governance_values_in_creation(self):
        self.db.cursor.fetchone.return_value = (1,)

        with self.db.patch_connection():
            create_shipment(
                shipment_id="TEST-SHP-GOV",
                supplier_id="SUP001",
                carrier_name="Synthetic Carrier",
                transport_mode="ROAD",
                origin_location="Rotterdam",
                destination_location="The Hague",
                estimated_delivery_date=date(2026, 10, 26),
                event_timestamp=self.created_at,
            )

        insert_call = next(
            call
            for call in self.db.cursor.execute.call_args_list
            if "INSERT INTO logistics.shipments" in call.args[0]
        )

        self.assertIn("SIMULATION", insert_call.args[0])
        self.assertIn(
            "SYNTHETIC_UNVERIFIED",
            insert_call.args[0],
        )
        self.assertIn(
            "NOT_AUTHORIZED",
            insert_call.args[0],
        )


if __name__ == "__main__":
    unittest.main()
