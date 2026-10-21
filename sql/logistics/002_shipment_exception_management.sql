
-- NovaTech Industries
-- Shipment Exception Management — Migration 002
-- Simulation-only operational investigation records
-- Preserves all existing logistics tables and records

BEGIN;

CREATE TABLE IF NOT EXISTS logistics.shipment_exceptions (
    exception_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    shipment_id VARCHAR(30) NOT NULL
        REFERENCES logistics.shipments(shipment_id),

    exception_type VARCHAR(40) NOT NULL
        CHECK (exception_type IN (
            'DELIVERY_DELAY',
            'DAMAGED_GOODS',
            'LOST_SHIPMENT',
            'INCORRECT_DELIVERY',
            'DOCUMENTATION_ISSUE',
            'CARRIER_ISSUE',
            'OTHER'
        )),

    severity VARCHAR(15) NOT NULL
        CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),

    exception_status VARCHAR(20) NOT NULL DEFAULT 'OPEN'
        CHECK (exception_status IN (
            'OPEN',
            'INVESTIGATING',
            'RESOLVED',
            'CLOSED'
        )),

    description TEXT NOT NULL
        CHECK (length(trim(description)) > 0),

    reported_by VARCHAR(100) NOT NULL
        CHECK (length(trim(reported_by)) > 0),

    assigned_to VARCHAR(100),

    corrective_action TEXT,

    resolution_notes TEXT,

    reported_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    closed_at TIMESTAMP,

    simulation_mode VARCHAR(20) NOT NULL DEFAULT 'SIMULATION'
        CHECK (simulation_mode = 'SIMULATION'),

    evidence_classification VARCHAR(40) NOT NULL
        DEFAULT 'SYNTHETIC_UNVERIFIED'
        CHECK (evidence_classification = 'SYNTHETIC_UNVERIFIED'),

    authorization_status VARCHAR(30) NOT NULL
        DEFAULT 'NOT_AUTHORIZED'
        CHECK (authorization_status = 'NOT_AUTHORIZED'),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT exception_resolution_consistency CHECK (
        (exception_status IN ('OPEN', 'INVESTIGATING')
            AND resolved_at IS NULL
            AND closed_at IS NULL)
        OR
        (exception_status = 'RESOLVED'
            AND resolved_at IS NOT NULL
            AND closed_at IS NULL)
        OR
        (exception_status = 'CLOSED'
            AND resolved_at IS NOT NULL
            AND closed_at IS NOT NULL)
    ),

    CONSTRAINT exception_timestamp_order CHECK (
        (resolved_at IS NULL OR resolved_at >= reported_at)
        AND
        (closed_at IS NULL OR closed_at >= resolved_at)
    )
);

CREATE TABLE IF NOT EXISTS logistics.shipment_exception_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    exception_id BIGINT NOT NULL
        REFERENCES logistics.shipment_exceptions(exception_id),

    event_timestamp TIMESTAMP NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    event_type VARCHAR(30) NOT NULL
        CHECK (event_type IN (
            'REPORTED',
            'ASSIGNED',
            'INVESTIGATION_STARTED',
            'CORRECTIVE_ACTION',
            'RESOLVED',
            'CLOSED',
            'NOTE_ADDED'
        )),

    previous_status VARCHAR(20),
    new_status VARCHAR(20),

    event_description TEXT NOT NULL
        CHECK (length(trim(event_description)) > 0),

    recorded_by VARCHAR(100) NOT NULL
        CHECK (length(trim(recorded_by)) > 0),

    simulation_mode VARCHAR(20) NOT NULL DEFAULT 'SIMULATION'
        CHECK (simulation_mode = 'SIMULATION'),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_exception_event
        UNIQUE (exception_id, event_timestamp, event_type)
);

CREATE INDEX IF NOT EXISTS idx_shipment_exceptions_shipment
    ON logistics.shipment_exceptions(shipment_id);

CREATE INDEX IF NOT EXISTS idx_shipment_exceptions_status
    ON logistics.shipment_exceptions(exception_status);

CREATE INDEX IF NOT EXISTS idx_shipment_exceptions_severity
    ON logistics.shipment_exceptions(severity);

CREATE INDEX IF NOT EXISTS idx_shipment_exception_events_history
    ON logistics.shipment_exception_events(
        exception_id,
        event_timestamp
    );

COMMIT;
