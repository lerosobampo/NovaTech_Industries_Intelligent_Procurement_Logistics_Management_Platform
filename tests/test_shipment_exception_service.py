
"""
NovaTech Industries
Shipment Exception Management — Automated Unit Tests

These tests use mocked database connections.
No PostgreSQL records are created or modified.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from src.database import shipment_exception_service as service


BASE_TIME = datetime(2026, 10, 21, 12, 0, 0)


def sample_exception(status="OPEN", **overrides):
    record = {
        "exception_id": 1,
        "shipment_id": "SHP-DEMO-001",
        "exception_type": "DELIVERY_DELAY",
        "severity": "MEDIUM",
        "exception_status": status,
        "description": "Simulated delivery delay.",
        "reported_by": "Logistics Analyst",
        "assigned_to": None,
        "corrective_action": None,
        "resolution_notes": None,
        "reported_at": BASE_TIME,
        "resolved_at": None,
        "closed_at": None,
        "simulation_mode": "SIMULATION",
        "evidence_classification": "SYNTHETIC_UNVERIFIED",
        "authorization_status": "NOT_AUTHORIZED",
        "created_at": BASE_TIME,
        "updated_at": BASE_TIME,
    }
    record.update(overrides)
    return record


@pytest.fixture
def mock_database():
    """Provide a mocked connection and cursor."""
    connection = MagicMock()
    cursor = MagicMock()

    connection.__enter__.return_value = connection
    connection.cursor.return_value.__enter__.return_value = cursor

    with patch.object(
        service, "get_connection", return_value=connection
    ):
        yield connection, cursor


class TestValidation:
    def test_supported_exception_types(self):
        assert len(service.EXCEPTION_TYPES) == 7
        assert "DELIVERY_DELAY" in service.EXCEPTION_TYPES
        assert "DAMAGED_GOODS" in service.EXCEPTION_TYPES

    def test_supported_severities(self):
        assert service.SEVERITIES == {
            "LOW", "MEDIUM", "HIGH", "CRITICAL"
        }

    def test_valid_workflow(self):
        assert service.STATUS_TRANSITIONS == {
            "OPEN": {"INVESTIGATING"},
            "INVESTIGATING": {"RESOLVED"},
            "RESOLVED": {"CLOSED"},
            "CLOSED": set(),
        }

    @pytest.mark.parametrize(
        "value",
        ["", " ", None, 123],
    )
    def test_required_text_rejects_invalid_values(self, value):
        with pytest.raises(service.ShipmentExceptionError):
            service._required_text(value, "test_field")

    def test_required_text_trims_whitespace(self):
        assert service._required_text(
            "  Logistics Analyst  ", "name"
        ) == "Logistics Analyst"

    def test_required_text_rejects_excessive_length(self):
        with pytest.raises(service.ShipmentExceptionError):
            service._required_text("ABCDEF", "name", 5)

    def test_choice_normalizes_case(self):
        assert service._choice(
            "medium", "severity", service.SEVERITIES
        ) == "MEDIUM"

    def test_choice_rejects_invalid_value(self):
        with pytest.raises(service.ShipmentExceptionError):
            service._choice(
                "EXTREME", "severity", service.SEVERITIES
            )

    @pytest.mark.parametrize(
        "exception_id",
        [0, -1, "1", None, True],
    )
    def test_invalid_exception_id(self, exception_id):
        with pytest.raises(service.ShipmentExceptionError):
            service._validate_exception_id(exception_id)

    def test_valid_exception_id(self):
        assert service._validate_exception_id(1) == 1

    def test_timestamp_accepts_datetime(self):
        assert service._timestamp(BASE_TIME) == BASE_TIME

    def test_timestamp_rejects_string(self):
        with pytest.raises(service.ShipmentExceptionError):
            service._timestamp("2026-10-21")


class TestChronology:
    def test_event_before_report_is_rejected(self):
        cursor = MagicMock()
        record = sample_exception()

        with pytest.raises(
            service.ShipmentExceptionError,
            match="precede",
        ):
            service._validate_event_time(
                cursor,
                record,
                BASE_TIME - timedelta(seconds=1),
            )

    def test_event_equal_to_latest_is_rejected(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = (BASE_TIME,)

        with pytest.raises(
            service.ShipmentExceptionError,
            match="later than",
        ):
            service._validate_event_time(
                cursor,
                sample_exception(),
                BASE_TIME,
            )

    def test_event_after_latest_is_accepted(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = (BASE_TIME,)

        service._validate_event_time(
            cursor,
            sample_exception(),
            BASE_TIME + timedelta(seconds=1),
        )

    def test_first_event_after_report_is_accepted(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = (None,)

        service._validate_event_time(
            cursor,
            sample_exception(),
            BASE_TIME + timedelta(seconds=1),
        )


class TestCreateException:
    def test_create_exception_writes_record_and_audit_event(
        self, mock_database
    ):
        _, cursor = mock_database

        # First fetch verifies shipment existence.
        # Second fetch returns the new exception ID.
        cursor.fetchone.side_effect = [
            ("SHP-DEMO-001",),
            (42,),
            (1001,),
        ]

        exception_id = service.create_exception(
            shipment_id="SHP-DEMO-001",
            exception_type="DELIVERY_DELAY",
            severity="MEDIUM",
            description="Simulated delay.",
            reported_by="Logistics Analyst",
            event_timestamp=BASE_TIME,
        )

        assert exception_id == 42

        queries = [
            call.args[0]
            for call in cursor.execute.call_args_list
        ]

        assert any(
            "INSERT INTO logistics.shipment_exceptions" in query
            for query in queries
        )
        assert any(
            "INSERT INTO logistics.shipment_exception_events"
            in query
            for query in queries
        )

    def test_create_exception_rejects_missing_shipment(
        self, mock_database
    ):
        _, cursor = mock_database
        cursor.fetchone.return_value = None

        with pytest.raises(
            service.ShipmentExceptionError,
            match="does not exist",
        ):
            service.create_exception(
                shipment_id="UNKNOWN",
                exception_type="DELIVERY_DELAY",
                severity="MEDIUM",
                description="Simulated delay.",
                reported_by="Logistics Analyst",
            )

    def test_create_exception_rejects_invalid_type(
        self, mock_database
    ):
        with pytest.raises(service.ShipmentExceptionError):
            service.create_exception(
                shipment_id="SHP-DEMO-001",
                exception_type="INVALID",
                severity="MEDIUM",
                description="Simulated delay.",
                reported_by="Logistics Analyst",
            )

    def test_create_exception_rejects_invalid_severity(
        self, mock_database
    ):
        with pytest.raises(service.ShipmentExceptionError):
            service.create_exception(
                shipment_id="SHP-DEMO-001",
                exception_type="DELIVERY_DELAY",
                severity="EXTREME",
                description="Simulated delay.",
                reported_by="Logistics Analyst",
            )


class TestWorkflowSafeguards:
    @pytest.mark.parametrize(
        "status",
        ["RESOLVED", "CLOSED"],
    )
    def test_assignment_rejects_final_statuses(
        self, mock_database, status
    ):
        with patch.object(
            service,
            "_fetch_exception",
            return_value=sample_exception(status),
        ):
            with pytest.raises(
                service.ShipmentExceptionError,
                match="Only OPEN or INVESTIGATING",
            ):
                service.assign_exception(
                    1,
                    "Another Analyst",
                    "Logistics Manager",
                )

    def test_investigation_rejects_closed_exception(
        self, mock_database
    ):
        with patch.object(
            service,
            "_fetch_exception",
            return_value=sample_exception("CLOSED"),
        ):
            with pytest.raises(
                service.ShipmentExceptionError,
                match="Invalid exception transition",
            ):
                service.start_investigation(
                    1,
                    "Logistics Analyst",
                    "Restart investigation.",
                )

    def test_corrective_action_requires_investigation(
        self, mock_database
    ):
        with patch.object(
            service,
            "_fetch_exception",
            return_value=sample_exception("OPEN"),
        ):
            with pytest.raises(
                service.ShipmentExceptionError,
                match="INVESTIGATING",
            ):
                service.record_corrective_action(
                    1,
                    "Contact simulated carrier.",
                    "Logistics Analyst",
                )

    def test_closed_exception_rejects_notes(
        self, mock_database
    ):
        with patch.object(
            service,
            "_fetch_exception",
            return_value=sample_exception("CLOSED"),
        ):
            with pytest.raises(
                service.ShipmentExceptionError,
                match="Closed exceptions",
            ):
                service.add_exception_note(
                    1,
                    "Additional note.",
                    "Logistics Analyst",
                )

    def test_resolution_requires_notes(self):
        with pytest.raises(
            service.ShipmentExceptionError,
            match="resolution_notes",
        ):
            service.resolve_exception(
                1,
                "",
                "Logistics Analyst",
            )

    def test_cannot_close_open_exception(
        self, mock_database
    ):
        with patch.object(
            service,
            "_fetch_exception",
            return_value=sample_exception("OPEN"),
        ):
            with pytest.raises(
                service.ShipmentExceptionError,
                match="Invalid exception transition",
            ):
                service.close_exception(
                    1,
                    "Logistics Manager",
                    "Attempted closure.",
                )


class TestSuccessfulTransitions:
    @pytest.mark.parametrize(
        "initial_status,new_status,event_type",
        [
            (
                "OPEN",
                "INVESTIGATING",
                "INVESTIGATION_STARTED",
            ),
            (
                "INVESTIGATING",
                "RESOLVED",
                "RESOLVED",
            ),
            (
                "RESOLVED",
                "CLOSED",
                "CLOSED",
            ),
        ],
    )
    def test_valid_transition_writes_audit_event(
        self,
        mock_database,
        initial_status,
        new_status,
        event_type,
    ):
        _, cursor = mock_database

        with (
            patch.object(
                service,
                "_fetch_exception",
                return_value=sample_exception(initial_status),
            ),
            patch.object(
                service, "_validate_event_time"
            ),
            patch.object(
                service, "_insert_event"
            ) as insert_event,
        ):
            service._transition_exception(
                exception_id=1,
                new_status=new_status,
                event_type=event_type,
                recorded_by="Logistics Analyst",
                description="Simulated workflow update.",
                event_timestamp=BASE_TIME + timedelta(seconds=1),
                resolution_notes="Resolved during simulation.",
            )

            assert cursor.execute.called
            insert_event.assert_called_once()

            args = insert_event.call_args.args
            assert args[3] == event_type
            assert args[6] == initial_status
            assert args[7] == new_status


class TestReadOperations:
    def test_list_exceptions_without_filters(
        self, mock_database
    ):
        _, cursor = mock_database

        cursor.description = [
            MagicMock(name="exception_id"),
            MagicMock(name="exception_status"),
        ]
        cursor.description[0].name = "exception_id"
        cursor.description[1].name = "exception_status"
        cursor.fetchall.return_value = [(1, "CLOSED")]

        results = service.list_exceptions()

        assert results == [
            {
                "exception_id": 1,
                "exception_status": "CLOSED",
            }
        ]

    def test_list_exceptions_with_filters(
        self, mock_database
    ):
        _, cursor = mock_database
        cursor.description = []
        cursor.fetchall.return_value = []

        service.list_exceptions(
            shipment_id="SHP-DEMO-001",
            status="OPEN",
        )

        query, parameters = cursor.execute.call_args.args

        assert "shipment_id = %s" in query
        assert "exception_status = %s" in query
        assert parameters == ("SHP-DEMO-001", "OPEN")

    def test_list_exceptions_rejects_invalid_status(self):
        with pytest.raises(service.ShipmentExceptionError):
            service.list_exceptions(status="INVALID")


class TestGovernance:
    def test_governance_constants(self):
        assert service.GOVERNANCE == {
            "simulation_mode": "SIMULATION",
            "evidence_classification": "SYNTHETIC_UNVERIFIED",
            "authorization_status": "NOT_AUTHORIZED",
        }

    def test_service_contains_no_shipment_status_updates(self):
        """Exception operations must not update shipment lifecycle."""

        import inspect

        source = inspect.getsource(service)

        assert "UPDATE logistics.shipments" not in source
        assert "DELETE FROM logistics.shipments" not in source
        assert "UPDATE procurement." not in source
