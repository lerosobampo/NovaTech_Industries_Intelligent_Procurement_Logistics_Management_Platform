
"""
NovaTech Industries
Logistics Risk Scenario Analysis Engine — V1

Evaluate hypothetical shipment conditions without modifying
PostgreSQL records.

All data is synthetic and unverified.
Scenario results are analytical simulations, not predictions,
operational instructions, or purchasing authorizations.
"""

from copy import deepcopy
from datetime import date, datetime

from src.analysis.logistics_risk_intelligence import (
    assess_shipment_risk,
    _validate_as_of_date,
    GOVERNANCE,
)


ALLOWED_SHIPMENT_STATUSES = {
    "CREATED",
    "DISPATCHED",
    "IN_TRANSIT",
    "EXCEPTION",
    "DELIVERED",
    "CANCELLED",
}

ALLOWED_EXCEPTION_SEVERITIES = {
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
}

ALLOWED_EXCEPTION_STATUSES = {
    "OPEN",
    "INVESTIGATING",
    "RESOLVED",
    "CLOSED",
}

SCENARIO_GOVERNANCE = {
    **GOVERNANCE,
    "scenario_mode": "WHAT_IF_ANALYSIS",
    "database_modifications": "NONE",
    "forecast_status": "NOT_A_PREDICTION",
}


class ScenarioValidationError(ValueError):
    """Raised when hypothetical scenario inputs are invalid."""


def _validate_delivery_date(value):
    """Validate an optional estimated delivery date."""

    if value is None:
        return None

    if isinstance(value, datetime) or not isinstance(value, date):
        raise ScenarioValidationError(
            "Estimated delivery date must be a date object or None."
        )

    return value


def _validate_shipment(shipment):
    """Validate the minimum fields required for risk assessment."""

    if not isinstance(shipment, dict):
        raise ScenarioValidationError(
            "Shipment must be a dictionary."
        )

    shipment_id = shipment.get("shipment_id")

    if not isinstance(shipment_id, str) or not shipment_id.strip():
        raise ScenarioValidationError(
            "Shipment must have a non-empty shipment_id."
        )

    status = shipment.get("shipment_status")

    if status not in ALLOWED_SHIPMENT_STATUSES:
        raise ScenarioValidationError(
            f"Unsupported shipment status: {status}"
        )

    _validate_delivery_date(
        shipment.get("estimated_delivery_date")
    )


def _validate_exceptions(exceptions, shipment_id):
    """Validate exceptions belonging to the selected shipment."""

    if not isinstance(exceptions, list):
        raise ScenarioValidationError(
            "Exceptions must be supplied as a list."
        )

    for exception in exceptions:
        if not isinstance(exception, dict):
            raise ScenarioValidationError(
                "Each exception must be a dictionary."
            )

        if exception.get("shipment_id") != shipment_id:
            raise ScenarioValidationError(
                "All exceptions must belong to the selected shipment."
            )

        if exception.get("severity") not in ALLOWED_EXCEPTION_SEVERITIES:
            raise ScenarioValidationError(
                "Exception severity must be LOW, MEDIUM, HIGH, "
                "or CRITICAL."
            )

        if exception.get("exception_status") not in ALLOWED_EXCEPTION_STATUSES:
            raise ScenarioValidationError(
                "Unsupported exception status."
            )


def _validate_scenario_changes(changes):
    """Validate permitted hypothetical modifications."""

    if not isinstance(changes, dict):
        raise ScenarioValidationError(
            "Scenario changes must be a dictionary."
        )

    allowed_keys = {
        "shipment_status",
        "estimated_delivery_date",
        "new_exception_severity",
        "new_exception_status",
        "override_exception_severity",
    }

    unsupported = set(changes) - allowed_keys

    if unsupported:
        raise ScenarioValidationError(
            "Unsupported scenario changes: "
            + ", ".join(sorted(unsupported))
        )

    if "shipment_status" in changes:
        if changes["shipment_status"] not in ALLOWED_SHIPMENT_STATUSES:
            raise ScenarioValidationError(
                "Invalid hypothetical shipment status."
            )

    if "estimated_delivery_date" in changes:
        _validate_delivery_date(
            changes["estimated_delivery_date"]
        )

    if "new_exception_severity" in changes:
        if (
            changes["new_exception_severity"]
            not in ALLOWED_EXCEPTION_SEVERITIES
        ):
            raise ScenarioValidationError(
                "Invalid new exception severity."
            )

    if "new_exception_status" in changes:
        if (
            changes["new_exception_status"]
            not in ALLOWED_EXCEPTION_STATUSES
        ):
            raise ScenarioValidationError(
                "Invalid new exception status."
            )

        if "new_exception_severity" not in changes:
            raise ScenarioValidationError(
                "new_exception_status requires "
                "new_exception_severity."
            )

    if "override_exception_severity" in changes:
        if (
            changes["override_exception_severity"]
            not in ALLOWED_EXCEPTION_SEVERITIES
        ):
            raise ScenarioValidationError(
                "Invalid exception severity override."
            )


def analyze_risk_scenario(
    shipment,
    exceptions,
    changes,
    as_of_date=None,
):
    """
    Compare a baseline shipment assessment against a
    hypothetical scenario.

    Inputs are deep-copied to prevent mutation.

    Changes are applied in memory only.
    """
    try:
        assessment_date = _validate_as_of_date(as_of_date)
    except ValueError as error:
        raise ScenarioValidationError(str(error)) from error

    _validate_shipment(shipment)
    _validate_exceptions(exceptions, shipment["shipment_id"])
    _validate_scenario_changes(changes)

    baseline_shipment = deepcopy(shipment)
    baseline_exceptions = deepcopy(exceptions)

    scenario_shipment = deepcopy(shipment)
    scenario_exceptions = deepcopy(exceptions)

    if "shipment_status" in changes:
        scenario_shipment["shipment_status"] = changes[
            "shipment_status"
        ]

    if "estimated_delivery_date" in changes:
        scenario_shipment["estimated_delivery_date"] = changes[
            "estimated_delivery_date"
        ]

    if "override_exception_severity" in changes:
        for exception in scenario_exceptions:
            if exception["exception_status"] in {
                "OPEN",
                "INVESTIGATING",
            }:
                exception["severity"] = changes[
                    "override_exception_severity"
                ]

    if "new_exception_severity" in changes:
        scenario_exceptions.append({
            "shipment_id": shipment["shipment_id"],
            "severity": changes["new_exception_severity"],
            "exception_status": changes.get(
                "new_exception_status",
                "OPEN",
            ),
            "scenario_only": True,
        })

    baseline = assess_shipment_risk(
        baseline_shipment,
        baseline_exceptions,
        assessment_date,
    )

    scenario = assess_shipment_risk(
        scenario_shipment,
        scenario_exceptions,
        assessment_date,
    )

    score_change = (
        scenario["risk_score"] - baseline["risk_score"]
    )

    if score_change > 0:
        direction = "INCREASED"
    elif score_change < 0:
        direction = "DECREASED"
    else:
        direction = "UNCHANGED"

    return {
        "shipment_id": shipment["shipment_id"],
        "assessment_date": assessment_date,
        "baseline": baseline,
        "scenario": scenario,
        "score_change": score_change,
        "risk_direction": direction,
        "scenario_changes": deepcopy(changes),
        "governance": SCENARIO_GOVERNANCE.copy(),
    }


if __name__ == "__main__":
    demo_shipment = {
        "shipment_id": "SHP-SCENARIO-DEMO",
        "shipment_status": "IN_TRANSIT",
        "estimated_delivery_date": date(2026, 10, 28),
    }

    demo_exceptions = []

    demo_changes = {
        "shipment_status": "EXCEPTION",
        "estimated_delivery_date": date(2026, 10, 14),
        "new_exception_severity": "HIGH",
    }

    result = analyze_risk_scenario(
        shipment=demo_shipment,
        exceptions=demo_exceptions,
        changes=demo_changes,
        as_of_date=date(2026, 10, 21),
    )

    print("\nNOVATECH — LOGISTICS RISK SCENARIO ANALYSIS")
    print("------------------------------------------")
    print("Shipment:", result["shipment_id"])
    print("Baseline score:", result["baseline"]["risk_score"])
    print("Baseline level:", result["baseline"]["risk_level"])
    print("Scenario score:", result["scenario"]["risk_score"])
    print("Scenario level:", result["scenario"]["risk_level"])
    print("Score change:", result["score_change"])
    print("Risk direction:", result["risk_direction"])
    print("Governance:", result["governance"])
