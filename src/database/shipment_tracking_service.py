
"""
NovaTech Industries
Logistics Intelligence — Shipment Tracking Service V1

Features:
- Create simulated shipments
- Enforce shipment lifecycle transitions
- Maintain chronological tracking history
- Prevent duplicate shipment IDs and tracking events
- Update shipment status and events atomically
- Preserve simulation-only governance

No real carrier bookings or purchasing authorization.
"""

from datetime import date, datetime, time
from uuid import uuid4

from psycopg.errors import UniqueViolation

from src.database.connection import get_connection


VALID_STATUSES = {
    "CREATED",
    "DISPATCHED",
    "IN_TRANSIT",
    "DELIVERED",
    "EXCEPTION",
    "CANCELLED",
}

ALLOWED_TRANSITIONS = {
    "CREATED": {"DISPATCHED", "CANCELLED"},
    "DISPATCHED": {"IN_TRANSIT", "EXCEPTION", "CANCELLED"},
    "IN_TRANSIT": {"DELIVERED", "EXCEPTION"},
    "EXCEPTION": {"IN_TRANSIT", "CANCELLED"},
    "DELIVERED": set(),
    "CANCELLED": set(),
}

VALID_TRANSPORT_MODES = {
    "ROAD",
    "RAIL",
    "AIR",
    "SEA",
}


class ShipmentTrackingError(ValueError):
    """Raised when shipment data or a status change is invalid."""


def _required_text(value, field_name):
    if not isinstance(value, str) or not value.strip():
        raise ShipmentTrackingError(
            f"{field_name} must be a non-empty string."
        )
    return value.strip()


def _validate_date(value, field_name):
    if not isinstance(value, date) or isinstance(value, datetime):
        raise ShipmentTrackingError(
            f"{field_name} must be a datetime.date value."
        )
    return value


def _validate_timestamp(value):
    if not isinstance(value, datetime):
        raise ShipmentTrackingError(
            "event_timestamp must be a datetime value."
        )

    if value.tzinfo is not None:
        raise ShipmentTrackingError(
            "event_timestamp must be timezone-naive, "
            "matching the database TIMESTAMP columns."
        )

    return value


def _fetch_shipment(cur, shipment_id, lock=False):
    query = """
        SELECT
            shipment_id,
            supplier_id,
            delivery_id,
            tracking_number,
            carrier_name,
            transport_mode,
            origin_location,
            destination_location,
            dispatch_date,
            estimated_delivery_date,
            actual_delivery_date,
            shipment_status,
            simulation_mode,
            evidence_classification,
            authorization_status,
            created_at,
            updated_at
        FROM logistics.shipments
        WHERE shipment_id = %s
    """

    if lock:
        query += " FOR UPDATE"

    cur.execute(query, (shipment_id,))

    if cur.description is None:
        return None

    columns = [column.name for column in cur.description]
    record = cur.fetchone()

    return dict(zip(columns, record)) if record else None


def create_shipment(
    supplier_id,
    carrier_name,
    transport_mode,
    origin_location,
    destination_location,
    estimated_delivery_date,
    shipment_id=None,
    tracking_number=None,
    delivery_id=None,
    event_timestamp=None,
):
    """Create a simulated shipment and its initial tracking event."""

    supplier_id = _required_text(supplier_id, "supplier_id")
    carrier_name = _required_text(carrier_name, "carrier_name")
    origin_location = _required_text(
        origin_location, "origin_location"
    )
    destination_location = _required_text(
        destination_location, "destination_location"
    )

    transport_mode = _required_text(
        transport_mode, "transport_mode"
    ).upper()

    if transport_mode not in VALID_TRANSPORT_MODES:
        raise ShipmentTrackingError(
            f"Invalid transport mode: {transport_mode}"
        )

    estimated_delivery_date = _validate_date(
        estimated_delivery_date,
        "estimated_delivery_date",
    )

    shipment_id = (
        _required_text(shipment_id, "shipment_id")
        if shipment_id is not None
        else f"SHP-{uuid4().hex[:20].upper()}"
    )

    if tracking_number is not None:
        tracking_number = _required_text(
            tracking_number, "tracking_number"
        )

    if delivery_id is not None:
        delivery_id = _required_text(
            delivery_id, "delivery_id"
        )

    event_timestamp = _validate_timestamp(
        event_timestamp
        if event_timestamp is not None
        else datetime.now()
    )

    if estimated_delivery_date < event_timestamp.date():
        raise ShipmentTrackingError(
            "Estimated delivery date cannot precede "
            "the shipment creation event date."
        )

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT 1
                    FROM procurement.suppliers
                    WHERE supplier_id = %s
                    """,
                    (supplier_id,),
                )

                if cur.fetchone() is None:
                    raise ShipmentTrackingError(
                        f"Unknown supplier: {supplier_id}"
                    )

                if delivery_id is not None:
                    cur.execute(
                        """
                        SELECT supplier_id
                        FROM logistics.supplier_deliveries
                        WHERE delivery_id = %s
                        """,
                        (delivery_id,),
                    )

                    delivery = cur.fetchone()

                    if delivery is None:
                        raise ShipmentTrackingError(
                            f"Unknown delivery: {delivery_id}"
                        )

                    if delivery[0] != supplier_id:
                        raise ShipmentTrackingError(
                            "Delivery and shipment supplier IDs "
                            "must match."
                        )

                cur.execute(
                    """
                    INSERT INTO logistics.shipments (
                        shipment_id,
                        supplier_id,
                        delivery_id,
                        tracking_number,
                        carrier_name,
                        transport_mode,
                        origin_location,
                        destination_location,
                        estimated_delivery_date,
                        shipment_status,
                        simulation_mode,
                        evidence_classification,
                        authorization_status,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        'CREATED',
                        'SIMULATION',
                        'SYNTHETIC_UNVERIFIED',
                        'NOT_AUTHORIZED',
                        %s, %s
                    )
                    """,
                    (
                        shipment_id,
                        supplier_id,
                        delivery_id,
                        tracking_number,
                        carrier_name,
                        transport_mode,
                        origin_location,
                        destination_location,
                        estimated_delivery_date,
                        event_timestamp,
                        event_timestamp,
                    ),
                )

                cur.execute(
                    """
                    INSERT INTO logistics.shipment_events (
                        shipment_id,
                        event_timestamp,
                        event_type,
                        event_location,
                        event_description,
                        recorded_by,
                        simulation_mode
                    )
                    VALUES (
                        %s, %s, 'CREATED', %s, %s,
                        'SYSTEM_SIMULATION', 'SIMULATION'
                    )
                    """,
                    (
                        shipment_id,
                        event_timestamp,
                        origin_location,
                        "Synthetic shipment record created.",
                    ),
                )

    except UniqueViolation as error:
        raise ShipmentTrackingError(
            "Shipment ID, tracking number, or tracking event "
            "already exists."
        ) from error

    return shipment_id


def update_shipment_status(
    shipment_id,
    new_status,
    event_timestamp,
    event_location,
    event_description,
    recorded_by="SYSTEM_SIMULATION",
):
    """
    Apply a valid status transition and append a tracking event.

    The shipment row is locked during the transaction to prevent
    concurrent status updates from bypassing transition checks.
    """

    shipment_id = _required_text(shipment_id, "shipment_id")

    new_status = _required_text(
        new_status, "new_status"
    ).upper()

    if new_status not in VALID_STATUSES:
        raise ShipmentTrackingError(
            f"Invalid shipment status: {new_status}"
        )

    event_timestamp = _validate_timestamp(event_timestamp)

    event_description = _required_text(
        event_description, "event_description"
    )

    recorded_by = _required_text(recorded_by, "recorded_by")

    if event_location is not None:
        event_location = _required_text(
            event_location, "event_location"
        )

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:

                shipment = _fetch_shipment(
                    cur, shipment_id, lock=True
                )

                if shipment is None:
                    raise ShipmentTrackingError(
                        f"Unknown shipment: {shipment_id}"
                    )

                current_status = shipment["shipment_status"]

                if new_status not in ALLOWED_TRANSITIONS[
                    current_status
                ]:
                    raise ShipmentTrackingError(
                        f"Invalid transition: "
                        f"{current_status} -> {new_status}"
                    )

                cur.execute(
                    """
                    SELECT MAX(event_timestamp)
                    FROM logistics.shipment_events
                    WHERE shipment_id = %s
                    """,
                    (shipment_id,),
                )

                latest_timestamp = cur.fetchone()[0]

                if (
                    latest_timestamp is not None
                    and event_timestamp <= latest_timestamp
                ):
                    raise ShipmentTrackingError(
                        "Tracking event timestamp must be later "
                        "than the previous event."
                    )

                dispatch_date = shipment["dispatch_date"]
                actual_delivery_date = shipment[
                    "actual_delivery_date"
                ]

                if new_status == "DISPATCHED":
                    dispatch_date = event_timestamp.date()

                    if (
                        dispatch_date
                        > shipment["estimated_delivery_date"]
                    ):
                        raise ShipmentTrackingError(
                            "Dispatch date cannot be after the "
                            "estimated delivery date under the "
                            "current schema."
                        )

                if new_status == "DELIVERED":
                    actual_delivery_date = event_timestamp.date()

                    if dispatch_date is None:
                        raise ShipmentTrackingError(
                            "A shipment must be dispatched "
                            "before delivery."
                        )

                    if actual_delivery_date < dispatch_date:
                        raise ShipmentTrackingError(
                            "Actual delivery cannot precede "
                            "dispatch."
                        )

                cur.execute(
                    """
                    UPDATE logistics.shipments
                    SET
                        shipment_status = %s,
                        dispatch_date = %s,
                        actual_delivery_date = %s,
                        updated_at = %s
                    WHERE shipment_id = %s
                    """,
                    (
                        new_status,
                        dispatch_date,
                        actual_delivery_date,
                        event_timestamp,
                        shipment_id,
                    ),
                )

                cur.execute(
                    """
                    INSERT INTO logistics.shipment_events (
                        shipment_id,
                        event_timestamp,
                        event_type,
                        event_location,
                        event_description,
                        recorded_by,
                        simulation_mode
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, 'SIMULATION'
                    )
                    """,
                    (
                        shipment_id,
                        event_timestamp,
                        new_status,
                        event_location,
                        event_description,
                        recorded_by,
                    ),
                )

    except UniqueViolation as error:
        raise ShipmentTrackingError(
            "Duplicate shipment tracking event."
        ) from error

    return new_status


def get_shipment(shipment_id):
    """Retrieve one shipment without modifying it."""

    shipment_id = _required_text(shipment_id, "shipment_id")

    with get_connection() as conn:
        with conn.cursor() as cur:
            return _fetch_shipment(cur, shipment_id)


def get_shipment_events(shipment_id):
    """Retrieve a shipment's chronological tracking history."""

    shipment_id = _required_text(shipment_id, "shipment_id")

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    event_id,
                    shipment_id,
                    event_timestamp,
                    event_type,
                    event_location,
                    event_description,
                    recorded_by,
                    simulation_mode,
                    created_at
                FROM logistics.shipment_events
                WHERE shipment_id = %s
                ORDER BY event_timestamp, event_id
                """,
                (shipment_id,),
            )

            columns = [
                column.name
                for column in cur.description
            ]

            return [
                dict(zip(columns, row))
                for row in cur.fetchall()
            ]



def list_shipments(status=None):
    """List shipments, optionally filtered by status."""

    if status is not None:
        status = _required_text(status, "status").upper()

        if status not in VALID_STATUSES:
            raise ShipmentTrackingError(
                f"Invalid shipment status: {status}"
            )

    query = """
        SELECT
            shipment_id,
            supplier_id,
            tracking_number,
            carrier_name,
            transport_mode,
            origin_location,
            destination_location,
            dispatch_date,
            estimated_delivery_date,
            actual_delivery_date,
            shipment_status,
            simulation_mode,
            evidence_classification,
            authorization_status
        FROM logistics.shipments
    """

    parameters = ()

    if status is not None:
        query += " WHERE shipment_status = %s"
        parameters = (status,)

    query += " ORDER BY shipment_id"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, parameters)

            columns = [
                column.name
                for column in cur.description
            ]

            return [
                dict(zip(columns, row))
                for row in cur.fetchall()
            ]
