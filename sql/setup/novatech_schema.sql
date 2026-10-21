--
-- PostgreSQL database dump
--

\restrict Q2SbNFUWrUMVVkmacGqngQjiolr0Djen8bSsrMSlmS54xoee4HXTf1PhbKZA4re

-- Dumped from database version 17.11 (Homebrew)
-- Dumped by pg_dump version 17.11 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: analytics; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA analytics;


--
-- Name: logistics; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA logistics;


--
-- Name: procurement; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA procurement;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: shipment_events; Type: TABLE; Schema: logistics; Owner: -
--

CREATE TABLE logistics.shipment_events (
    event_id bigint NOT NULL,
    shipment_id character varying(30) NOT NULL,
    event_timestamp timestamp without time zone NOT NULL,
    event_type character varying(30) NOT NULL,
    event_location character varying(200),
    event_description text NOT NULL,
    recorded_by character varying(100) DEFAULT 'SYSTEM_SIMULATION'::character varying NOT NULL,
    simulation_mode character varying(20) DEFAULT 'SIMULATION'::character varying NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT event_description_not_empty CHECK ((length(TRIM(BOTH FROM event_description)) > 0)),
    CONSTRAINT shipment_events_event_type_check CHECK (((event_type)::text = ANY ((ARRAY['CREATED'::character varying, 'DISPATCHED'::character varying, 'IN_TRANSIT'::character varying, 'DELIVERED'::character varying, 'EXCEPTION'::character varying, 'CANCELLED'::character varying])::text[]))),
    CONSTRAINT shipment_events_simulation_mode_check CHECK (((simulation_mode)::text = 'SIMULATION'::text))
);


--
-- Name: TABLE shipment_events; Type: COMMENT; Schema: logistics; Owner: -
--

COMMENT ON TABLE logistics.shipment_events IS 'Synthetic shipment tracking event history. Events do not authorize procurement or transport.';


--
-- Name: shipment_events_event_id_seq; Type: SEQUENCE; Schema: logistics; Owner: -
--

ALTER TABLE logistics.shipment_events ALTER COLUMN event_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME logistics.shipment_events_event_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: shipment_exception_events; Type: TABLE; Schema: logistics; Owner: -
--

CREATE TABLE logistics.shipment_exception_events (
    event_id bigint NOT NULL,
    exception_id bigint NOT NULL,
    event_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    event_type character varying(30) NOT NULL,
    previous_status character varying(20),
    new_status character varying(20),
    event_description text NOT NULL,
    recorded_by character varying(100) NOT NULL,
    simulation_mode character varying(20) DEFAULT 'SIMULATION'::character varying NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT shipment_exception_events_event_description_check CHECK ((length(TRIM(BOTH FROM event_description)) > 0)),
    CONSTRAINT shipment_exception_events_event_type_check CHECK (((event_type)::text = ANY ((ARRAY['REPORTED'::character varying, 'ASSIGNED'::character varying, 'INVESTIGATION_STARTED'::character varying, 'CORRECTIVE_ACTION'::character varying, 'RESOLVED'::character varying, 'CLOSED'::character varying, 'NOTE_ADDED'::character varying])::text[]))),
    CONSTRAINT shipment_exception_events_recorded_by_check CHECK ((length(TRIM(BOTH FROM recorded_by)) > 0)),
    CONSTRAINT shipment_exception_events_simulation_mode_check CHECK (((simulation_mode)::text = 'SIMULATION'::text))
);


--
-- Name: shipment_exception_events_event_id_seq; Type: SEQUENCE; Schema: logistics; Owner: -
--

ALTER TABLE logistics.shipment_exception_events ALTER COLUMN event_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME logistics.shipment_exception_events_event_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: shipment_exceptions; Type: TABLE; Schema: logistics; Owner: -
--

CREATE TABLE logistics.shipment_exceptions (
    exception_id bigint NOT NULL,
    shipment_id character varying(30) NOT NULL,
    exception_type character varying(40) NOT NULL,
    severity character varying(15) NOT NULL,
    exception_status character varying(20) DEFAULT 'OPEN'::character varying NOT NULL,
    description text NOT NULL,
    reported_by character varying(100) NOT NULL,
    assigned_to character varying(100),
    corrective_action text,
    resolution_notes text,
    reported_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    resolved_at timestamp without time zone,
    closed_at timestamp without time zone,
    simulation_mode character varying(20) DEFAULT 'SIMULATION'::character varying NOT NULL,
    evidence_classification character varying(40) DEFAULT 'SYNTHETIC_UNVERIFIED'::character varying NOT NULL,
    authorization_status character varying(30) DEFAULT 'NOT_AUTHORIZED'::character varying NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT exception_resolution_consistency CHECK (((((exception_status)::text = ANY ((ARRAY['OPEN'::character varying, 'INVESTIGATING'::character varying])::text[])) AND (resolved_at IS NULL) AND (closed_at IS NULL)) OR (((exception_status)::text = 'RESOLVED'::text) AND (resolved_at IS NOT NULL) AND (closed_at IS NULL)) OR (((exception_status)::text = 'CLOSED'::text) AND (resolved_at IS NOT NULL) AND (closed_at IS NOT NULL)))),
    CONSTRAINT exception_timestamp_order CHECK ((((resolved_at IS NULL) OR (resolved_at >= reported_at)) AND ((closed_at IS NULL) OR (closed_at >= resolved_at)))),
    CONSTRAINT shipment_exceptions_authorization_status_check CHECK (((authorization_status)::text = 'NOT_AUTHORIZED'::text)),
    CONSTRAINT shipment_exceptions_description_check CHECK ((length(TRIM(BOTH FROM description)) > 0)),
    CONSTRAINT shipment_exceptions_evidence_classification_check CHECK (((evidence_classification)::text = 'SYNTHETIC_UNVERIFIED'::text)),
    CONSTRAINT shipment_exceptions_exception_status_check CHECK (((exception_status)::text = ANY ((ARRAY['OPEN'::character varying, 'INVESTIGATING'::character varying, 'RESOLVED'::character varying, 'CLOSED'::character varying])::text[]))),
    CONSTRAINT shipment_exceptions_exception_type_check CHECK (((exception_type)::text = ANY ((ARRAY['DELIVERY_DELAY'::character varying, 'DAMAGED_GOODS'::character varying, 'LOST_SHIPMENT'::character varying, 'INCORRECT_DELIVERY'::character varying, 'DOCUMENTATION_ISSUE'::character varying, 'CARRIER_ISSUE'::character varying, 'OTHER'::character varying])::text[]))),
    CONSTRAINT shipment_exceptions_reported_by_check CHECK ((length(TRIM(BOTH FROM reported_by)) > 0)),
    CONSTRAINT shipment_exceptions_severity_check CHECK (((severity)::text = ANY ((ARRAY['LOW'::character varying, 'MEDIUM'::character varying, 'HIGH'::character varying, 'CRITICAL'::character varying])::text[]))),
    CONSTRAINT shipment_exceptions_simulation_mode_check CHECK (((simulation_mode)::text = 'SIMULATION'::text))
);


--
-- Name: shipment_exceptions_exception_id_seq; Type: SEQUENCE; Schema: logistics; Owner: -
--

ALTER TABLE logistics.shipment_exceptions ALTER COLUMN exception_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME logistics.shipment_exceptions_exception_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: shipments; Type: TABLE; Schema: logistics; Owner: -
--

CREATE TABLE logistics.shipments (
    shipment_id character varying(30) NOT NULL,
    supplier_id character varying NOT NULL,
    delivery_id character varying,
    tracking_number character varying(100),
    carrier_name character varying(100) NOT NULL,
    transport_mode character varying(20) NOT NULL,
    origin_location character varying(200) NOT NULL,
    destination_location character varying(200) NOT NULL,
    dispatch_date date,
    estimated_delivery_date date NOT NULL,
    actual_delivery_date date,
    shipment_status character varying(30) DEFAULT 'CREATED'::character varying NOT NULL,
    simulation_mode character varying(20) DEFAULT 'SIMULATION'::character varying NOT NULL,
    evidence_classification character varying(40) DEFAULT 'SYNTHETIC_UNVERIFIED'::character varying NOT NULL,
    authorization_status character varying(30) DEFAULT 'NOT_AUTHORIZED'::character varying NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT actual_date_requires_delivered_status CHECK (((actual_delivery_date IS NULL) OR ((shipment_status)::text = 'DELIVERED'::text))),
    CONSTRAINT cancelled_has_no_actual_delivery CHECK ((((shipment_status)::text <> 'CANCELLED'::text) OR (actual_delivery_date IS NULL))),
    CONSTRAINT created_has_no_dispatch CHECK ((((shipment_status)::text <> 'CREATED'::text) OR ((dispatch_date IS NULL) AND (actual_delivery_date IS NULL)))),
    CONSTRAINT delivered_requires_actual_date CHECK ((((shipment_status)::text <> 'DELIVERED'::text) OR (actual_delivery_date IS NOT NULL))),
    CONSTRAINT dispatched_requires_dispatch_date CHECK ((((shipment_status)::text <> ALL ((ARRAY['DISPATCHED'::character varying, 'IN_TRANSIT'::character varying, 'DELIVERED'::character varying])::text[])) OR (dispatch_date IS NOT NULL))),
    CONSTRAINT shipment_actual_delivery_consistency CHECK (((actual_delivery_date IS NULL) OR (dispatch_date IS NULL) OR (actual_delivery_date >= dispatch_date))),
    CONSTRAINT shipment_date_consistency CHECK (((dispatch_date IS NULL) OR (dispatch_date <= estimated_delivery_date))),
    CONSTRAINT shipments_authorization_status_check CHECK (((authorization_status)::text = 'NOT_AUTHORIZED'::text)),
    CONSTRAINT shipments_evidence_classification_check CHECK (((evidence_classification)::text = 'SYNTHETIC_UNVERIFIED'::text)),
    CONSTRAINT shipments_shipment_status_check CHECK (((shipment_status)::text = ANY ((ARRAY['CREATED'::character varying, 'DISPATCHED'::character varying, 'IN_TRANSIT'::character varying, 'DELIVERED'::character varying, 'EXCEPTION'::character varying, 'CANCELLED'::character varying])::text[]))),
    CONSTRAINT shipments_simulation_mode_check CHECK (((simulation_mode)::text = 'SIMULATION'::text)),
    CONSTRAINT shipments_transport_mode_check CHECK (((transport_mode)::text = ANY ((ARRAY['ROAD'::character varying, 'RAIL'::character varying, 'AIR'::character varying, 'SEA'::character varying])::text[])))
);


--
-- Name: TABLE shipments; Type: COMMENT; Schema: logistics; Owner: -
--

COMMENT ON TABLE logistics.shipments IS 'Synthetic operational shipment tracking. No real shipments or carrier bookings.';


--
-- Name: supplier_deliveries; Type: TABLE; Schema: logistics; Owner: -
--

CREATE TABLE logistics.supplier_deliveries (
    delivery_id character varying(20) NOT NULL,
    supplier_id character varying(20) NOT NULL,
    planned_delivery_date date NOT NULL,
    actual_delivery_date date,
    on_time boolean,
    status character varying(30) NOT NULL
);


--
-- Name: supplier_inventory_history; Type: TABLE; Schema: logistics; Owner: -
--

CREATE TABLE logistics.supplier_inventory_history (
    supplier_id character varying(20) NOT NULL,
    product_id character varying(20) NOT NULL,
    available_quantity integer NOT NULL,
    minimum_order_quantity integer NOT NULL,
    effective_from date NOT NULL,
    effective_to date,
    recorded_at timestamp without time zone NOT NULL,
    evidence_source character varying(100) NOT NULL,
    CONSTRAINT supplier_inventory_history_available_quantity_check CHECK ((available_quantity >= 0)),
    CONSTRAINT supplier_inventory_history_check CHECK (((effective_to IS NULL) OR (effective_to >= effective_from))),
    CONSTRAINT supplier_inventory_history_minimum_order_quantity_check CHECK ((minimum_order_quantity >= 0))
);


--
-- Name: supplier_quality_inspections; Type: TABLE; Schema: logistics; Owner: -
--

CREATE TABLE logistics.supplier_quality_inspections (
    inspection_id character varying(20) NOT NULL,
    supplier_id character varying(20) NOT NULL,
    inspection_date date NOT NULL,
    inspected_units integer NOT NULL,
    accepted_units integer NOT NULL,
    rejected_units integer NOT NULL,
    CONSTRAINT supplier_quality_inspections_accepted_units_check CHECK ((accepted_units >= 0)),
    CONSTRAINT supplier_quality_inspections_check CHECK (((accepted_units + rejected_units) = inspected_units)),
    CONSTRAINT supplier_quality_inspections_inspected_units_check CHECK ((inspected_units > 0)),
    CONSTRAINT supplier_quality_inspections_rejected_units_check CHECK ((rejected_units >= 0))
);


--
-- Name: analyst_assessments; Type: TABLE; Schema: procurement; Owner: -
--

CREATE TABLE procurement.analyst_assessments (
    assessment_id bigint NOT NULL,
    requisition_id character varying NOT NULL,
    quotation_id character varying NOT NULL,
    analyst_name character varying NOT NULL,
    assessment_status character varying NOT NULL,
    assessment_notes text NOT NULL,
    decision_mode character varying DEFAULT 'SIMULATION'::character varying NOT NULL,
    authorization_status character varying DEFAULT 'NOT_AUTHORIZED'::character varying NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT analyst_assessments_assessment_status_check CHECK (((assessment_status)::text = ANY ((ARRAY['REVIEW_REQUIRED'::character varying, 'NOT_RECOMMENDED'::character varying])::text[]))),
    CONSTRAINT analyst_assessments_authorization_status_check CHECK (((authorization_status)::text = 'NOT_AUTHORIZED'::text)),
    CONSTRAINT analyst_assessments_decision_mode_check CHECK (((decision_mode)::text = 'SIMULATION'::text))
);


--
-- Name: analyst_assessments_assessment_id_seq; Type: SEQUENCE; Schema: procurement; Owner: -
--

ALTER TABLE procurement.analyst_assessments ALTER COLUMN assessment_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME procurement.analyst_assessments_assessment_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: procurement_approvals; Type: TABLE; Schema: procurement; Owner: -
--

CREATE TABLE procurement.procurement_approvals (
    approval_id character varying(30) NOT NULL,
    decision_id character varying(30) NOT NULL,
    requisition_id character varying(20) NOT NULL,
    approval_requested_at timestamp without time zone NOT NULL,
    approval_stage character varying(50) NOT NULL,
    approver_role character varying(100) NOT NULL,
    approval_status character varying(30) NOT NULL,
    approval_decided_at timestamp without time zone,
    approved_by character varying(100),
    approval_notes text,
    decision_mode character varying(30) NOT NULL,
    authorization_effect character varying(50) NOT NULL
);


--
-- Name: procurement_decision_audit; Type: TABLE; Schema: procurement; Owner: -
--

CREATE TABLE procurement.procurement_decision_audit (
    audit_id character varying(30) NOT NULL,
    decision_id character varying(30) NOT NULL,
    requisition_id character varying(20) NOT NULL,
    event_date timestamp without time zone NOT NULL,
    event_type character varying(50) NOT NULL,
    actor character varying(100) NOT NULL,
    previous_status character varying(30),
    new_status character varying(30) NOT NULL,
    evidence_reference character varying(255),
    event_details text,
    decision_mode character varying(30) NOT NULL,
    evidence_classification character varying(100) NOT NULL
);


--
-- Name: procurement_decisions; Type: TABLE; Schema: procurement; Owner: -
--

CREATE TABLE procurement.procurement_decisions (
    decision_id character varying(30) NOT NULL,
    requisition_id character varying(20) NOT NULL,
    decision_date date NOT NULL,
    decision_mode character varying(30) NOT NULL,
    decision_status character varying(30) NOT NULL,
    selected_quotation_id character varying(20),
    decision_maker character varying(100),
    decision_reason text,
    quotation_count integer NOT NULL,
    quotations_valid_on_decision_date integer NOT NULL,
    eligible_count integer NOT NULL,
    review_required_count integer NOT NULL,
    blocked_count integer NOT NULL,
    evaluation_source character varying(255),
    approval_status character varying(30) NOT NULL,
    CONSTRAINT procurement_decisions_blocked_count_check CHECK ((blocked_count >= 0)),
    CONSTRAINT procurement_decisions_eligible_count_check CHECK ((eligible_count >= 0)),
    CONSTRAINT procurement_decisions_quotation_count_check CHECK ((quotation_count >= 0)),
    CONSTRAINT procurement_decisions_quotations_valid_on_decision_date_check CHECK ((quotations_valid_on_decision_date >= 0)),
    CONSTRAINT procurement_decisions_review_required_count_check CHECK ((review_required_count >= 0))
);


--
-- Name: products; Type: TABLE; Schema: procurement; Owner: -
--

CREATE TABLE procurement.products (
    product_id character varying(20) NOT NULL,
    sku character varying(50) NOT NULL,
    product_name character varying(150) NOT NULL,
    category character varying(100) NOT NULL,
    unit_of_measure character varying(30) NOT NULL
);


--
-- Name: purchase_requisitions; Type: TABLE; Schema: procurement; Owner: -
--

CREATE TABLE procurement.purchase_requisitions (
    requisition_id character varying(20) NOT NULL,
    product_id character varying(20) NOT NULL,
    requested_quantity integer NOT NULL,
    request_date date NOT NULL,
    required_delivery_date date NOT NULL,
    status character varying(30) NOT NULL,
    CONSTRAINT purchase_requisitions_check CHECK ((required_delivery_date >= request_date)),
    CONSTRAINT purchase_requisitions_requested_quantity_check CHECK ((requested_quantity > 0))
);


--
-- Name: quotation_items; Type: TABLE; Schema: procurement; Owner: -
--

CREATE TABLE procurement.quotation_items (
    quotation_id character varying(20) NOT NULL,
    product_id character varying(20) NOT NULL,
    quoted_quantity integer NOT NULL,
    unit_price_eur numeric(12,2) NOT NULL,
    freight_eur numeric(12,2) NOT NULL,
    duties_eur numeric(12,2) NOT NULL,
    other_fees_eur numeric(12,2) NOT NULL,
    lead_time_days integer NOT NULL,
    CONSTRAINT quotation_items_duties_eur_check CHECK ((duties_eur >= (0)::numeric)),
    CONSTRAINT quotation_items_freight_eur_check CHECK ((freight_eur >= (0)::numeric)),
    CONSTRAINT quotation_items_lead_time_days_check CHECK ((lead_time_days >= 0)),
    CONSTRAINT quotation_items_other_fees_eur_check CHECK ((other_fees_eur >= (0)::numeric)),
    CONSTRAINT quotation_items_quoted_quantity_check CHECK ((quoted_quantity > 0)),
    CONSTRAINT quotation_items_unit_price_eur_check CHECK ((unit_price_eur >= (0)::numeric))
);


--
-- Name: quotations; Type: TABLE; Schema: procurement; Owner: -
--

CREATE TABLE procurement.quotations (
    quotation_id character varying(20) NOT NULL,
    requisition_id character varying(20) NOT NULL,
    supplier_id character varying(20) NOT NULL,
    quotation_date date NOT NULL,
    valid_until date NOT NULL,
    currency character varying(10) NOT NULL,
    status character varying(30) NOT NULL,
    CONSTRAINT quotations_check CHECK ((valid_until >= quotation_date))
);


--
-- Name: supplier_compliance; Type: TABLE; Schema: procurement; Owner: -
--

CREATE TABLE procurement.supplier_compliance (
    supplier_id character varying(20) NOT NULL,
    category character varying(100) NOT NULL,
    approval_status character varying(30) NOT NULL,
    valid_until date
);


--
-- Name: supplier_compliance_history; Type: TABLE; Schema: procurement; Owner: -
--

CREATE TABLE procurement.supplier_compliance_history (
    supplier_id character varying(20) NOT NULL,
    category character varying(100) NOT NULL,
    approval_status character varying(30) NOT NULL,
    effective_from date NOT NULL,
    effective_to date,
    valid_until date,
    recorded_at timestamp without time zone NOT NULL,
    evidence_source character varying(100) NOT NULL,
    CONSTRAINT supplier_compliance_history_check CHECK (((effective_to IS NULL) OR (effective_to >= effective_from)))
);


--
-- Name: supplier_products; Type: TABLE; Schema: procurement; Owner: -
--

CREATE TABLE procurement.supplier_products (
    supplier_id character varying(20) NOT NULL,
    product_id character varying(20) NOT NULL,
    minimum_order_quantity integer NOT NULL,
    available_quantity integer NOT NULL,
    CONSTRAINT supplier_products_available_quantity_check CHECK ((available_quantity >= 0)),
    CONSTRAINT supplier_products_minimum_order_quantity_check CHECK ((minimum_order_quantity >= 0))
);


--
-- Name: supplier_status_history; Type: TABLE; Schema: procurement; Owner: -
--

CREATE TABLE procurement.supplier_status_history (
    supplier_id character varying(20) NOT NULL,
    status character varying(30) NOT NULL,
    effective_from date NOT NULL,
    effective_to date,
    recorded_at timestamp without time zone NOT NULL,
    evidence_source character varying(100) NOT NULL,
    CONSTRAINT supplier_status_history_check CHECK (((effective_to IS NULL) OR (effective_to >= effective_from)))
);


--
-- Name: suppliers; Type: TABLE; Schema: procurement; Owner: -
--

CREATE TABLE procurement.suppliers (
    supplier_id character varying(20) NOT NULL,
    supplier_name character varying(150) NOT NULL,
    country character varying(100),
    status character varying(30) NOT NULL
);


--
-- Name: shipment_events shipment_events_pkey; Type: CONSTRAINT; Schema: logistics; Owner: -
--

ALTER TABLE ONLY logistics.shipment_events
    ADD CONSTRAINT shipment_events_pkey PRIMARY KEY (event_id);


--
-- Name: shipment_exception_events shipment_exception_events_pkey; Type: CONSTRAINT; Schema: logistics; Owner: -
--

ALTER TABLE ONLY logistics.shipment_exception_events
    ADD CONSTRAINT shipment_exception_events_pkey PRIMARY KEY (event_id);


--
-- Name: shipment_exceptions shipment_exceptions_pkey; Type: CONSTRAINT; Schema: logistics; Owner: -
--

ALTER TABLE ONLY logistics.shipment_exceptions
    ADD CONSTRAINT shipment_exceptions_pkey PRIMARY KEY (exception_id);


--
-- Name: shipments shipments_pkey; Type: CONSTRAINT; Schema: logistics; Owner: -
--

ALTER TABLE ONLY logistics.shipments
    ADD CONSTRAINT shipments_pkey PRIMARY KEY (shipment_id);


--
-- Name: shipments shipments_tracking_number_key; Type: CONSTRAINT; Schema: logistics; Owner: -
--

ALTER TABLE ONLY logistics.shipments
    ADD CONSTRAINT shipments_tracking_number_key UNIQUE (tracking_number);


--
-- Name: supplier_deliveries supplier_deliveries_pkey; Type: CONSTRAINT; Schema: logistics; Owner: -
--

ALTER TABLE ONLY logistics.supplier_deliveries
    ADD CONSTRAINT supplier_deliveries_pkey PRIMARY KEY (delivery_id);


--
-- Name: supplier_inventory_history supplier_inventory_history_pkey; Type: CONSTRAINT; Schema: logistics; Owner: -
--

ALTER TABLE ONLY logistics.supplier_inventory_history
    ADD CONSTRAINT supplier_inventory_history_pkey PRIMARY KEY (supplier_id, product_id, effective_from);


--
-- Name: supplier_quality_inspections supplier_quality_inspections_pkey; Type: CONSTRAINT; Schema: logistics; Owner: -
--

ALTER TABLE ONLY logistics.supplier_quality_inspections
    ADD CONSTRAINT supplier_quality_inspections_pkey PRIMARY KEY (inspection_id);


--
-- Name: shipment_exception_events unique_exception_event; Type: CONSTRAINT; Schema: logistics; Owner: -
--

ALTER TABLE ONLY logistics.shipment_exception_events
    ADD CONSTRAINT unique_exception_event UNIQUE (exception_id, event_timestamp, event_type);


--
-- Name: shipment_events unique_shipment_event; Type: CONSTRAINT; Schema: logistics; Owner: -
--

ALTER TABLE ONLY logistics.shipment_events
    ADD CONSTRAINT unique_shipment_event UNIQUE (shipment_id, event_timestamp, event_type);


--
-- Name: analyst_assessments analyst_assessments_pkey; Type: CONSTRAINT; Schema: procurement; Owner: -
--

ALTER TABLE ONLY procurement.analyst_assessments
    ADD CONSTRAINT analyst_assessments_pkey PRIMARY KEY (assessment_id);


--
-- Name: procurement_approvals procurement_approvals_pkey; Type: CONSTRAINT; Schema: procurement; Owner: -
--

ALTER TABLE ONLY procurement.procurement_approvals
    ADD CONSTRAINT procurement_approvals_pkey PRIMARY KEY (approval_id);


--
-- Name: procurement_decision_audit procurement_decision_audit_pkey; Type: CONSTRAINT; Schema: procurement; Owner: -
--

ALTER TABLE ONLY procurement.procurement_decision_audit
    ADD CONSTRAINT procurement_decision_audit_pkey PRIMARY KEY (audit_id);


--
-- Name: procurement_decisions procurement_decisions_pkey; Type: CONSTRAINT; Schema: procurement; Owner: -
--

ALTER TABLE ONLY procurement.procurement_decisions
    ADD CONSTRAINT procurement_decisions_pkey PRIMARY KEY (decision_id);


--
-- Name: products products_pkey; Type: CONSTRAINT; Schema: procurement; Owner: -
--

ALTER TABLE ONLY procurement.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (product_id);


--
-- Name: purchase_requisitions purchase_requisitions_pkey; Type: CONSTRAINT; Schema: procurement; Owner: -
--

ALTER TABLE ONLY procurement.purchase_requisitions
    ADD CONSTRAINT purchase_requisitions_pkey PRIMARY KEY (requisition_id);


--
-- Name: quotation_items quotation_items_pkey; Type: CONSTRAINT; Schema: procurement; Owner: -
--

ALTER TABLE ONLY procurement.quotation_items
    ADD CONSTRAINT quotation_items_pkey PRIMARY KEY (quotation_id, product_id);


--
-- Name: quotations quotations_pkey; Type: CONSTRAINT; Schema: procurement; Owner: -
--

ALTER TABLE ONLY procurement.quotations
    ADD CONSTRAINT quotations_pkey PRIMARY KEY (quotation_id);


--
-- Name: supplier_compliance_history supplier_compliance_history_pkey; Type: CONSTRAINT; Schema: procurement; Owner: -
--

ALTER TABLE ONLY procurement.supplier_compliance_history
    ADD CONSTRAINT supplier_compliance_history_pkey PRIMARY KEY (supplier_id, category, effective_from);


--
-- Name: supplier_compliance supplier_compliance_pkey; Type: CONSTRAINT; Schema: procurement; Owner: -
--

ALTER TABLE ONLY procurement.supplier_compliance
    ADD CONSTRAINT supplier_compliance_pkey PRIMARY KEY (supplier_id, category);


--
-- Name: supplier_products supplier_products_pkey; Type: CONSTRAINT; Schema: procurement; Owner: -
--

ALTER TABLE ONLY procurement.supplier_products
    ADD CONSTRAINT supplier_products_pkey PRIMARY KEY (supplier_id, product_id);


--
-- Name: supplier_status_history supplier_status_history_pkey; Type: CONSTRAINT; Schema: procurement; Owner: -
--

ALTER TABLE ONLY procurement.supplier_status_history
    ADD CONSTRAINT supplier_status_history_pkey PRIMARY KEY (supplier_id, effective_from);


--
-- Name: suppliers suppliers_pkey; Type: CONSTRAINT; Schema: procurement; Owner: -
--

ALTER TABLE ONLY procurement.suppliers
    ADD CONSTRAINT suppliers_pkey PRIMARY KEY (supplier_id);


--
-- Name: idx_shipment_events_shipment_time; Type: INDEX; Schema: logistics; Owner: -
--

CREATE INDEX idx_shipment_events_shipment_time ON logistics.shipment_events USING btree (shipment_id, event_timestamp DESC);


--
-- Name: idx_shipment_exception_events_history; Type: INDEX; Schema: logistics; Owner: -
--

CREATE INDEX idx_shipment_exception_events_history ON logistics.shipment_exception_events USING btree (exception_id, event_timestamp);


--
-- Name: idx_shipment_exceptions_severity; Type: INDEX; Schema: logistics; Owner: -
--

CREATE INDEX idx_shipment_exceptions_severity ON logistics.shipment_exceptions USING btree (severity);


--
-- Name: idx_shipment_exceptions_shipment; Type: INDEX; Schema: logistics; Owner: -
--

CREATE INDEX idx_shipment_exceptions_shipment ON logistics.shipment_exceptions USING btree (shipment_id);


--
-- Name: idx_shipment_exceptions_status; Type: INDEX; Schema: logistics; Owner: -
--

CREATE INDEX idx_shipment_exceptions_status ON logistics.shipment_exceptions USING btree (exception_status);


--
-- Name: idx_shipments_estimated_delivery; Type: INDEX; Schema: logistics; Owner: -
--

CREATE INDEX idx_shipments_estimated_delivery ON logistics.shipments USING btree (estimated_delivery_date);


--
-- Name: idx_shipments_status; Type: INDEX; Schema: logistics; Owner: -
--

CREATE INDEX idx_shipments_status ON logistics.shipments USING btree (shipment_status);


--
-- Name: idx_shipments_supplier; Type: INDEX; Schema: logistics; Owner: -
--

CREATE INDEX idx_shipments_supplier ON logistics.shipments USING btree (supplier_id);


--
-- Name: shipment_events shipment_events_shipment_id_fkey; Type: FK CONSTRAINT; Schema: logistics; Owner: -
--

ALTER TABLE ONLY logistics.shipment_events
    ADD CONSTRAINT shipment_events_shipment_id_fkey FOREIGN KEY (shipment_id) REFERENCES logistics.shipments(shipment_id);


--
-- Name: shipment_exception_events shipment_exception_events_exception_id_fkey; Type: FK CONSTRAINT; Schema: logistics; Owner: -
--

ALTER TABLE ONLY logistics.shipment_exception_events
    ADD CONSTRAINT shipment_exception_events_exception_id_fkey FOREIGN KEY (exception_id) REFERENCES logistics.shipment_exceptions(exception_id);


--
-- Name: shipment_exceptions shipment_exceptions_shipment_id_fkey; Type: FK CONSTRAINT; Schema: logistics; Owner: -
--

ALTER TABLE ONLY logistics.shipment_exceptions
    ADD CONSTRAINT shipment_exceptions_shipment_id_fkey FOREIGN KEY (shipment_id) REFERENCES logistics.shipments(shipment_id);


--
-- Name: shipments shipments_delivery_id_fkey; Type: FK CONSTRAINT; Schema: logistics; Owner: -
--

ALTER TABLE ONLY logistics.shipments
    ADD CONSTRAINT shipments_delivery_id_fkey FOREIGN KEY (delivery_id) REFERENCES logistics.supplier_deliveries(delivery_id);


--
-- Name: shipments shipments_supplier_id_fkey; Type: FK CONSTRAINT; Schema: logistics; Owner: -
--

ALTER TABLE ONLY logistics.shipments
    ADD CONSTRAINT shipments_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES procurement.suppliers(supplier_id);


--
-- Name: supplier_deliveries supplier_deliveries_supplier_id_fkey; Type: FK CONSTRAINT; Schema: logistics; Owner: -
--

ALTER TABLE ONLY logistics.supplier_deliveries
    ADD CONSTRAINT supplier_deliveries_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES procurement.suppliers(supplier_id);


--
-- Name: supplier_inventory_history supplier_inventory_history_supplier_id_product_id_fkey; Type: FK CONSTRAINT; Schema: logistics; Owner: -
--

ALTER TABLE ONLY logistics.supplier_inventory_history
    ADD CONSTRAINT supplier_inventory_history_supplier_id_product_id_fkey FOREIGN KEY (supplier_id, product_id) REFERENCES procurement.supplier_products(supplier_id, product_id);


--
-- Name: supplier_quality_inspections supplier_quality_inspections_supplier_id_fkey; Type: FK CONSTRAINT; Schema: logistics; Owner: -
--

ALTER TABLE ONLY logistics.supplier_quality_inspections
    ADD CONSTRAINT supplier_quality_inspections_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES procurement.suppliers(supplier_id);


--
-- Name: analyst_assessments analyst_assessments_quotation_id_fkey; Type: FK CONSTRAINT; Schema: procurement; Owner: -
--

ALTER TABLE ONLY procurement.analyst_assessments
    ADD CONSTRAINT analyst_assessments_quotation_id_fkey FOREIGN KEY (quotation_id) REFERENCES procurement.quotations(quotation_id);


--
-- Name: analyst_assessments analyst_assessments_requisition_id_fkey; Type: FK CONSTRAINT; Schema: procurement; Owner: -
--

ALTER TABLE ONLY procurement.analyst_assessments
    ADD CONSTRAINT analyst_assessments_requisition_id_fkey FOREIGN KEY (requisition_id) REFERENCES procurement.purchase_requisitions(requisition_id);


--
-- Name: procurement_approvals procurement_approvals_decision_id_fkey; Type: FK CONSTRAINT; Schema: procurement; Owner: -
--

ALTER TABLE ONLY procurement.procurement_approvals
    ADD CONSTRAINT procurement_approvals_decision_id_fkey FOREIGN KEY (decision_id) REFERENCES procurement.procurement_decisions(decision_id);


--
-- Name: procurement_approvals procurement_approvals_requisition_id_fkey; Type: FK CONSTRAINT; Schema: procurement; Owner: -
--

ALTER TABLE ONLY procurement.procurement_approvals
    ADD CONSTRAINT procurement_approvals_requisition_id_fkey FOREIGN KEY (requisition_id) REFERENCES procurement.purchase_requisitions(requisition_id);


--
-- Name: procurement_decision_audit procurement_decision_audit_decision_id_fkey; Type: FK CONSTRAINT; Schema: procurement; Owner: -
--

ALTER TABLE ONLY procurement.procurement_decision_audit
    ADD CONSTRAINT procurement_decision_audit_decision_id_fkey FOREIGN KEY (decision_id) REFERENCES procurement.procurement_decisions(decision_id);


--
-- Name: procurement_decision_audit procurement_decision_audit_requisition_id_fkey; Type: FK CONSTRAINT; Schema: procurement; Owner: -
--

ALTER TABLE ONLY procurement.procurement_decision_audit
    ADD CONSTRAINT procurement_decision_audit_requisition_id_fkey FOREIGN KEY (requisition_id) REFERENCES procurement.purchase_requisitions(requisition_id);


--
-- Name: procurement_decisions procurement_decisions_requisition_id_fkey; Type: FK CONSTRAINT; Schema: procurement; Owner: -
--

ALTER TABLE ONLY procurement.procurement_decisions
    ADD CONSTRAINT procurement_decisions_requisition_id_fkey FOREIGN KEY (requisition_id) REFERENCES procurement.purchase_requisitions(requisition_id);


--
-- Name: procurement_decisions procurement_decisions_selected_quotation_id_fkey; Type: FK CONSTRAINT; Schema: procurement; Owner: -
--

ALTER TABLE ONLY procurement.procurement_decisions
    ADD CONSTRAINT procurement_decisions_selected_quotation_id_fkey FOREIGN KEY (selected_quotation_id) REFERENCES procurement.quotations(quotation_id);


--
-- Name: purchase_requisitions purchase_requisitions_product_id_fkey; Type: FK CONSTRAINT; Schema: procurement; Owner: -
--

ALTER TABLE ONLY procurement.purchase_requisitions
    ADD CONSTRAINT purchase_requisitions_product_id_fkey FOREIGN KEY (product_id) REFERENCES procurement.products(product_id);


--
-- Name: quotation_items quotation_items_product_id_fkey; Type: FK CONSTRAINT; Schema: procurement; Owner: -
--

ALTER TABLE ONLY procurement.quotation_items
    ADD CONSTRAINT quotation_items_product_id_fkey FOREIGN KEY (product_id) REFERENCES procurement.products(product_id);


--
-- Name: quotation_items quotation_items_quotation_id_fkey; Type: FK CONSTRAINT; Schema: procurement; Owner: -
--

ALTER TABLE ONLY procurement.quotation_items
    ADD CONSTRAINT quotation_items_quotation_id_fkey FOREIGN KEY (quotation_id) REFERENCES procurement.quotations(quotation_id);


--
-- Name: quotations quotations_requisition_id_fkey; Type: FK CONSTRAINT; Schema: procurement; Owner: -
--

ALTER TABLE ONLY procurement.quotations
    ADD CONSTRAINT quotations_requisition_id_fkey FOREIGN KEY (requisition_id) REFERENCES procurement.purchase_requisitions(requisition_id);


--
-- Name: quotations quotations_supplier_id_fkey; Type: FK CONSTRAINT; Schema: procurement; Owner: -
--

ALTER TABLE ONLY procurement.quotations
    ADD CONSTRAINT quotations_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES procurement.suppliers(supplier_id);


--
-- Name: supplier_compliance_history supplier_compliance_history_supplier_id_category_fkey; Type: FK CONSTRAINT; Schema: procurement; Owner: -
--

ALTER TABLE ONLY procurement.supplier_compliance_history
    ADD CONSTRAINT supplier_compliance_history_supplier_id_category_fkey FOREIGN KEY (supplier_id, category) REFERENCES procurement.supplier_compliance(supplier_id, category);


--
-- Name: supplier_compliance supplier_compliance_supplier_id_fkey; Type: FK CONSTRAINT; Schema: procurement; Owner: -
--

ALTER TABLE ONLY procurement.supplier_compliance
    ADD CONSTRAINT supplier_compliance_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES procurement.suppliers(supplier_id);


--
-- Name: supplier_products supplier_products_product_id_fkey; Type: FK CONSTRAINT; Schema: procurement; Owner: -
--

ALTER TABLE ONLY procurement.supplier_products
    ADD CONSTRAINT supplier_products_product_id_fkey FOREIGN KEY (product_id) REFERENCES procurement.products(product_id);


--
-- Name: supplier_products supplier_products_supplier_id_fkey; Type: FK CONSTRAINT; Schema: procurement; Owner: -
--

ALTER TABLE ONLY procurement.supplier_products
    ADD CONSTRAINT supplier_products_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES procurement.suppliers(supplier_id);


--
-- Name: supplier_status_history supplier_status_history_supplier_id_fkey; Type: FK CONSTRAINT; Schema: procurement; Owner: -
--

ALTER TABLE ONLY procurement.supplier_status_history
    ADD CONSTRAINT supplier_status_history_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES procurement.suppliers(supplier_id);


--
-- PostgreSQL database dump complete
--

\unrestrict Q2SbNFUWrUMVVkmacGqngQjiolr0Djen8bSsrMSlmS54xoee4HXTf1PhbKZA4re

