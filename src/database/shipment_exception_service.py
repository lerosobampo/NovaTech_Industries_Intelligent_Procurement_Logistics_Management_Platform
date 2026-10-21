
"""
NovaTech Industries
Shipment Exception Management Service

Simulation-only incident investigation and audit history.

This module never authorizes procurement and never modifies
shipment lifecycle statuses.
"""

from datetime import date, datetime

from src.database.connection import get_connection


class ShipmentExceptionError(ValueError):
    """Invalid exception-management operation."""


EXCEPTION_TYPES = {
    "DELIVERY_DELAY",
    "DAMAGED_GOODS",
    "LOST_SHIPMENT",
    "INCORRECT_DELIVERY",
    "DOCUMENTATION_ISSUE",
    "CARRIER_ISSUE",
    "OTHER",
}

SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

EXCEPTION_STATUSES = {
    "OPEN",
    "INVESTIGATING",
    "RESOLVED",
    "CLOSED",
}

STATUS_TRANSITIONS = {
    "OPEN": {"INVESTIGATING"},
    "INVESTIGATING": {"RESOLVED"},
    "RESOLVED": {"CLOSED"},
    "CLOSED": set(),
}

GOVERNANCE = {
    "simulation_mode": "SIMULATION",
    "evidence_classification": "SYNTHETIC_UNVERIFIED",
    "authorization_status": "NOT_AUTHORIZED",
}


def _required_text(value, field, max_length=None):
    if not isinstance(value, str) or not value.strip():
        raise ShipmentExceptionError(f"{field} must not be empty.")

    result = value.strip()

    if max_length is not None and len(result) > max_length:
        raise ShipmentExceptionError(
            f"{field} must contain at most {max_length} characters."
        )

    return result


def _optional_text(value, field, max_length=None):
    if value is None:
        return None

    return _required_text(value, field, max_length)


def _choice(value, field, allowed):
    result = _required_text(value, field).upper()

    if result not in allowed:
        raise ShipmentExceptionError(
            f"Invalid {field}: {result}. "
            f"Allowed values: {', '.join(sorted(allowed))}"
        )

    return result


def _timestamp(value):
    if value is None:
        return datetime.now()

    if isinstance(value, datetime):
        if value.tzinfo is not None:
            raise ShipmentExceptionError(
                "Event timestamps must be timezone-naive."
            )
        return value

    raise ShipmentExceptionError(
        "event_timestamp must be a datetime object."
    )


def _fetch_exception(cur, exception_id, lock=False):
    query = """
        SELECT
            exception_id,
            shipment_id,
            exception_type,
            severity,
            exception_status,
            description,
            reported_by,
            assigned_to,
            corrective_action,
            resolution_notes,
            reported_at,
            resolved_at,
            closed_at,
            simulation_mode,
            evidence_classification,
            authorization_status,
            created_at,
            updated_at
        FROM logistics.shipment_exceptions
        WHERE exception_id = %s
    """

    if lock:
        query += " FOR UPDATE"

    cur.execute(query, (exception_id,))
    row = cur.fetchone()

    if row is None:
        raise ShipmentExceptionError(
            f"Shipment exception {exception_id} does not exist."
        )

    columns = [column.name for column in cur.description]
    return dict(zip(columns, row))


def _validate_exception_id(exception_id):
    if isinstance(exception_id, bool) or not isinstance(
        exception_id, int
    ) or exception_id <= 0:
        raise ShipmentExceptionError(
            "exception_id must be a positive integer."
        )

    return exception_id


def _latest_event_timestamp(cur, exception_id):
    cur.execute(
        """
        SELECT MAX(event_timestamp)
        FROM logistics.shipment_exception_events
        WHERE exception_id = %s
        """,
        (exception_id,),
    )

    return cur.fetchone()[0]


def _validate_event_time(cur, exception_record, event_timestamp):
    if event_timestamp < exception_record["reported_at"]:
        raise ShipmentExceptionError(
            "An event cannot precede the exception report."
        )

    latest = _latest_event_timestamp(
        cur, exception_record["exception_id"]
    )

    if latest is not None and event_timestamp <= latest:
        raise ShipmentExceptionError(
            "An event timestamp must be later than "
            "the latest recorded exception event."
        )


def _insert_event(
    cur,
    exception_id,
    event_timestamp,
    event_type,
    description,
    recorded_by,
    previous_status=None,
    new_status=None,
):
    cur.execute(
        """
        INSERT INTO logistics.shipment_exception_events (
            exception_id,
            event_timestamp,
            event_type,
            previous_status,
            new_status,
            event_description,
            recorded_by,
            simulation_mode
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'SIMULATION')
        RETURNING event_id
        """,
        (
            exception_id,
            event_timestamp,
            event_type,
            previous_status,
            new_status,
            description,
            recorded_by,
        ),
    )

    return cur.fetchone()[0]


def create_exception(
    shipment_id,
    exception_type,
    severity,
    description,
    reported_by,
    assigned_to=None,
    event_timestamp=None,
):
    """Create an OPEN exception with its initial audit event."""

    shipment_id = _required_text(
        shipment_id, "shipment_id", 30
    )
    exception_type = _choice(
        exception_type, "exception_type", EXCEPTION_TYPES
    )
    severity = _choice(severity, "severity", SEVERITIES)
    description = _required_text(description, "description")
    reported_by = _required_text(
        reported_by, "reported_by", 100
    )
    assigned_to = _optional_text(
        assigned_to, "assigned_to", 100
    )
    timestamp = _timestamp(event_timestamp)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT shipment_id
                FROM logistics.shipments
                WHERE shipment_id = %s
                """,
                (shipment_id,),
            )

            if cur.fetchone() is None:
                raise ShipmentExceptionError(
                    f"Shipment {shipment_id} does not exist."
                )

            cur.execute(
                """
                INSERT INTO logistics.shipment_exceptions (
                    shipment_id,
                    exception_type,
                    severity,
                    exception_status,
                    description,
                    reported_by,
                    assigned_to,
                    reported_at,
                    simulation_mode,
                    evidence_classification,
                    authorization_status
                )
                VALUES (
                    %s, %s, %s, 'OPEN', %s, %s, %s, %s,
                    'SIMULATION',
                    'SYNTHETIC_UNVERIFIED',
                    'NOT_AUTHORIZED'
                )
                RETURNING exception_id
                """,
                (
                    shipment_id,
                    exception_type,
                    severity,
                    description,
                    reported_by,
                    assigned_to,
                    timestamp,
                ),
            )

            exception_id = cur.fetchone()[0]

            _insert_event(
                cur=cur,
                exception_id=exception_id,
                event_timestamp=timestamp,
                event_type="REPORTED",
                description=description,
                recorded_by=reported_by,
                previous_status=None,
                new_status="OPEN",
            )

    return exception_id


def assign_exception(
    exception_id,
    assigned_to,
    recorded_by,
    event_timestamp=None,
):
    """Assign or reassign an OPEN/INVESTIGATING exception."""

    exception_id = _validate_exception_id(exception_id)
    assigned_to = _required_text(
        assigned_to, "assigned_to", 100
    )
    recorded_by = _required_text(
        recorded_by, "recorded_by", 100
    )
    timestamp = _timestamp(event_timestamp)

    with get_connection() as conn:
        with conn.cursor() as cur:
            record = _fetch_exception(
                cur, exception_id, lock=True
            )

            if record["exception_status"] not in {
                "OPEN", "INVESTIGATING"
            }:
                raise ShipmentExceptionError(
                    "Only OPEN or INVESTIGATING exceptions "
                    "can be assigned."
                )

            _validate_event_time(cur, record, timestamp)

            cur.execute(
                """
                UPDATE logistics.shipment_exceptions
                SET assigned_to = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE exception_id = %s
                """,
                (assigned_to, exception_id),
            )

            _insert_event(
                cur,
                exception_id,
                timestamp,
                "ASSIGNED",
                f"Exception assigned to {assigned_to}.",
                recorded_by,
                record["exception_status"],
                record["exception_status"],
            )

    return exception_id


def start_investigation(
    exception_id,
    recorded_by,
    description,
    event_timestamp=None,
):
    """Transition an exception from OPEN to INVESTIGATING."""

    return _transition_exception(
        exception_id=exception_id,
        new_status="INVESTIGATING",
        event_type="INVESTIGATION_STARTED",
        recorded_by=recorded_by,
        description=description,
        event_timestamp=event_timestamp,
    )


def record_corrective_action(
    exception_id,
    corrective_action,
    recorded_by,
    event_timestamp=None,
):
    """Record a corrective action during an investigation."""

    exception_id = _validate_exception_id(exception_id)
    corrective_action = _required_text(
        corrective_action, "corrective_action"
    )
    recorded_by = _required_text(
        recorded_by, "recorded_by", 100
    )
    timestamp = _timestamp(event_timestamp)

    with get_connection() as conn:
        with conn.cursor() as cur:
            record = _fetch_exception(
                cur, exception_id, lock=True
            )

            if record["exception_status"] != "INVESTIGATING":
                raise ShipmentExceptionError(
                    "Corrective actions require an "
                    "INVESTIGATING exception."
                )

            _validate_event_time(cur, record, timestamp)

            cur.execute(
                """
                UPDATE logistics.shipment_exceptions
                SET corrective_action = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE exception_id = %s
                """,
                (corrective_action, exception_id),
            )

            _insert_event(
                cur,
                exception_id,
                timestamp,
                "CORRECTIVE_ACTION",
                corrective_action,
                recorded_by,
                "INVESTIGATING",
                "INVESTIGATING",
            )

    return exception_id


def resolve_exception(
    exception_id,
    resolution_notes,
    recorded_by,
    event_timestamp=None,
):
    """Resolve an investigation with mandatory resolution notes."""

    resolution_notes = _required_text(
        resolution_notes, "resolution_notes"
    )

    return _transition_exception(
        exception_id=exception_id,
        new_status="RESOLVED",
        event_type="RESOLVED",
        recorded_by=recorded_by,
        description=resolution_notes,
        event_timestamp=event_timestamp,
        resolution_notes=resolution_notes,
    )


def close_exception(
    exception_id,
    recorded_by,
    description,
    event_timestamp=None,
):
    """Close a previously resolved exception."""

    return _transition_exception(
        exception_id=exception_id,
        new_status="CLOSED",
        event_type="CLOSED",
        recorded_by=recorded_by,
        description=description,
        event_timestamp=event_timestamp,
    )


def _transition_exception(
    exception_id,
    new_status,
    event_type,
    recorded_by,
    description,
    event_timestamp=None,
    resolution_notes=None,
):
    exception_id = _validate_exception_id(exception_id)
    recorded_by = _required_text(
        recorded_by, "recorded_by", 100
    )
    description = _required_text(
        description, "description"
    )
    timestamp = _timestamp(event_timestamp)

    with get_connection() as conn:
        with conn.cursor() as cur:
            record = _fetch_exception(
                cur, exception_id, lock=True
            )

            previous_status = record["exception_status"]

            if new_status not in STATUS_TRANSITIONS.get(
                previous_status, set()
            ):
                raise ShipmentExceptionError(
                    f"Invalid exception transition: "
                    f"{previous_status} -> {new_status}"
                )

            _validate_event_time(cur, record, timestamp)

            if new_status == "INVESTIGATING":
                cur.execute(
                    """
                    UPDATE logistics.shipment_exceptions
                    SET exception_status = 'INVESTIGATING',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE exception_id = %s
                    """,
                    (exception_id,),
                )

            elif new_status == "RESOLVED":
                cur.execute(
                    """
                    UPDATE logistics.shipment_exceptions
                    SET exception_status = 'RESOLVED',
                        resolution_notes = %s,
                        resolved_at = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE exception_id = %s
                    """,
                    (
                        resolution_notes,
                        timestamp,
                        exception_id,
                    ),
                )

            elif new_status == "CLOSED":
                cur.execute(
                    """
                    UPDATE logistics.shipment_exceptions
                    SET exception_status = 'CLOSED',
                        closed_at = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE exception_id = %s
                    """,
                    (timestamp, exception_id),
                )

            _insert_event(
                cur,
                exception_id,
                timestamp,
                event_type,
                description,
                recorded_by,
                previous_status,
                new_status,
            )

    return exception_id


def add_exception_note(
    exception_id,
    note,
    recorded_by,
    event_timestamp=None,
):
    """Append an investigation note without changing its status."""

    exception_id = _validate_exception_id(exception_id)
    note = _required_text(note, "note")
    recorded_by = _required_text(
        recorded_by, "recorded_by", 100
    )
    timestamp = _timestamp(event_timestamp)

    with get_connection() as conn:
        with conn.cursor() as cur:
            record = _fetch_exception(
                cur, exception_id, lock=True
            )

            if record["exception_status"] == "CLOSED":
                raise ShipmentExceptionError(
                    "Closed exceptions cannot be modified."
                )

            _validate_event_time(cur, record, timestamp)

            _insert_event(
                cur,
                exception_id,
                timestamp,
                "NOTE_ADDED",
                note,
                recorded_by,
                record["exception_status"],
                record["exception_status"],
            )

    return exception_id


def get_exception(exception_id):
    """Retrieve one exception without modifying the database."""

    exception_id = _validate_exception_id(exception_id)

    with get_connection() as conn:
        with conn.cursor() as cur:
            return _fetch_exception(cur, exception_id)


def get_exception_events(exception_id):
    """Retrieve the chronological audit history of an exception."""

    exception_id = _validate_exception_id(exception_id)

    with get_connection() as conn:
        with conn.cursor() as cur:
            _fetch_exception(cur, exception_id)

            cur.execute(
                """
                SELECT
                    event_id,
                    exception_id,
                    event_timestamp,
                    event_type,
                    previous_status,
                    new_status,
                    event_description,
                    recorded_by,
                    simulation_mode,
                    created_at
                FROM logistics.shipment_exception_events
                WHERE exception_id = %s
                ORDER BY event_timestamp, event_id
                """,
                (exception_id,),
            )

            columns = [
                column.name for column in cur.description
            ]

            return [
                dict(zip(columns, row))
                for row in cur.fetchall()
            ]


def list_exceptions(shipment_id=None, status=None):
    """List exceptions, optionally filtered by shipment or status."""

    conditions = []
    parameters = []

    if shipment_id is not None:
        shipment_id = _required_text(
            shipment_id, "shipment_id", 30
        )
        conditions.append("shipment_id = %s")
        parameters.append(shipment_id)

    if status is not None:
        status = _choice(
            status, "status", EXCEPTION_STATUSES
        )
        conditions.append("exception_status = %s")
        parameters.append(status)

    query = """
        SELECT
            exception_id,
            shipment_id,
            exception_type,
            severity,
            exception_status,
            description,
            reported_by,
            assigned_to,
            corrective_action,
            resolution_notes,
            reported_at,
            resolved_at,
            closed_at,
            simulation_mode,
            evidence_classification,
            authorization_status,
            created_at,
            updated_at
        FROM logistics.shipment_exceptions
    """

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY reported_at DESC, exception_id DESC"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, tuple(parameters))

            columns = [
                column.name for column in cur.description
            ]

            return [
                dict(zip(columns, row))
                for row in cur.fetchall()
            ]
