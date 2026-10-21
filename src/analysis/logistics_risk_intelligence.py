
"""
NovaTech Industries
Logistics Risk Intelligence Engine — V1

Read-only shipment risk assessment using PostgreSQL data.

All outputs are simulation-only, based on synthetic,
unverified evidence. Risk scores are heuristic indicators,
not calibrated probabilities or operational authorizations.
"""

from datetime import date, datetime

from src.database.connection import get_connection


SEVERITY_POINTS = {
    "LOW": 10,
    "MEDIUM": 20,
    "HIGH": 35,
    "CRITICAL": 50,
}

RISK_LEVELS = (
    (70, "CRITICAL"),
    (40, "HIGH"),
    (20, "MEDIUM"),
    (0, "LOW"),
)

ACTIVE_STATUSES = {
    "CREATED",
    "DISPATCHED",
    "IN_TRANSIT",
    "EXCEPTION",
}

UNRESOLVED_STATUSES = {
    "OPEN",
    "INVESTIGATING",
}

GOVERNANCE = {
    "simulation_mode": "SIMULATION",
    "evidence_classification": "SYNTHETIC_UNVERIFIED",
    "authorization_status": "NOT_AUTHORIZED",
    "risk_model": "RULE_BASED_HEURISTIC_V1",
}


def _validate_as_of_date(as_of_date):
    """Validate the date used to evaluate shipment risk."""
    if as_of_date is None:
        return date.today()

    if isinstance(as_of_date, datetime):
        raise ValueError("as_of_date must be a date, not datetime.")

    if not isinstance(as_of_date, date):
        raise ValueError("as_of_date must be a date object.")

    return as_of_date


def _risk_level(score):
    """Classify a numeric risk score."""
    for threshold, level in RISK_LEVELS:
        if score >= threshold:
            return level

    return "LOW"


def _overdue_points(days_overdue):
    """Calculate risk points for an overdue shipment."""
    if days_overdue >= 7:
        return 45

    if days_overdue >= 3:
        return 35

    if days_overdue >= 1:
        return 20

    return 0


def assess_shipment_risk(shipment, exceptions, as_of_date):
    """
    Assess one shipment without modifying any records.

    A resolved or closed exception remains visible in the
    exception history but does not contribute active risk.
    """
    as_of_date = _validate_as_of_date(as_of_date)

    shipment_id = shipment["shipment_id"]
    shipment_status = shipment["shipment_status"]

    estimated_delivery = shipment.get(
        "estimated_delivery_date"
    )

    risk_score = 0
    risk_factors = []
    days_overdue = 0

    if (
        shipment_status in ACTIVE_STATUSES
        and estimated_delivery is not None
        and as_of_date > estimated_delivery
    ):
        days_overdue = (
            as_of_date - estimated_delivery
        ).days

        points = _overdue_points(days_overdue)
        risk_score += points

        risk_factors.append({
            "factor": "OVERDUE_SHIPMENT",
            "points": points,
            "description": (
                f"Shipment is {days_overdue} calendar "
                "day(s) past estimated delivery."
            ),
        })

    if shipment_status == "EXCEPTION":
        risk_score += 25

        risk_factors.append({
            "factor": "SHIPMENT_EXCEPTION_STATUS",
            "points": 25,
            "description": (
                "Shipment lifecycle status is EXCEPTION."
            ),
        })

    unresolved = [
        exception
        for exception in exceptions
        if (
            exception["shipment_id"] == shipment_id
            and exception["exception_status"]
            in UNRESOLVED_STATUSES
        )
    ]

    highest_severity = None

    if unresolved:
        highest_severity = max(
            (
                exception["severity"]
                for exception in unresolved
            ),
            key=lambda severity: SEVERITY_POINTS[severity],
        )

        points = SEVERITY_POINTS[highest_severity]
        risk_score += points

        risk_factors.append({
            "factor": "UNRESOLVED_EXCEPTION",
            "points": points,
            "description": (
                f"{len(unresolved)} unresolved exception(s); "
                f"highest severity: {highest_severity}."
            ),
        })

    risk_score = min(risk_score, 100)

    return {
        "shipment_id": shipment_id,
        "shipment_status": shipment_status,
        "estimated_delivery_date": estimated_delivery,
        "assessment_date": as_of_date,
        "days_overdue": days_overdue,
        "unresolved_exception_count": len(unresolved),
        "highest_exception_severity": highest_severity,
        "risk_score": risk_score,
        "risk_level": _risk_level(risk_score),
        "risk_factors": risk_factors,
        **GOVERNANCE,
    }


def generate_logistics_risk_intelligence(as_of_date=None):
    """
    Load shipment and exception records from PostgreSQL,
    then calculate risk indicators for every shipment.

    Read-only: no database inserts, updates, or deletes.
    """
    as_of_date = _validate_as_of_date(as_of_date)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    shipment_id,
                    shipment_status,
                    estimated_delivery_date
                FROM logistics.shipments
                ORDER BY shipment_id
                """
            )

            columns = [
                column.name for column in cur.description
            ]

            shipments = [
                dict(zip(columns, row))
                for row in cur.fetchall()
            ]

            cur.execute(
                """
                SELECT
                    exception_id,
                    shipment_id,
                    exception_status,
                    severity
                FROM logistics.shipment_exceptions
                WHERE exception_status IN (
                    'OPEN', 'INVESTIGATING'
                )
                ORDER BY shipment_id, exception_id
                """
            )

            columns = [
                column.name for column in cur.description
            ]

            exceptions = [
                dict(zip(columns, row))
                for row in cur.fetchall()
            ]

    assessments = [
        assess_shipment_risk(
            shipment,
            exceptions,
            as_of_date,
        )
        for shipment in shipments
    ]

    assessments.sort(
        key=lambda item: (
            -item["risk_score"],
            item["shipment_id"],
        )
    )

    risk_distribution = {
        level: sum(
            item["risk_level"] == level
            for item in assessments
        )
        for level in (
            "LOW", "MEDIUM", "HIGH", "CRITICAL"
        )
    }

    return {
        "assessment_date": as_of_date,
        "total_shipments": len(assessments),
        "high_priority_shipments": sum(
            item["risk_level"] in {"HIGH", "CRITICAL"}
            for item in assessments
        ),
        "risk_distribution": risk_distribution,
        "shipments": assessments,
        "governance": GOVERNANCE.copy(),
    }


if __name__ == "__main__":
    report = generate_logistics_risk_intelligence()

    print("\nNOVATECH — LOGISTICS RISK INTELLIGENCE")
    print("-------------------------------------")
    print("Assessment date:", report["assessment_date"])
    print("Total shipments:", report["total_shipments"])
    print(
        "High-priority shipments:",
        report["high_priority_shipments"],
    )
    print("Risk distribution:", report["risk_distribution"])

    for shipment in report["shipments"]:
        print(
            shipment["shipment_id"],
            "|",
            shipment["risk_level"],
            "| Score:",
            shipment["risk_score"],
            "| Unresolved exceptions:",
            shipment["unresolved_exception_count"],
        )

    print("\nGovernance:", report["governance"])
