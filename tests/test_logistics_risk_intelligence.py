
"""
NovaTech Industries
Logistics Risk Intelligence — Automated Tests

Tests the rule-based shipment risk assessment engine.

All test data is synthetic.
Database connections are mocked; no PostgreSQL records are modified.
"""

from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from src.analysis import logistics_risk_intelligence as risk


ASSESSMENT_DATE = date(2026, 10, 21)


def make_shipment(
    shipment_id="SHP-TEST-001",
    status="IN_TRANSIT",
    estimated_delivery=None,
):
    """Create a synthetic shipment record."""

    return {
        "shipment_id": shipment_id,
        "shipment_status": status,
        "estimated_delivery_date": estimated_delivery,
    }


def make_exception(
    shipment_id="SHP-TEST-001",
    severity="MEDIUM",
    status="OPEN",
):
    """Create a synthetic exception record."""

    return {
        "shipment_id": shipment_id,
        "severity": severity,
        "exception_status": status,
    }


def assess(shipment, exceptions=None):
    """Assess a shipment using the fixed test date."""

    return risk.assess_shipment_risk(
        shipment,
        exceptions or [],
        ASSESSMENT_DATE,
    )


class TestDateValidation:

    def test_default_date_is_valid(self):
        assert isinstance(risk._validate_as_of_date(None), date)

    def test_explicit_date_is_accepted(self):
        assert (
            risk._validate_as_of_date(ASSESSMENT_DATE)
            == ASSESSMENT_DATE
        )

    def test_datetime_is_rejected(self):
        with pytest.raises(ValueError):
            risk._validate_as_of_date(
                datetime(2026, 10, 21, 12, 0)
            )

    @pytest.mark.parametrize(
        "invalid_value",
        ["2026-10-21", 123, [], {}],
    )
    def test_invalid_dates_are_rejected(self, invalid_value):
        with pytest.raises(ValueError):
            risk._validate_as_of_date(invalid_value)


class TestRiskClassification:

    @pytest.mark.parametrize(
        "score,expected",
        [
            (0, "LOW"),
            (19, "LOW"),
            (20, "MEDIUM"),
            (39, "MEDIUM"),
            (40, "HIGH"),
            (69, "HIGH"),
            (70, "CRITICAL"),
            (100, "CRITICAL"),
        ],
    )
    def test_risk_level_boundaries(self, score, expected):
        assert risk._risk_level(score) == expected


class TestOverdueScoring:

    @pytest.mark.parametrize(
        "days,expected",
        [
            (0, 0),
            (1, 20),
            (2, 20),
            (3, 35),
            (6, 35),
            (7, 45),
            (30, 45),
        ],
    )
    def test_overdue_points(self, days, expected):
        assert risk._overdue_points(days) == expected

    def test_future_delivery_has_no_overdue_risk(self):
        shipment = make_shipment(
            estimated_delivery=ASSESSMENT_DATE
            + timedelta(days=7)
        )

        result = assess(shipment)

        assert result["risk_score"] == 0
        assert result["days_overdue"] == 0
        assert result["risk_level"] == "LOW"

    def test_delivery_due_today_is_not_overdue(self):
        shipment = make_shipment(
            estimated_delivery=ASSESSMENT_DATE
        )

        result = assess(shipment)

        assert result["risk_score"] == 0
        assert result["days_overdue"] == 0

    def test_one_day_overdue(self):
        shipment = make_shipment(
            estimated_delivery=ASSESSMENT_DATE
            - timedelta(days=1)
        )

        result = assess(shipment)

        assert result["risk_score"] == 20
        assert result["risk_level"] == "MEDIUM"
        assert result["days_overdue"] == 1

    def test_three_days_overdue(self):
        shipment = make_shipment(
            estimated_delivery=ASSESSMENT_DATE
            - timedelta(days=3)
        )

        result = assess(shipment)

        assert result["risk_score"] == 35
        assert result["risk_level"] == "MEDIUM"

    def test_seven_days_overdue(self):
        shipment = make_shipment(
            estimated_delivery=ASSESSMENT_DATE
            - timedelta(days=7)
        )

        result = assess(shipment)

        assert result["risk_score"] == 45
        assert result["risk_level"] == "HIGH"

    def test_delivered_shipment_is_not_overdue(self):
        shipment = make_shipment(
            status="DELIVERED",
            estimated_delivery=ASSESSMENT_DATE
            - timedelta(days=10),
        )

        result = assess(shipment)

        assert result["risk_score"] == 0
        assert result["days_overdue"] == 0

    def test_cancelled_shipment_is_not_overdue(self):
        shipment = make_shipment(
            status="CANCELLED",
            estimated_delivery=ASSESSMENT_DATE
            - timedelta(days=10),
        )

        result = assess(shipment)

        assert result["risk_score"] == 0


class TestExceptionScoring:

    @pytest.mark.parametrize(
        "severity,expected_score",
        [
            ("LOW", 10),
            ("MEDIUM", 20),
            ("HIGH", 35),
            ("CRITICAL", 50),
        ],
    )
    def test_unresolved_exception_severity(
        self, severity, expected_score
    ):
        shipment = make_shipment()

        result = assess(
            shipment,
            [make_exception(severity=severity)],
        )

        assert result["risk_score"] == expected_score
        assert result["unresolved_exception_count"] == 1
        assert result["highest_exception_severity"] == severity

    def test_investigating_exception_counts_as_unresolved(self):
        result = assess(
            make_shipment(),
            [make_exception(status="INVESTIGATING")],
        )

        assert result["unresolved_exception_count"] == 1
        assert result["risk_score"] == 20

    @pytest.mark.parametrize(
        "status",
        ["RESOLVED", "CLOSED"],
    )
    def test_completed_exception_does_not_add_risk(self, status):
        result = assess(
            make_shipment(),
            [make_exception(status=status)],
        )

        assert result["risk_score"] == 0
        assert result["unresolved_exception_count"] == 0

    def test_highest_severity_is_used_once(self):
        exceptions = [
            make_exception(severity="LOW"),
            make_exception(severity="MEDIUM"),
            make_exception(severity="HIGH"),
        ]

        result = assess(make_shipment(), exceptions)

        assert result["risk_score"] == 35
        assert result["unresolved_exception_count"] == 3
        assert result["highest_exception_severity"] == "HIGH"

    def test_exception_from_other_shipment_is_ignored(self):
        exception = make_exception(
            shipment_id="SHP-OTHER-001",
            severity="CRITICAL",
        )

        result = assess(make_shipment(), [exception])

        assert result["risk_score"] == 0
        assert result["unresolved_exception_count"] == 0


class TestCombinedRisk:

    def test_exception_shipment_status_adds_25_points(self):
        result = assess(
            make_shipment(status="EXCEPTION")
        )

        assert result["risk_score"] == 25
        assert result["risk_level"] == "MEDIUM"

    def test_overdue_and_high_exception(self):
        shipment = make_shipment(
            estimated_delivery=ASSESSMENT_DATE
            - timedelta(days=7)
        )

        result = assess(
            shipment,
            [make_exception(severity="HIGH")],
        )

        assert result["risk_score"] == 80
        assert result["risk_level"] == "CRITICAL"

    def test_risk_score_is_capped_at_100(self):
        shipment = make_shipment(
            status="EXCEPTION",
            estimated_delivery=ASSESSMENT_DATE
            - timedelta(days=10),
        )

        result = assess(
            shipment,
            [make_exception(severity="CRITICAL")],
        )

        assert result["risk_score"] == 100
        assert result["risk_level"] == "CRITICAL"

    def test_risk_factors_explain_score(self):
        shipment = make_shipment(
            estimated_delivery=ASSESSMENT_DATE
            - timedelta(days=3)
        )

        result = assess(
            shipment,
            [make_exception(severity="MEDIUM")],
        )

        factors = result["risk_factors"]

        assert len(factors) == 2
        assert sum(f["points"] for f in factors) == 55
        assert result["risk_score"] == 55

        assert {
            factor["factor"] for factor in factors
        } == {
            "OVERDUE_SHIPMENT",
            "UNRESOLVED_EXCEPTION",
        }


class TestGovernance:

    def test_governance_constants(self):
        assert risk.GOVERNANCE == {
            "simulation_mode": "SIMULATION",
            "evidence_classification": "SYNTHETIC_UNVERIFIED",
            "authorization_status": "NOT_AUTHORIZED",
            "risk_model": "RULE_BASED_HEURISTIC_V1",
        }

    def test_assessment_includes_governance(self):
        result = assess(make_shipment())

        for key, value in risk.GOVERNANCE.items():
            assert result[key] == value

    def test_risk_engine_has_no_database_writes(self):
        import inspect

        source = inspect.getsource(risk)

        assert "INSERT INTO" not in source
        assert "UPDATE logistics." not in source
        assert "DELETE FROM" not in source


class TestReportGeneration:

    def test_report_aggregates_and_sorts_risk(self):
        """
        Mock PostgreSQL query results and verify report ordering,
        classification totals, and high-priority counts.
        """

        shipments = [
            (
                "SHP-LOW",
                "IN_TRANSIT",
                ASSESSMENT_DATE + timedelta(days=5),
            ),
            (
                "SHP-HIGH",
                "IN_TRANSIT",
                ASSESSMENT_DATE - timedelta(days=7),
            ),
            (
                "SHP-CRITICAL",
                "EXCEPTION",
                ASSESSMENT_DATE - timedelta(days=10),
            ),
        ]

        exceptions = [
            (1, "SHP-CRITICAL", "OPEN", "CRITICAL"),
        ]

        connection = MagicMock()
        cursor = MagicMock()

        connection.__enter__.return_value = connection
        connection.cursor.return_value.__enter__.return_value = cursor

        shipment_columns = [
            "shipment_id",
            "shipment_status",
            "estimated_delivery_date",
        ]

        exception_columns = [
            "exception_id",
            "shipment_id",
            "exception_status",
            "severity",
        ]

        def execute_query(query):
            if "FROM logistics.shipments" in query:
                cursor.description = [
                    type("Column", (), {"name": name})()
                    for name in shipment_columns
                ]
                cursor.fetchall.return_value = shipments

            elif "FROM logistics.shipment_exceptions" in query:
                cursor.description = [
                    type("Column", (), {"name": name})()
                    for name in exception_columns
                ]
                cursor.fetchall.return_value = exceptions

        cursor.execute.side_effect = execute_query

        with patch.object(
            risk,
            "get_connection",
            return_value=connection,
        ):
            report = risk.generate_logistics_risk_intelligence(
                ASSESSMENT_DATE
            )

        assert report["total_shipments"] == 3
        assert report["high_priority_shipments"] == 2

        assert report["risk_distribution"] == {
            "LOW": 1,
            "MEDIUM": 0,
            "HIGH": 1,
            "CRITICAL": 1,
        }

        assert [
            item["shipment_id"]
            for item in report["shipments"]
        ] == [
            "SHP-CRITICAL",
            "SHP-HIGH",
            "SHP-LOW",
        ]

        assert report["shipments"][0]["risk_score"] == 100
        assert report["shipments"][1]["risk_score"] == 45
        assert report["shipments"][2]["risk_score"] == 0

    def test_empty_database_returns_empty_report(self):
        connection = MagicMock()
        cursor = MagicMock()

        connection.__enter__.return_value = connection
        connection.cursor.return_value.__enter__.return_value = cursor

        cursor.description = []
        cursor.fetchall.return_value = []

        with patch.object(
            risk,
            "get_connection",
            return_value=connection,
        ):
            report = risk.generate_logistics_risk_intelligence(
                ASSESSMENT_DATE
            )

        assert report["total_shipments"] == 0
        assert report["high_priority_shipments"] == 0
        assert report["shipments"] == []

        assert all(
            count == 0
            for count in report["risk_distribution"].values()
        )
