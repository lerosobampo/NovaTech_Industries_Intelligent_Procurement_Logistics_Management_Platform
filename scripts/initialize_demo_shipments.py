
"""
NovaTech Industries
Demonstration Shipment Initializer — V1

Recreates one synthetic shipment and its completed exception
workflow using the existing application services.

Target database: novatech_demo ONLY.

Run from the project root:

    python scripts/initialize_demo_shipments.py --dry-run

    DB_NAME=novatech_demo python scripts/initialize_demo_shipments.py

IMPORTANT:
Existing service functions commit separate transactions.
A failure during initialization may leave partial records.
Do not automatically rerun after a failure.
"""

import argparse
import os
import sys
from datetime import date, datetime
from pathlib import Path

import psycopg


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.database import connection as database_connection
from src.database import shipment_tracking_service as tracking
from src.database import shipment_exception_service as exceptions


ALLOWED_DATABASE = "novatech_demo"

SHIPMENT_ID = "SHP-DEMO-001"
SUPPLIER_ID = "SUP001"
TRACKING_NUMBER = "NT-DEMO-001"

EVENT_TIMES = {
    "created": datetime(2026, 10, 19, 9, 0),
    "dispatched": datetime(2026, 10, 19, 11, 0),
    "in_transit": datetime(2026, 10, 20, 8, 0),
    "reported": datetime(2026, 10, 20, 9, 0),
    "assigned": datetime(2026, 10, 20, 9, 30),
    "investigating": datetime(2026, 10, 20, 10, 0),
    "corrective_action": datetime(2026, 10, 20, 11, 0),
    "resolved": datetime(2026, 10, 20, 14, 0),
    "closed": datetime(2026, 10, 20, 15, 0),
}


class DemoInitializationError(Exception):
    """Raised when demonstration initialization is unsafe."""


def get_safe_connection():
    """
    Connect only to the explicitly selected demonstration database.
    """

    configured_database = os.getenv("DB_NAME")

    if configured_database != ALLOWED_DATABASE:
        raise DemoInitializationError(
            f"Set DB_NAME={ALLOWED_DATABASE} explicitly. "
            "The original novatech database is not permitted."
        )

    connection = database_connection.get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database()")
            actual_database = cursor.fetchone()[0]

        if actual_database != ALLOWED_DATABASE:
            raise DemoInitializationError(
                "Unexpected database connection. "
                "Initialization cancelled."
            )

        return connection

    except Exception:
        connection.close()
        raise


def validate_demo_environment():
    """
    Check required records and ensure demonstration shipment
    and exception tables are empty before writing anything.
    """

    with get_safe_connection() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM procurement.suppliers
                WHERE supplier_id = %s
                """,
                (SUPPLIER_ID,),
            )

            if cursor.fetchone()[0] != 1:
                raise DemoInitializationError(
                    f"Required supplier {SUPPLIER_ID} "
                    "was not found."
                )

            tables = [
                "logistics.shipments",
                "logistics.shipment_events",
                "logistics.shipment_exceptions",
                "logistics.shipment_exception_events",
            ]

            for table in tables:
                schema_name, table_name = table.split(".")

                cursor.execute(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_schema = %s
                          AND table_name = %s
                    )
                    """,
                    (schema_name, table_name),
                )

                if not cursor.fetchone()[0]:
                    raise DemoInitializationError(
                        f"Required table missing: {table}"
                    )

                # These names come from a fixed internal list,
                # not from user-provided input.
                cursor.execute(
                    f"SELECT EXISTS (SELECT 1 FROM {table})"
                )

                if cursor.fetchone()[0]:
                    raise DemoInitializationError(
                        f"Table {table} is not empty. "
                        "Initialization cancelled to prevent "
                        "duplicate or partial demonstration data."
                    )

            print("[DB OK] Required supplier exists.")
            print("[DB OK] Shipment demonstration tables are empty.")


def validate_service_database_routing():
    """
    Ensure both service modules use the same database connection
    function, and the selected database is the demo database.
    """

    if tracking.get_connection is not database_connection.get_connection:
        raise DemoInitializationError(
            "Shipment tracking service uses an unexpected "
            "connection function."
        )

    if exceptions.get_connection is not database_connection.get_connection:
        raise DemoInitializationError(
            "Shipment exception service uses an unexpected "
            "connection function."
        )

    with get_safe_connection():
        pass

    print("[DB OK] Service connection routing verified.")


def initialize_demo():
    """Create the synthetic shipment and exception lifecycle."""

    validate_service_database_routing()
    validate_demo_environment()

    print("\nCreating demonstration shipment...")

    created_id = tracking.create_shipment(
        supplier_id=SUPPLIER_ID,
        carrier_name="NovaTech Demo Logistics",
        transport_mode="ROAD",
        origin_location="Rotterdam",
        destination_location="The Hague",
        estimated_delivery_date=date(2026, 10, 28),
        shipment_id=SHIPMENT_ID,
        tracking_number=TRACKING_NUMBER,
        event_timestamp=EVENT_TIMES["created"],
    )

    print(f"[CREATED] Shipment {created_id}")

    tracking.update_shipment_status(
        shipment_id=SHIPMENT_ID,
        new_status="DISPATCHED",
        event_timestamp=EVENT_TIMES["dispatched"],
        event_location="Rotterdam",
        event_description=(
            "Synthetic shipment dispatched from Rotterdam."
        ),
    )

    print("[TRACKING] DISPATCHED")

    tracking.update_shipment_status(
        shipment_id=SHIPMENT_ID,
        new_status="IN_TRANSIT",
        event_timestamp=EVENT_TIMES["in_transit"],
        event_location="Rotterdam",
        event_description=(
            "Synthetic shipment in transit to The Hague."
        ),
    )

    print("[TRACKING] IN_TRANSIT")

    print("\nCreating demonstration exception...")

    exception_id = exceptions.create_exception(
        shipment_id=SHIPMENT_ID,
        exception_type="DELIVERY_DELAY",
        severity="MEDIUM",
        description=(
            "Synthetic delivery delay reported for "
            "demonstration purposes."
        ),
        reported_by="DEMO_ANALYST",
        event_timestamp=EVENT_TIMES["reported"],
    )

    print(f"[EXCEPTION] Created exception {exception_id}")

    exceptions.assign_exception(
        exception_id=exception_id,
        assigned_to="DEMO_LOGISTICS_TEAM",
        recorded_by="DEMO_ANALYST",
        event_timestamp=EVENT_TIMES["assigned"],
    )

    print("[EXCEPTION] ASSIGNED")

    exceptions.start_investigation(
        exception_id=exception_id,
        recorded_by="DEMO_ANALYST",
        description=(
            "Investigation started for synthetic delivery delay."
        ),
        event_timestamp=EVENT_TIMES["investigating"],
    )

    print("[EXCEPTION] INVESTIGATION_STARTED")

    exceptions.record_corrective_action(
        exception_id=exception_id,
        corrective_action=(
            "Reviewed simulated carrier tracking information "
            "and updated the demonstration response plan."
        ),
        recorded_by="DEMO_ANALYST",
        event_timestamp=EVENT_TIMES["corrective_action"],
    )

    print("[EXCEPTION] CORRECTIVE_ACTION")

    exceptions.resolve_exception(
        exception_id=exception_id,
        resolution_notes=(
            "Synthetic delay investigation completed. "
            "No real-world action required."
        ),
        recorded_by="DEMO_ANALYST",
        event_timestamp=EVENT_TIMES["resolved"],
    )

    print("[EXCEPTION] RESOLVED")

    exceptions.close_exception(
        exception_id=exception_id,
        recorded_by="DEMO_ANALYST",
        description=(
            "Synthetic exception closed after review."
        ),
        event_timestamp=EVENT_TIMES["closed"],
    )

    print("[EXCEPTION] CLOSED")

    print("\nVerifying demonstration records...")

    with get_safe_connection() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT shipment_status
                FROM logistics.shipments
                WHERE shipment_id = %s
                """,
                (SHIPMENT_ID,),
            )

            shipment_row = cursor.fetchone()

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM logistics.shipment_events
                WHERE shipment_id = %s
                """,
                (SHIPMENT_ID,),
            )

            tracking_count = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT exception_status
                FROM logistics.shipment_exceptions
                WHERE exception_id = %s
                """,
                (exception_id,),
            )

            exception_row = cursor.fetchone()

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM logistics.shipment_exception_events
                WHERE exception_id = %s
                """,
                (exception_id,),
            )

            exception_event_count = cursor.fetchone()[0]

    if (
        shipment_row is None
        or shipment_row[0] != "IN_TRANSIT"
        or tracking_count != 3
        or exception_row is None
        or exception_row[0] != "CLOSED"
        or exception_event_count != 6
    ):
        raise DemoInitializationError(
            "Demonstration verification failed. "
            "Inspect the demo database before retrying."
        )

    print(f"Shipment: {SHIPMENT_ID} — IN_TRANSIT")
    print(f"Tracking events: {tracking_count}")
    print(f"Exception: {exception_id} — CLOSED")
    print(f"Exception audit events: {exception_event_count}")
    print("\nDemonstration initialization completed successfully.")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Initialize synthetic shipment demonstration "
            "records in novatech_demo."
        )
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Validate configuration without connecting "
            "to PostgreSQL or writing records."
        ),
    )

    args = parser.parse_args()

    try:
        if args.dry_run:
            print("NOVATECH — SHIPMENT INITIALIZER DRY RUN")
            print("---------------------------------------")
            print(f"Target database: {ALLOWED_DATABASE}")
            print(f"Shipment: {SHIPMENT_ID}")
            print(f"Supplier: {SUPPLIER_ID}")
            print("Tracking events: 3")
            print("Exception audit events: 6")
            print(
                "\nDRY RUN COMPLETE — "
                "No database connection or modifications."
            )
            return 0

        initialize_demo()
        return 0

    except (
        DemoInitializationError,
        psycopg.Error,
        tracking.ShipmentTrackingError,
        exceptions.ShipmentExceptionError,
    ) as error:
        print(f"\nINITIALIZATION FAILED: {error}", file=sys.stderr)
        print(
            "Existing service operations may already have committed. "
            "Inspect novatech_demo before attempting any retry.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
