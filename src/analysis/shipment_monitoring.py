
"""
NovaTech Industries
Logistics Intelligence — Shipment Monitoring Analytics V1

Analyzes synthetic shipment tracking records to produce:
- Shipment status KPIs
- Active and overdue shipment monitoring
- Delivery performance
- Carrier performance
- Operational alerts
- Data quality checks

All records are synthetic and unverified.
No real-world shipping or purchasing actions are authorized.
"""

from collections import Counter, defaultdict
from datetime import date, datetime

from src.database.shipment_tracking_service import list_shipments


ACTIVE_STATUSES = {"DISPATCHED", "IN_TRANSIT"}
OPEN_STATUSES = {"CREATED", "DISPATCHED", "IN_TRANSIT", "EXCEPTION"}
TERMINAL_STATUSES = {"DELIVERED", "CANCELLED"}

GOVERNANCE = {
    "simulation_mode": "SIMULATION",
    "evidence_classification": "SYNTHETIC_UNVERIFIED",
    "authorization_status": "NOT_AUTHORIZED",
}


def _as_date(value):
    """Convert a date or datetime to a date, or return None."""
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    return None


def _percentage(numerator, denominator):
    """Return a percentage rounded to two decimal places."""
    if denominator == 0:
        return 0.0

    return round((numerator / denominator) * 100, 2)


def calculate_shipment_monitoring(shipments, as_of_date=None):
    """
    Calculate operational shipment monitoring metrics.

    Parameters
    ----------
    shipments : list[dict]
        Shipment records from PostgreSQL or test fixtures.

    as_of_date : datetime.date, optional
        Date used to determine whether open shipments are overdue.
        Defaults to the current date.

    Returns
    -------
    dict
        Shipment KPIs, carrier metrics, alerts, data-quality
        findings, and governance metadata.
    """

    if as_of_date is None:
        as_of_date = date.today()

    if not isinstance(as_of_date, date) or isinstance(
        as_of_date, datetime
    ):
        raise ValueError("as_of_date must be a datetime.date.")

    shipments = list(shipments)

    status_counts = Counter()
    carrier_groups = defaultdict(list)

    active_shipments = []
    overdue_shipments = []
    exception_shipments = []
    alerts = []
    data_quality_issues = []

    delivered_count = 0
    on_time_deliveries = 0
    late_deliveries = 0
    total_delivery_delay_days = 0

    for shipment in shipments:
        shipment_id = shipment.get("shipment_id")
        status = shipment.get("shipment_status")
        carrier = shipment.get("carrier_name") or "UNKNOWN"

        estimated_date = _as_date(
            shipment.get("estimated_delivery_date")
        )
        actual_date = _as_date(
            shipment.get("actual_delivery_date")
        )
        dispatch_date = _as_date(
            shipment.get("dispatch_date")
        )

        status_counts[status] += 1
        carrier_groups[carrier].append(shipment)

        # -----------------------------
        # Governance and data quality
        # -----------------------------

        for field, expected in GOVERNANCE.items():
            if shipment.get(field) != expected:
                data_quality_issues.append({
                    "shipment_id": shipment_id,
                    "issue_type": "GOVERNANCE_MISMATCH",
                    "field": field,
                    "description": (
                        f"Expected {expected}; "
                        f"found {shipment.get(field)}"
                    ),
                })

        if estimated_date is None:
            data_quality_issues.append({
                "shipment_id": shipment_id,
                "issue_type": "MISSING_ESTIMATED_DELIVERY",
                "field": "estimated_delivery_date",
                "description": "Estimated delivery date is missing.",
            })

        if status in ACTIVE_STATUSES and dispatch_date is None:
            data_quality_issues.append({
                "shipment_id": shipment_id,
                "issue_type": "MISSING_DISPATCH_DATE",
                "field": "dispatch_date",
                "description": (
                    "Active shipment has no dispatch date."
                ),
            })

        if status == "DELIVERED" and actual_date is None:
            data_quality_issues.append({
                "shipment_id": shipment_id,
                "issue_type": "MISSING_ACTUAL_DELIVERY",
                "field": "actual_delivery_date",
                "description": (
                    "Delivered shipment has no actual delivery date."
                ),
            })

        if status != "DELIVERED" and actual_date is not None:
            data_quality_issues.append({
                "shipment_id": shipment_id,
                "issue_type": "UNEXPECTED_ACTUAL_DELIVERY",
                "field": "actual_delivery_date",
                "description": (
                    "Non-delivered shipment has an actual "
                    "delivery date."
                ),
            })

        if (
            dispatch_date is not None
            and actual_date is not None
            and actual_date < dispatch_date
        ):
            data_quality_issues.append({
                "shipment_id": shipment_id,
                "issue_type": "INVALID_DELIVERY_SEQUENCE",
                "field": "actual_delivery_date",
                "description": (
                    "Actual delivery precedes dispatch."
                ),
            })

        # -----------------------------
        # Active shipment monitoring
        # -----------------------------

        if status in ACTIVE_STATUSES:
            active_shipments.append({
                "shipment_id": shipment_id,
                "supplier_id": shipment.get("supplier_id"),
                "carrier_name": carrier,
                "shipment_status": status,
                "estimated_delivery_date": estimated_date,
                "destination_location": shipment.get(
                    "destination_location"
                ),
            })

        # -----------------------------
        # Overdue shipment detection
        # -----------------------------

        if (
            status in OPEN_STATUSES
            and estimated_date is not None
            and estimated_date < as_of_date
        ):
            days_overdue = (as_of_date - estimated_date).days

            overdue_record = {
                "shipment_id": shipment_id,
                "supplier_id": shipment.get("supplier_id"),
                "carrier_name": carrier,
                "shipment_status": status,
                "estimated_delivery_date": estimated_date,
                "days_overdue": days_overdue,
            }

            overdue_shipments.append(overdue_record)

            alerts.append({
                "shipment_id": shipment_id,
                "alert_type": "OVERDUE_SHIPMENT",
                "severity": "HIGH",
                "description": (
                    f"Shipment is {days_overdue} day(s) overdue."
                ),
            })

        # -----------------------------
        # Exception detection
        # -----------------------------

        if status == "EXCEPTION":
            exception_shipments.append({
                "shipment_id": shipment_id,
                "supplier_id": shipment.get("supplier_id"),
                "carrier_name": carrier,
                "shipment_status": status,
            })

            alerts.append({
                "shipment_id": shipment_id,
                "alert_type": "SHIPMENT_EXCEPTION",
                "severity": "HIGH",
                "description": (
                    "Shipment requires operational review."
                ),
            })

        # -----------------------------
        # Completed delivery analysis
        # -----------------------------

        if status == "DELIVERED" and actual_date is not None:
            delivered_count += 1

            if estimated_date is not None:
                delay_days = max(
                    0,
                    (actual_date - estimated_date).days,
                )

                total_delivery_delay_days += delay_days

                if delay_days == 0:
                    on_time_deliveries += 1
                else:
                    late_deliveries += 1

    # -----------------------------
    # Carrier performance
    # -----------------------------

    carrier_performance = []

    for carrier, carrier_shipments in sorted(
        carrier_groups.items()
    ):
        completed = 0
        on_time = 0
        late = 0
        active = 0
        exceptions = 0
        total_delay = 0

        for shipment in carrier_shipments:
            status = shipment.get("shipment_status")
            estimated_date = _as_date(
                shipment.get("estimated_delivery_date")
            )
            actual_date = _as_date(
                shipment.get("actual_delivery_date")
            )

            if status in ACTIVE_STATUSES:
                active += 1

            if status == "EXCEPTION":
                exceptions += 1

            if (
                status == "DELIVERED"
                and actual_date is not None
            ):
                completed += 1

                if estimated_date is not None:
                    delay = max(
                        0,
                        (actual_date - estimated_date).days,
                    )

                    total_delay += delay

                    if delay == 0:
                        on_time += 1
                    else:
                        late += 1

        evaluated_deliveries = on_time + late

        carrier_performance.append({
            "carrier_name": carrier,
            "total_shipments": len(carrier_shipments),
            "completed_deliveries": completed,
            "evaluated_deliveries": evaluated_deliveries,
            "on_time_deliveries": on_time,
            "late_deliveries": late,
            "on_time_rate_pct": _percentage(
                on_time, evaluated_deliveries
            ),
            "average_delay_days": round(
                total_delay / evaluated_deliveries, 2
            ) if evaluated_deliveries else 0.0,
            "active_shipments": active,
            "exception_shipments": exceptions,
            "evidence_classification": (
                "SYNTHETIC_UNVERIFIED"
            ),
        })

    evaluated_deliveries = (
        on_time_deliveries + late_deliveries
    )

    kpis = {
        "total_shipments": len(shipments),
        "active_shipments": len(active_shipments),
        "open_shipments": sum(
            status_counts[status]
            for status in OPEN_STATUSES
        ),
        "overdue_shipments": len(overdue_shipments),
        "exception_shipments": len(exception_shipments),
        "delivered_shipments": delivered_count,
        "cancelled_shipments": status_counts["CANCELLED"],
        "evaluated_deliveries": evaluated_deliveries,
        "on_time_deliveries": on_time_deliveries,
        "late_deliveries": late_deliveries,
        "on_time_delivery_rate_pct": _percentage(
            on_time_deliveries,
            evaluated_deliveries,
        ),
        "average_delay_days": round(
            total_delivery_delay_days / evaluated_deliveries,
            2,
        ) if evaluated_deliveries else 0.0,
        "operational_alerts": len(alerts),
        "data_quality_issues": len(data_quality_issues),
    }

    return {
        "as_of_date": as_of_date,
        "kpis": kpis,
        "status_distribution": dict(status_counts),
        "active_shipments": active_shipments,
        "overdue_shipments": sorted(
            overdue_shipments,
            key=lambda record: record["days_overdue"],
            reverse=True,
        ),
        "exception_shipments": exception_shipments,
        "carrier_performance": carrier_performance,
        "alerts": alerts,
        "data_quality_issues": data_quality_issues,
        "governance": GOVERNANCE.copy(),
    }


def generate_shipment_monitoring(as_of_date=None):
    """
    Load shipment records from PostgreSQL and generate
    operational monitoring analytics.
    """

    shipments = list_shipments()

    return calculate_shipment_monitoring(
        shipments,
        as_of_date=as_of_date,
    )


if __name__ == "__main__":
    results = generate_shipment_monitoring()

    print("\nNOVATECH — SHIPMENT MONITORING")
    print("=" * 55)

    print("\nKPIs")
    for metric, value in results["kpis"].items():
        print(f"{metric}: {value}")

    print("\nSTATUS DISTRIBUTION")
    for status, count in sorted(
        results["status_distribution"].items()
    ):
        print(f"{status}: {count}")

    print("\nCARRIER PERFORMANCE")
    for carrier in results["carrier_performance"]:
        print(
            f"{carrier['carrier_name']} | "
            f"Shipments: {carrier['total_shipments']} | "
            f"On-time: {carrier['on_time_rate_pct']}% | "
            f"Active: {carrier['active_shipments']}"
        )

    print("\nGOVERNANCE")
    for field, value in results["governance"].items():
        print(f"{field}: {value}")
