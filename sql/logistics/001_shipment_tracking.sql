
-- ============================================================
-- NovaTech Industries
-- Logistics Intelligence — Shipment Tracking Schema V1
--
-- Migration: 001_shipment_tracking.sql
--
-- Purpose:
--   Track simulated shipments and their event history.
--
-- Safeguards:
--   - No existing tables are modified
--   - All shipments are simulations
--   - No real carrier bookings
--   - No purchasing authorization
--   - Shipment events have unique identifiers
-- ============================================================

BEGIN;

-- ------------------------------------------------------------
-- 1. Shipments
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS logistics.shipments (

    shipment_id VARCHAR(30) PRIMARY KEY,

    supplier_id VARCHAR NOT NULL
        REFERENCES procurement.suppliers(supplier_id),

    delivery_id VARCHAR
        REFERENCES logistics.supplier_deliveries(delivery_id),

    tracking_number VARCHAR(100) UNIQUE,

    carrier_name VARCHAR(100) NOT NULL,

    transport_mode VARCHAR(20) NOT NULL
        CHECK (
            transport_mode IN (
                'ROAD',
                'RAIL',
                'AIR',
                'SEA'
            )
        ),

    origin_location VARCHAR(200) NOT NULL,

    destination_location VARCHAR(200) NOT NULL,

    dispatch_date DATE,

    estimated_delivery_date DATE NOT NULL,

    actual_delivery_date DATE,

    shipment_status VARCHAR(30) NOT NULL DEFAULT 'CREATED'
        CHECK (
            shipment_status IN (
                'CREATED',
                'DISPATCHED',
                'IN_TRANSIT',
                'DELIVERED',
                'EXCEPTION',
                'CANCELLED'
            )
        ),

    simulation_mode VARCHAR(20) NOT NULL DEFAULT 'SIMULATION'
        CHECK (simulation_mode = 'SIMULATION'),

    evidence_classification VARCHAR(40) NOT NULL
        DEFAULT 'SYNTHETIC_UNVERIFIED'
        CHECK (
            evidence_classification = 'SYNTHETIC_UNVERIFIED'
        ),

    authorization_status VARCHAR(30) NOT NULL
        DEFAULT 'NOT_AUTHORIZED'
        CHECK (
            authorization_status = 'NOT_AUTHORIZED'
        ),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT shipment_date_consistency CHECK (
        dispatch_date IS NULL
        OR dispatch_date <= estimated_delivery_date
    ),

    CONSTRAINT shipment_actual_delivery_consistency CHECK (
        actual_delivery_date IS NULL
        OR dispatch_date IS NULL
        OR actual_delivery_date >= dispatch_date
    ),

    CONSTRAINT delivered_requires_actual_date CHECK (
        shipment_status <> 'DELIVERED'
        OR actual_delivery_date IS NOT NULL
    ),

    CONSTRAINT actual_date_requires_delivered_status CHECK (
        actual_delivery_date IS NULL
        OR shipment_status = 'DELIVERED'
    ),

    CONSTRAINT dispatched_requires_dispatch_date CHECK (
        shipment_status NOT IN (
            'DISPATCHED',
            'IN_TRANSIT',
            'DELIVERED'
        )
        OR dispatch_date IS NOT NULL
    ),

    CONSTRAINT created_has_no_dispatch CHECK (
        shipment_status <> 'CREATED'
        OR (
            dispatch_date IS NULL
            AND actual_delivery_date IS NULL
        )
    ),

    CONSTRAINT cancelled_has_no_actual_delivery CHECK (
        shipment_status <> 'CANCELLED'
        OR actual_delivery_date IS NULL
    )
);


-- ------------------------------------------------------------
-- 2. Shipment tracking events
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS logistics.shipment_events (

    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    shipment_id VARCHAR(30) NOT NULL
        REFERENCES logistics.shipments(shipment_id),

    event_timestamp TIMESTAMP NOT NULL,

    event_type VARCHAR(30) NOT NULL
        CHECK (
            event_type IN (
                'CREATED',
                'DISPATCHED',
                'IN_TRANSIT',
                'DELIVERED',
                'EXCEPTION',
                'CANCELLED'
            )
        ),

    event_location VARCHAR(200),

    event_description TEXT NOT NULL,

    recorded_by VARCHAR(100) NOT NULL DEFAULT 'SYSTEM_SIMULATION',

    simulation_mode VARCHAR(20) NOT NULL DEFAULT 'SIMULATION'
        CHECK (simulation_mode = 'SIMULATION'),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_shipment_event
        UNIQUE (
            shipment_id,
            event_timestamp,
            event_type
        ),

    CONSTRAINT event_description_not_empty CHECK (
        length(trim(event_description)) > 0
    )
);


-- ------------------------------------------------------------
-- 3. Performance indexes
-- ------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_shipments_supplier
    ON logistics.shipments(supplier_id);

CREATE INDEX IF NOT EXISTS idx_shipments_status
    ON logistics.shipments(shipment_status);

CREATE INDEX IF NOT EXISTS idx_shipments_estimated_delivery
    ON logistics.shipments(estimated_delivery_date);

CREATE INDEX IF NOT EXISTS idx_shipment_events_shipment_time
    ON logistics.shipment_events(
        shipment_id,
        event_timestamp DESC
    );


-- ------------------------------------------------------------
-- 4. Documentation
-- ------------------------------------------------------------

COMMENT ON TABLE logistics.shipments IS
    'Synthetic operational shipment tracking. No real shipments or carrier bookings.';

COMMENT ON TABLE logistics.shipment_events IS
    'Synthetic shipment tracking event history. Events do not authorize procurement or transport.';

COMMIT;
