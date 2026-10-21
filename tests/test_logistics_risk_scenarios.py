
"""
NovaTech Industries
Logistics Risk Scenario Analysis — Automated Tests

All data is synthetic.
Tests operate in memory without PostgreSQL access.
"""

from copy import deepcopy
from datetime import date, datetime, timedelta

import pytest

from src.analysis.logistics_risk_intelligence import (
    assess_shipment_risk,
)
from src.analysis.logistics_risk_scenarios import (
    ScenarioValidationError,
    SCENARIO_GOVERNANCE,
    analyze_risk_scenario,
)


TODAY = date(2026, 10, 21)


def make_shipment(
    shipment_id="SHP-TEST-001",
    status="IN_TRANSIT",
    delivery=None,
):
    return {
        "shipment_id": shipment_id,
        "shipment_status": status,
        "estimated_delivery_date": (
            delivery
            if delivery is not None
            else TODAY + timedelta(days=7)
        ),
    }


def make_exception(
    shipment_id="SHP-TEST-001",
    severity="MEDIUM",
    status="OPEN",
):
    return {
        "shipment_id": shipment_id,
        "severity": severity,
        "exception_status": status,
    }


_SENTINEL = object()

def run_scenario(
    changes,
    shipment=_SENTINEL,
    exceptions=None,
):
    return analyze_risk_scenario(
        shipment=(
            make_shipment()
            if shipment is _SENTINEL
            else shipment
        ),
        exceptions=(
            exceptions
            if exceptions is not None
            else []
        ),
        changes=changes,
        as_of_date=TODAY,
    )

class TestScenarioBasics:

    def test_empty_changes_produce_identical_assessments(self):
        result = run_scenario({})

        assert result["baseline"]["risk_score"] == 0
        assert result["scenario"]["risk_score"] == 0
        assert result["score_change"] == 0
        assert result["risk_direction"] == "UNCHANGED"

    def test_scenario_contains_expected_fields(self):
        result = run_scenario({})

        assert result["shipment_id"] == "SHP-TEST-001"
        assert result["assessment_date"] == TODAY
        assert "baseline" in result
        assert "scenario" in result
        assert "score_change" in result
        assert "risk_direction" in result
        assert "scenario_changes" in result
        assert "governance" in result

    def test_scenario_does_not_mutate_inputs(self):
        shipment = make_shipment()
        exceptions = [make_exception()]
        changes = {
            "shipment_status": "EXCEPTION",
            "new_exception_severity": "HIGH",
            "override_exception_severity": "CRITICAL",
        }

        original_shipment = deepcopy(shipment)
        original_exceptions = deepcopy(exceptions)
        original_changes = deepcopy(changes)

        analyze_risk_scenario(
            shipment, exceptions, changes, TODAY
        )

        assert shipment == original_shipment
        assert exceptions == original_exceptions
        assert changes == original_changes

    def test_empty_scenario_preserves_existing_risk(self):
        shipment = make_shipment(
            delivery=TODAY - timedelta(days=3)
        )
        exceptions = [make_exception(severity="HIGH")]

        result = run_scenario(
            {},
            shipment=shipment,
            exceptions=exceptions,
        )

        assert result["baseline"]["risk_score"] == 70
        assert result["scenario"]["risk_score"] == 70
        assert result["score_change"] == 0


class TestDeliveryDateScenarios:

    @pytest.mark.parametrize(
        "days_overdue,expected_score",
        [
            (1, 20),
            (2, 20),
            (3, 35),
            (6, 35),
            (7, 45),
            (14, 45),
        ],
    )
    def test_overdue_scenario(
        self, days_overdue, expected_score
    ):
        result = run_scenario({
            "estimated_delivery_date":
                TODAY - timedelta(days=days_overdue)
        })

        assert result["baseline"]["risk_score"] == 0
        assert result["scenario"]["risk_score"] == expected_score
        assert result["score_change"] == expected_score
        assert result["risk_direction"] == "INCREASED"

    def test_postponed_delivery_reduces_risk(self):
        shipment = make_shipment(
            delivery=TODAY - timedelta(days=7)
        )

        result = run_scenario(
            {
                "estimated_delivery_date":
                    TODAY + timedelta(days=5)
            },
            shipment=shipment,
        )

        assert result["baseline"]["risk_score"] == 45
        assert result["scenario"]["risk_score"] == 0
        assert result["score_change"] == -45
        assert result["risk_direction"] == "DECREASED"

    def test_delivery_today_is_not_overdue(self):
        result = run_scenario({
            "estimated_delivery_date": TODAY
        })

        assert result["scenario"]["risk_score"] == 0

    def test_missing_delivery_date_does_not_add_risk(self):
        result = run_scenario({
            "estimated_delivery_date": None
        })

        assert result["scenario"]["risk_score"] == 0

    def test_delivery_date_change_does_not_change_status(self):
        result = run_scenario({
            "estimated_delivery_date":
                TODAY - timedelta(days=3)
        })

        assert (
            result["scenario"]["shipment_status"]
            == "IN_TRANSIT"
        )


class TestShipmentStatusScenarios:

    def test_exception_status_adds_risk(self):
        result = run_scenario({
            "shipment_status": "EXCEPTION"
        })

        assert result["scenario"]["risk_score"] == 25
        assert result["scenario"]["risk_level"] == "MEDIUM"

    def test_delivered_status_removes_overdue_risk(self):
        shipment = make_shipment(
            delivery=TODAY - timedelta(days=10)
        )

        result = run_scenario(
            {"shipment_status": "DELIVERED"},
            shipment=shipment,
        )

        assert result["baseline"]["risk_score"] == 45
        assert result["scenario"]["risk_score"] == 0
        assert result["risk_direction"] == "DECREASED"

    def test_cancelled_status_removes_overdue_risk(self):
        shipment = make_shipment(
            delivery=TODAY - timedelta(days=10)
        )

        result = run_scenario(
            {"shipment_status": "CANCELLED"},
            shipment=shipment,
        )

        assert result["baseline"]["risk_score"] == 45
        assert result["scenario"]["risk_score"] == 0

    @pytest.mark.parametrize(
        "status",
        [
            "CREATED",
            "DISPATCHED",
            "IN_TRANSIT",
            "EXCEPTION",
            "DELIVERED",
            "CANCELLED",
        ],
    )
    def test_supported_statuses(self, status):
        result = run_scenario({
            "shipment_status": status
        })

        assert result["scenario"]["shipment_status"] == status


class TestExceptionScenarios:

    @pytest.mark.parametrize(
        "severity,expected_score",
        [
            ("LOW", 10),
            ("MEDIUM", 20),
            ("HIGH", 35),
            ("CRITICAL", 50),
        ],
    )
    def test_new_exception_severity(
        self, severity, expected_score
    ):
        result = run_scenario({
            "new_exception_severity": severity
        })

        assert result["scenario"]["risk_score"] == expected_score
        assert (
            result["scenario"]["unresolved_exception_count"]
            == 1
        )

    def test_new_exception_defaults_to_open(self):
        result = run_scenario({
            "new_exception_severity": "HIGH"
        })

        assert result["scenario"]["risk_score"] == 35

    def test_new_investigating_exception_counts(self):
        result = run_scenario({
            "new_exception_severity": "HIGH",
            "new_exception_status": "INVESTIGATING",
        })

        assert result["scenario"]["risk_score"] == 35

    @pytest.mark.parametrize(
        "status",
        ["RESOLVED", "CLOSED"],
    )
    def test_completed_new_exception_does_not_add_risk(
        self, status
    ):
        result = run_scenario({
            "new_exception_severity": "CRITICAL",
            "new_exception_status": status,
        })

        assert result["scenario"]["risk_score"] == 0

    def test_severity_override_increases_risk(self):
        exceptions = [make_exception(severity="LOW")]

        result = run_scenario(
            {"override_exception_severity": "CRITICAL"},
            exceptions=exceptions,
        )

        assert result["baseline"]["risk_score"] == 10
        assert result["scenario"]["risk_score"] == 50
        assert result["score_change"] == 40

    def test_severity_override_decreases_risk(self):
        exceptions = [make_exception(severity="CRITICAL")]

        result = run_scenario(
            {"override_exception_severity": "LOW"},
            exceptions=exceptions,
        )

        assert result["baseline"]["risk_score"] == 50
        assert result["scenario"]["risk_score"] == 10
        assert result["score_change"] == -40

    def test_override_does_not_reopen_closed_exception(self):
        exceptions = [
            make_exception(severity="HIGH", status="CLOSED")
        ]

        result = run_scenario(
            {"override_exception_severity": "CRITICAL"},
            exceptions=exceptions,
        )

        assert result["baseline"]["risk_score"] == 0
        assert result["scenario"]["risk_score"] == 0

    def test_highest_severity_is_counted_once(self):
        exceptions = [
            make_exception(severity="LOW"),
            make_exception(severity="MEDIUM"),
        ]

        result = run_scenario(
            {"new_exception_severity": "HIGH"},
            exceptions=exceptions,
        )

        assert result["scenario"]["risk_score"] == 35
        assert (
            result["scenario"]["unresolved_exception_count"]
            == 3
        )


class TestCombinedScenarios:

    def test_full_scenario_reaches_critical_risk(self):
        result = run_scenario({
            "shipment_status": "EXCEPTION",
            "estimated_delivery_date":
                TODAY - timedelta(days=7),
            "new_exception_severity": "HIGH",
        })

        assert result["baseline"]["risk_score"] == 0
        assert result["scenario"]["risk_score"] == 100
        assert result["scenario"]["risk_level"] == "CRITICAL"
        assert result["score_change"] == 100

    def test_scenario_score_is_capped_at_100(self):
        result = run_scenario({
            "shipment_status": "EXCEPTION",
            "estimated_delivery_date":
                TODAY - timedelta(days=10),
            "new_exception_severity": "CRITICAL",
        })

        assert result["scenario"]["risk_score"] == 100

    def test_scenario_uses_original_risk_engine(self):
        shipment = make_shipment()
        exceptions = [make_exception(severity="MEDIUM")]

        result = run_scenario(
            {"shipment_status": "EXCEPTION"},
            shipment=shipment,
            exceptions=exceptions,
        )

        expected_baseline = assess_shipment_risk(
            shipment, exceptions, TODAY
        )

        expected_scenario_shipment = deepcopy(shipment)
        expected_scenario_shipment[
            "shipment_status"
        ] = "EXCEPTION"

        expected_scenario = assess_shipment_risk(
            expected_scenario_shipment,
            exceptions,
            TODAY,
        )

        assert result["baseline"] == expected_baseline
        assert result["scenario"] == expected_scenario

    def test_risk_factors_explain_scenario(self):
        result = run_scenario({
            "shipment_status": "EXCEPTION",
            "estimated_delivery_date":
                TODAY - timedelta(days=3),
            "new_exception_severity": "MEDIUM",
        })

        factors = result["scenario"]["risk_factors"]

        assert {
            factor["factor"] for factor in factors
        } == {
            "OVERDUE_SHIPMENT",
            "SHIPMENT_EXCEPTION_STATUS",
            "UNRESOLVED_EXCEPTION",
        }

        assert result["scenario"]["risk_score"] == 80


class TestValidation:

    @pytest.mark.parametrize(
        "invalid_shipment",
        [
            None,
            [],
            {},
            {"shipment_id": "", "shipment_status": "IN_TRANSIT"},
            {"shipment_id": "SHP-1", "shipment_status": "UNKNOWN"},
        ],
    )
    def test_invalid_shipments_are_rejected(
        self, invalid_shipment
    ):
        with pytest.raises(ScenarioValidationError):
            run_scenario({}, shipment=invalid_shipment)

    @pytest.mark.parametrize(
        "invalid_changes",
        [
            None,
            [],
            {"unknown_field": "value"},
            {"shipment_status": "UNKNOWN"},
            {"new_exception_severity": "EXTREME"},
            {"new_exception_status": "OPEN"},
            {"override_exception_severity": "EXTREME"},
        ],
    )
    def test_invalid_changes_are_rejected(
        self, invalid_changes
    ):
        with pytest.raises(ScenarioValidationError):
            run_scenario(invalid_changes)

    def test_invalid_delivery_date_is_rejected(self):
        with pytest.raises(ScenarioValidationError):
            run_scenario({
                "estimated_delivery_date": "2026-10-14"
            })

    def test_datetime_delivery_date_is_rejected(self):
        with pytest.raises(ScenarioValidationError):
            run_scenario({
                "estimated_delivery_date":
                    datetime(2026, 10, 14, 12, 0)
            })

    def test_invalid_exception_severity_is_rejected(self):
        with pytest.raises(ScenarioValidationError):
            run_scenario(
                {},
                exceptions=[
                    make_exception(severity="EXTREME")
                ],
            )

    def test_exception_from_other_shipment_is_rejected(self):
        with pytest.raises(ScenarioValidationError):
            run_scenario(
                {},
                exceptions=[
                    make_exception(shipment_id="SHP-OTHER")
                ],
            )

    def test_invalid_exception_status_is_rejected(self):
        with pytest.raises(ScenarioValidationError):
            run_scenario(
                {},
                exceptions=[
                    make_exception(status="UNKNOWN")
                ],
            )

    def test_invalid_assessment_date_is_rejected(self):
        with pytest.raises(ScenarioValidationError):
            analyze_risk_scenario(
                make_shipment(),
                [],
                {},
                "2026-10-21",
            )


class TestGovernance:

    def test_scenario_governance(self):
        assert SCENARIO_GOVERNANCE[
            "simulation_mode"
        ] == "SIMULATION"

        assert SCENARIO_GOVERNANCE[
            "evidence_classification"
        ] == "SYNTHETIC_UNVERIFIED"

        assert SCENARIO_GOVERNANCE[
            "authorization_status"
        ] == "NOT_AUTHORIZED"

        assert SCENARIO_GOVERNANCE[
            "scenario_mode"
        ] == "WHAT_IF_ANALYSIS"

        assert SCENARIO_GOVERNANCE[
            "database_modifications"
        ] == "NONE"

        assert SCENARIO_GOVERNANCE[
            "forecast_status"
        ] == "NOT_A_PREDICTION"

    def test_scenario_result_includes_governance(self):
        result = run_scenario({})

        assert result["governance"] == SCENARIO_GOVERNANCE

    def test_scenario_engine_does_not_import_database(self):
        import inspect
        import src.analysis.logistics_risk_scenarios as module

        source = inspect.getsource(module)

        assert "get_connection" not in source
        assert "INSERT INTO" not in source
        assert "UPDATE logistics." not in source
        assert "DELETE FROM" not in source
