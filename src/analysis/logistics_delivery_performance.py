
"""
NovaTech Industries
Logistics Intelligence — Supplier Delivery Performance V1

Calculates historical supplier delivery performance using
PostgreSQL delivery records.

Data classification: SYNTHETIC_UNVERIFIED
Read-only analytics. No purchasing authorization.
"""

from collections import defaultdict
from statistics import mean

from src.database.connection import get_connection


def load_delivery_records():
    """Read supplier delivery records from PostgreSQL."""

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    delivery_id,
                    supplier_id,
                    planned_delivery_date,
                    actual_delivery_date,
                    on_time,
                    status
                FROM logistics.supplier_deliveries
                ORDER BY supplier_id, delivery_id
                """
            )

            columns = [
                column.name
                for column in cur.description
            ]

            return [
                dict(zip(columns, record))
                for record in cur.fetchall()
            ]


def calculate_delivery_performance(deliveries):
    """Calculate historical delivery KPIs by supplier."""

    grouped = defaultdict(list)

    for delivery in deliveries:
        grouped[delivery["supplier_id"]].append(delivery)

    results = []

    for supplier_id, records in sorted(grouped.items()):

        completed = [
            record
            for record in records
            if record["status"] == "COMPLETED"
            and record["planned_delivery_date"] is not None
            and record["actual_delivery_date"] is not None
        ]

        total_completed = len(completed)
        on_time_count = 0
        late_count = 0
        flag_mismatches = 0
        delays = []

        for record in completed:

            days_difference = (
                record["actual_delivery_date"]
                - record["planned_delivery_date"]
            ).days

            calculated_on_time = days_difference <= 0

            if calculated_on_time:
                on_time_count += 1
            else:
                late_count += 1

            delays.append(max(0, days_difference))

            if (
                record["on_time"] is not None
                and record["on_time"] != calculated_on_time
            ):
                flag_mismatches += 1

        on_time_rate = (
            round(on_time_count / total_completed * 100, 2)
            if total_completed
            else None
        )

        average_delay = (
            round(mean(delays), 2)
            if delays
            else None
        )

        maximum_delay = (
            max(delays)
            if delays
            else None
        )

        results.append(
            {
                "supplier_id": supplier_id,
                "total_delivery_records": len(records),
                "completed_deliveries": total_completed,
                "on_time_deliveries": on_time_count,
                "late_deliveries": late_count,
                "on_time_delivery_rate_pct": on_time_rate,
                "average_delay_days": average_delay,
                "maximum_delay_days": maximum_delay,
                "on_time_flag_mismatches": flag_mismatches,
                "evidence_classification": "SYNTHETIC_UNVERIFIED",
            }
        )

    return results


def generate_delivery_performance():
    """Load and analyze delivery performance."""

    deliveries = load_delivery_records()

    return calculate_delivery_performance(deliveries)


if __name__ == "__main__":

    results = generate_delivery_performance()

    print("\nNOVATECH — SUPPLIER DELIVERY PERFORMANCE")
    print("=" * 65)

    for supplier in results:
        print(
            f"{supplier['supplier_id']} | "
            f"Completed: {supplier['completed_deliveries']} | "
            f"On-time: {supplier['on_time_delivery_rate_pct']}% | "
            f"Late: {supplier['late_deliveries']} | "
            f"Avg delay: {supplier['average_delay_days']} days | "
            f"Flag mismatches: {supplier['on_time_flag_mismatches']}"
        )

    print("\nEvidence: SYNTHETIC_UNVERIFIED")
    print("Purchasing authorization: NOT_AUTHORIZED")
