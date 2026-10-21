
"""
NovaTech Industries
Intelligent Procurement & Logistics Management Platform

Procurement & Logistics Analytics Dashboard — V10 | Logistics Risk Intelligence

Data source:
PostgreSQL -> Supplier Evaluation Engine V5 -> Streamlit

All data is synthetic and unverified.
No purchasing decisions are automatically authorized.
"""

import pandas as pd
import streamlit as st

from src.analysis.evaluate_suppliers_v5 import evaluate
from src.analysis.procurement_insights import generate_procurement_insights
from src.analysis.logistics_delivery_performance import generate_delivery_performance
from src.analysis.shipment_monitoring import generate_shipment_monitoring
from src.analysis.logistics_risk_intelligence import generate_logistics_risk_intelligence
from src.database.shipment_tracking_service import get_shipment_events, list_shipments
from src.database.assessment_service import save_analyst_assessment
from src.database.shipment_exception_service import (
    ShipmentExceptionError,
    EXCEPTION_TYPES,
    SEVERITIES,
    create_exception,
    assign_exception,
    start_investigation,
    record_corrective_action,
    add_exception_note,
    resolve_exception,
    close_exception,
    get_exception_events,
    list_exceptions,
)
from src.database.connection import get_connection

# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="NovaTech | Procurement & Logistics Analytics",
    page_icon="📊",
    layout="wide",
)



# --------------------------------------------------
# Dashboard V5: Modern Dark visual system
# Presentation only; no procurement rules are changed.
# --------------------------------------------------

st.markdown(
    """
    <style>
    :root {
        color-scheme: dark;
        --nt-bg: #080E1C;
        --nt-panel: #101B2E;
        --nt-panel-2: #14233A;
        --nt-border: #263A54;
        --nt-text: #ECF3FF;
        --nt-muted: #A4B5CF;
        --nt-accent: #5B9DFF;
        --nt-cyan: #42D3DC;
    }

    [data-testid="stAppViewContainer"],
    [data-testid="stApp"] {
        background:
            radial-gradient(ellipse at 82% 0%, rgba(47, 99, 187, 0.14), transparent 44%),
            var(--nt-bg);
        color: var(--nt-text);
    }

    [data-testid="stHeader"] {
        background: rgba(8, 14, 28, 0.86);
        backdrop-filter: blur(12px);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0C182C 0%, #0A1425 100%);
        border-right: 1px solid var(--nt-border);
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] label {
        color: var(--nt-muted);
    }

    [data-testid="stSidebar"] [role="radiogroup"] label {
        border: 1px solid transparent;
        border-radius: 10px;
        padding: 8px 10px;
        transition: background 0.15s ease, border-color 0.15s ease;
    }

    [data-testid="stSidebar"] [role="radiogroup"] label:hover {
        background: rgba(91, 157, 255, 0.10);
        border-color: rgba(91, 157, 255, 0.25);
    }

    .block-container {
        max-width: 1450px;
        padding-top: 2.3rem;
        padding-bottom: 4rem;
    }

    h1, h2, h3 {
        color: var(--nt-text) !important;
        letter-spacing: -0.025em;
    }

    h1 { font-weight: 750 !important; }
    h2 { font-weight: 680 !important; }

    [data-testid="stMetric"] {
        background: linear-gradient(145deg, var(--nt-panel), #152640);
        border: 1px solid var(--nt-border);
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 8px 26px rgba(0, 0, 0, 0.12);
        min-height: 118px;
    }

    [data-testid="stMetricLabel"] {
        color: var(--nt-muted);
    }

    [data-testid="stMetricValue"] {
        color: #F5F9FF;
        font-weight: 720;
    }

    [data-testid="stDataFrame"],
    [data-testid="stExpander"],
    [data-testid="stForm"] {
        border: 1px solid var(--nt-border);
        border-radius: 12px;
        overflow: hidden;
    }

    [data-testid="stForm"] {
        background: rgba(16, 27, 46, 0.6);
        padding: 16px;
    }

    [data-testid="stAlert"] {
        border-radius: 10px;
    }

    [data-testid="stCaptionContainer"],
    .stCaption {
        color: var(--nt-muted);
    }

    hr {
        border-color: var(--nt-border) !important;
        margin-top: 1.5rem;
        margin-bottom: 1.5rem;
    }

    .nt-hero {
        border: 1px solid var(--nt-border);
        border-radius: 18px;
        background: linear-gradient(110deg, #142744, #0F1C31 70%);
        padding: 26px 30px 22px;
        margin-bottom: 18px;
    }

    .nt-eyebrow {
        color: var(--nt-cyan);
        font-size: 0.76rem;
        font-weight: 750;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        margin-bottom: 10px;
    }

    .nt-hero h1 {
        margin: 0 0 6px;
        font-size: clamp(1.6rem, 3vw, 2.45rem);
        line-height: 1.2;
    }

    .nt-hero p {
        margin: 0;
        color: var(--nt-muted);
        font-size: 0.98rem;
    }

    .nt-sidebar-brand {
        font-size: 1.3rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        color: #F3F7FF;
    }

    .nt-sidebar-brand span { color: var(--nt-cyan); }

    .nt-sidebar-subtitle {
        color: var(--nt-muted);
        font-size: 0.78rem;
        margin: 5px 0 24px;
    }

    .nt-sidebar-foot {
        padding: 12px 14px;
        border: 1px solid var(--nt-border);
        border-radius: 12px;
        background: rgba(91, 157, 255, 0.05);
        color: var(--nt-muted);
        font-size: 0.78rem;
        line-height: 1.6;
    }

    .nt-sidebar-foot strong {
        color: #F8C979;
    }

    [data-testid="stButton"] button[kind="primary"],
    [data-testid="stFormSubmitButton"] button {
        border-radius: 9px;
        font-weight: 650;
    }

    @media (max-width: 768px) {
        .block-container { padding-top: 1rem; }
        .nt-hero { padding: 18px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# Human-readable evaluation reasons
# --------------------------------------------------

REASON_DESCRIPTIONS = {
    "INACTIVE_SUPPLIER":
        "The supplier was not active at the evaluation date.",
    "CATEGORY_COMPLIANCE_NOT_APPROVED":
        "The supplier did not have approved compliance for this product category.",
    "CATEGORY_COMPLIANCE_EXPIRED":
        "The supplier's category compliance had expired.",
    "SUPPLIER_STATUS_SYNTHETIC_OR_UNVERIFIED":
        "Supplier status is based on synthetic or unverified evidence.",
    "CATEGORY_COMPLIANCE_SYNTHETIC_OR_UNVERIFIED":
        "Category compliance is based on synthetic or unverified evidence.",
    "INVENTORY_SYNTHETIC_OR_UNVERIFIED":
        "Inventory availability is based on synthetic or unverified evidence.",
    "DECISION_TIMESTAMP_NOT_VERIFIED":
        "The exact decision timestamp has not been independently verified.",
    "INSUFFICIENT_PERFORMANCE_HISTORY":
        "There is insufficient historical evidence to calculate reliable performance metrics.",
    "QUOTATION_PREDATES_REQUISITION":
        "The quotation was issued before the purchase requisition.",
    "QUOTATION_EXPIRY_BEFORE_ISSUE":
        "The quotation expiry date precedes its issue date.",
    "QUOTATION_EXPIRED_AT_CUTOFF":
        "The quotation had expired at the evaluation cutoff.",
    "INVALID_QUOTATION_STATUS":
        "The quotation does not have the required RECEIVED status.",
    "INSUFFICIENT_QUOTED_QUANTITY":
        "The supplier quoted fewer units than requested.",
    "DELIVERY_AFTER_REQUIRED_DATE":
        "The quoted delivery date exceeds the required delivery deadline.",
    "SUPPLIER_PRODUCT_RELATIONSHIP_MISSING":
        "The supplier is not registered for this product.",
    "BELOW_MINIMUM_ORDER":
        "The quoted quantity is below the supplier's minimum order quantity.",
    "INSUFFICIENT_AVAILABLE_STOCK":
        "The supplier's historical inventory cannot cover the quoted quantity.",
}


# --------------------------------------------------
# Load evaluation and reference data
# --------------------------------------------------

@st.cache_data(show_spinner="Loading procurement data...")
def load_dashboard_data():

    results = evaluate()
    datasets = results["datasets"]

    evaluations = pd.DataFrame(results["evaluations"])

    suppliers = pd.DataFrame(datasets["suppliers"])
    products = pd.DataFrame(datasets["products"])

    requisitions = pd.DataFrame(
        datasets["purchase_requisitions"]
    )

    # Supplier information
    evaluations = evaluations.merge(
        suppliers[["supplier_id", "supplier_name"]],
        on="supplier_id",
        how="left",
        validate="many_to_one",
    )

    # Product information
    evaluations = evaluations.merge(
        products[
            [
                "product_id",
                "sku",
                "product_name",
                "category",
                "unit_of_measure",
            ]
        ].rename(
            columns={"category": "product_category"}
        ),
        on="product_id",
        how="left",
        validate="many_to_one",
    )

    # Purchase requisition context
    evaluations = evaluations.merge(
        requisitions[
            [
                "requisition_id",
                "requested_quantity",
                "request_date",
                "required_delivery_date",
            ]
        ],
        on="requisition_id",
        how="left",
        validate="many_to_one",
    )

    return evaluations


# --------------------------------------------------
# Dashboard header
# --------------------------------------------------

st.markdown(
    """
    <div class="nt-hero">
        <div class="nt-eyebrow">Procurement &amp; logistics intelligence / Analytics V10</div>
        <h1>NovaTech Industries</h1>
        <p>Intelligent Procurement &amp; Logistics Management Platform
        &nbsp;·&nbsp; PostgreSQL + Supplier Evaluation Engine V5</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.warning(
    "SIMULATION ENVIRONMENT — Historical evidence is synthetic and "
    "unverified. No purchasing decisions are automatically authorized."
)


# --------------------------------------------------
# Retrieve results
# --------------------------------------------------

try:
    df = load_dashboard_data()

except Exception as error:
    st.error("Unable to load procurement evaluation data.")
    st.exception(error)
    st.stop()


if df.empty:
    st.info("No procurement evaluations are available.")
    st.stop()


# --------------------------------------------------
# Prepare numerical columns
# --------------------------------------------------

numeric_columns = [
    "total_cost_eur",
    "lead_time_days",
    "quality_score",
    "reliability_score",
    "weighted_score",
    "requested_quantity",
]

for column in numeric_columns:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce",
    )



@st.cache_data(show_spinner="Loading decision records...")
def load_decision_records():

    with get_connection() as conn:

        decisions = pd.read_sql_query(
            """
            SELECT *
            FROM procurement.procurement_decisions
            ORDER BY requisition_id
            """,
            conn,
        )

        approvals = pd.read_sql_query(
            """
            SELECT *
            FROM procurement.procurement_approvals
            ORDER BY approval_requested_at
            """,
            conn,
        )

        audit = pd.read_sql_query(
            """
            SELECT *
            FROM procurement.procurement_decision_audit
            ORDER BY event_date
            """,
            conn,
        )

    return decisions, approvals, audit


@st.cache_data(show_spinner="Loading analyst assessments...")
def load_analyst_assessments():

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    assessment_id,
                    requisition_id,
                    quotation_id,
                    analyst_name,
                    assessment_status,
                    assessment_notes,
                    decision_mode,
                    authorization_status,
                    created_at
                FROM procurement.analyst_assessments
                ORDER BY created_at DESC, assessment_id DESC
                """
            )

            columns = [
                column.name
                for column in cur.description
            ]

            return pd.DataFrame(
                cur.fetchall(),
                columns=columns,
            )



# --------------------------------------------------
# Sidebar navigation
# --------------------------------------------------

with st.sidebar:
    st.markdown(
        '<div class="nt-sidebar-brand">NOVA<span>TECH</span></div>'
        '<div class="nt-sidebar-subtitle">Intelligent Procurement Platform</div>',
        unsafe_allow_html=True,
    )

    page = st.radio(
        "WORKSPACE",
        [
            "Procurement Overview",
            "Supplier Comparison",
            "Procurement Insights",
            "Logistics Intelligence",
            "Shipment Tracking",
            "Shipment Exception Management",
            "Decision & Audit Trail",
            "Analyst Workspace",
            "Logistics Risk Intelligence",
            "Logistics Risk Scenario Analysis",
        ],
        key="dashboard_page",
    )

    st.divider()
    st.markdown(
        '<div class="nt-sidebar-foot">'
        '<strong>SIMULATION ONLY</strong><br>'
        'Evidence: SYNTHETIC_UNVERIFIED<br>'
        'Authorization: NOT_AUTHORIZED'
        '</div>',
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner="Calculating procurement insights...")
def load_procurement_insights():
    """Read-only analytical summaries from the V5 evaluation engine."""
    return generate_procurement_insights()


@st.cache_data(show_spinner="Loading logistics delivery performance...")
def load_logistics_delivery_performance():
    """Read-only supplier delivery KPIs from PostgreSQL."""
    return generate_delivery_performance()


@st.cache_data(show_spinner="Loading shipment monitoring...")
def load_shipment_monitoring():
    """Read-only shipment monitoring metrics from PostgreSQL."""
    return generate_shipment_monitoring()


@st.cache_data(show_spinner="Loading shipment tracking records...")
def load_shipment_tracking_records():
    return list_shipments()


@st.cache_data(show_spinner="Loading tracking events...")
def load_tracking_events(shipment_id):
    return get_shipment_events(shipment_id)


@st.cache_data(show_spinner="Loading shipment exceptions...")
def load_shipment_exceptions():
    return list_exceptions()


@st.cache_data(show_spinner="Loading exception audit history...")
def load_shipment_exception_events(exception_id):
    return get_exception_events(exception_id)


def refresh_exception_data():
    load_shipment_exceptions.clear()
    load_shipment_exception_events.clear()


def show_shipment_exception_management():
    """Simulated exception reporting, investigation and audit history."""
    st.divider()
    st.header("Shipment Exception Management")
    st.caption(
        "Record and investigate simulated logistics incidents with "
        "a traceable, append-only audit history."
    )
    st.warning(
        "SIMULATION ONLY — All incident records are synthetic and unverified. "
        "Exception actions do not change shipment status, contact carriers, "
        "or authorize purchases."
    )

    if st.button("Refresh exception records", key="exception_refresh"):
        refresh_exception_data()
        load_shipment_tracking_records.clear()
        st.rerun()

    try:
        shipments = load_shipment_tracking_records()
        exceptions = load_shipment_exceptions()
    except Exception as error:
        st.error("Unable to load shipment exception records.")
        st.exception(error)
        return

    total = len(exceptions)
    active = sum(row["exception_status"] in {"OPEN", "INVESTIGATING"} for row in exceptions)
    critical = sum(row["severity"] == "CRITICAL" and row["exception_status"] != "CLOSED" for row in exceptions)
    closed = sum(row["exception_status"] == "CLOSED" for row in exceptions)
    a, b, c, d = st.columns(4)
    a.metric("Total Exceptions", total)
    b.metric("Active Investigations", active)
    c.metric("Unclosed Critical", critical)
    d.metric("Closed", closed)

    st.divider()
    st.subheader("Report a Simulated Exception")
    if not shipments:
        st.info("Create a simulated shipment in Shipment Tracking before reporting an exception.")
    else:
        shipment_options = sorted(row["shipment_id"] for row in shipments)
        with st.form("exception_report_form", clear_on_submit=True):
            shipment_id = st.selectbox("Shipment", shipment_options, key="exception_new_shipment")
            col_type, col_severity = st.columns(2)
            with col_type:
                exception_type = st.selectbox("Exception Type", sorted(EXCEPTION_TYPES))
            with col_severity:
                severity = st.selectbox("Severity", ["LOW", "MEDIUM", "HIGH", "CRITICAL"], index=1)
            description = st.text_area("Incident Description", height=100)
            reported_by = st.text_input("Reported By")
            assigned_to = st.text_input("Initial Assignee (optional)")
            submit_report = st.form_submit_button("Record Simulated Exception")
        if submit_report:
            try:
                new_id = create_exception(
                    shipment_id=shipment_id,
                    exception_type=exception_type,
                    severity=severity,
                    description=description,
                    reported_by=reported_by,
                    assigned_to=assigned_to or None,
                )
            except Exception as error:
                st.error(f"Unable to report exception: {error}")
            else:
                refresh_exception_data()
                st.success(f"Simulated exception #{new_id} recorded with a REPORTED audit event.")
                st.rerun()

    st.divider()
    st.subheader("Exception Register")
    if not exceptions:
        st.info("No simulated shipment exceptions have been recorded.")
        return

    register = pd.DataFrame(exceptions)
    filter_col, severity_col = st.columns(2)
    with filter_col:
        status_filter = st.selectbox(
            "Filter by investigation status",
            ["All", "OPEN", "INVESTIGATING", "RESOLVED", "CLOSED"],
            key="exception_status_filter",
        )
    with severity_col:
        severity_filter = st.selectbox(
            "Filter by severity",
            ["All", "LOW", "MEDIUM", "HIGH", "CRITICAL"],
            key="exception_severity_filter",
        )
    if status_filter != "All":
        register = register[register["exception_status"] == status_filter]
    if severity_filter != "All":
        register = register[register["severity"] == severity_filter]
    st.dataframe(
        register[[
            "exception_id", "shipment_id", "exception_type", "severity",
            "exception_status", "assigned_to", "reported_by", "reported_at",
            "resolved_at", "closed_at",
        ]],
        hide_index=True,
        use_container_width=True,
    )

    st.divider()
    st.subheader("Investigation Workspace")
    by_id = {row["exception_id"]: row for row in exceptions}
    selected_id = st.selectbox(
        "Select exception",
        sorted(by_id, reverse=True),
        format_func=lambda value: (
            f"#{value} · {by_id[value]['shipment_id']} · "
            f"{by_id[value]['exception_type']} · {by_id[value]['exception_status']}"
        ),
        key="exception_selected_id",
    )
    selected = by_id[selected_id]
    st.write(f"**Incident:** {selected['description']}")
    st.write(
        f"**Severity:** {selected['severity']}  |  "
        f"**Status:** {selected['exception_status']}  |  "
        f"**Assigned to:** {selected['assigned_to'] or 'Unassigned'}"
    )
    if selected["corrective_action"]:
        st.write("**Latest corrective action:**", selected["corrective_action"])
    if selected["resolution_notes"]:
        st.write("**Resolution notes:**", selected["resolution_notes"])

    status = selected["exception_status"]
    available_actions = []
    if status in {"OPEN", "INVESTIGATING"}:
        available_actions.append("Assign Analyst")
    if status == "OPEN":
        available_actions.append("Start Investigation")
    if status == "INVESTIGATING":
        available_actions.extend(["Record Corrective Action", "Resolve Exception"])
    if status == "RESOLVED":
        available_actions.append("Close Exception")
    if status != "CLOSED":
        available_actions.append("Add Note")

    if available_actions:
        action = st.selectbox("Investigation Action", available_actions, key="exception_action")
        with st.form("exception_action_form", clear_on_submit=True):
            actor = st.text_input("Recorded By (analyst or manager)")
            if action == "Assign Analyst":
                action_text = st.text_input("Assign To")
            elif action == "Start Investigation":
                action_text = st.text_area("Investigation Description")
            elif action == "Record Corrective Action":
                action_text = st.text_area("Corrective Action")
            elif action == "Resolve Exception":
                action_text = st.text_area("Resolution Notes")
            elif action == "Close Exception":
                action_text = st.text_area("Closure Description")
            else:
                action_text = st.text_area("Audit Note")
            submitted_action = st.form_submit_button("Save Simulated Action")
        if submitted_action:
            try:
                if action == "Assign Analyst":
                    assign_exception(selected_id, action_text, actor)
                elif action == "Start Investigation":
                    start_investigation(selected_id, actor, action_text)
                elif action == "Record Corrective Action":
                    record_corrective_action(selected_id, action_text, actor)
                elif action == "Resolve Exception":
                    resolve_exception(selected_id, action_text, actor)
                elif action == "Close Exception":
                    close_exception(selected_id, actor, action_text)
                else:
                    add_exception_note(selected_id, action_text, actor)
            except Exception as error:
                st.error(f"Unable to save simulated action: {error}")
            else:
                refresh_exception_data()
                st.success(f"{action} recorded for exception #{selected_id}.")
                st.rerun()
    else:
        st.info("This exception is CLOSED. Further modifications are prohibited.")

    st.divider()
    st.subheader("Exception Audit History")
    try:
        audit_events = load_shipment_exception_events(selected_id)
    except Exception as error:
        st.error("Unable to load exception audit events.")
        st.exception(error)
    else:
        if audit_events:
            st.dataframe(
                pd.DataFrame(audit_events)[[
                    "event_timestamp", "event_type", "previous_status",
                    "new_status", "event_description", "recorded_by",
                    "simulation_mode",
                ]],
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info("No audit events recorded for this exception.")

    st.divider()
    st.subheader("Governance")
    st.write("**Decision mode:** SIMULATION")
    st.write("**Evidence classification:** SYNTHETIC_UNVERIFIED")
    st.write("**Authorization:** NOT_AUTHORIZED")
    st.caption(
        "Exception management is separate from shipment lifecycle tracking. "
        "Resolving or closing an exception never marks a shipment DELIVERED."
    )


def show_overview():
    # --------------------------------------------------
    # Procurement overview
    # --------------------------------------------------

    st.divider()
    st.header("Procurement Overview")
    st.caption("Portfolio-level procurement activity, quotation risk, and evaluation coverage.")

    total_quotations = len(df)
    total_requisitions = df["requisition_id"].nunique()

    review_required = int(
        (df["evaluation_status"] == "REVIEW_REQUIRED").sum()
    )

    blocked = int(
        (df["evaluation_status"] == "BLOCKED").sum()
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Purchase Requisitions",
        total_requisitions,
    )

    col2.metric(
        "Supplier Quotations",
        total_quotations,
    )

    col3.metric(
        "Review Required",
        review_required,
    )

    col4.metric(
        "Blocked Quotations",
        blocked,
    )


    # --------------------------------------------------
    # Evaluation status distribution
    # --------------------------------------------------

    st.divider()
    st.header("Supplier Evaluation Status")

    status_counts = (
        df["evaluation_status"]
        .value_counts()
        .rename_axis("Status")
        .reset_index(name="Quotations")
    )

    left, right = st.columns([1, 2])

    with left:
        st.dataframe(
            status_counts,
            hide_index=True,
            use_container_width=True,
        )

    with right:
        st.bar_chart(
            status_counts.set_index("Status")["Quotations"]
        )


    # --------------------------------------------------
    # Quotation cost analysis
    # --------------------------------------------------

    st.divider()
    st.header("Quotation Cost Analysis")

    cost_data = df[
        [
            "quotation_id",
            "supplier_name",
            "requisition_id",
            "total_cost_eur",
        ]
    ].sort_values(
        "total_cost_eur",
        ascending=False,
    )

    st.bar_chart(
        cost_data.set_index("quotation_id")["total_cost_eur"]
    )

    st.caption(
        "Quoted costs are supplier offers in EUR, "
        "not actual procurement expenditure."
    )


    # --------------------------------------------------
    # Detailed supplier evaluations
    # --------------------------------------------------

    st.divider()
    st.header("Detailed Supplier Evaluations")

    selected_status = st.selectbox(
        "Filter by evaluation status",
        ["All"] + sorted(df["evaluation_status"].unique()),
    )

    if selected_status == "All":
        filtered_df = df.copy()

    else:
        filtered_df = df[
            df["evaluation_status"] == selected_status
        ].copy()

    display_columns = [
        "quotation_id",
        "requisition_id",
        "supplier_name",
        "product_name",
        "total_cost_eur",
        "lead_time_days",
        "quality_score",
        "reliability_score",
        "evaluation_status",
        "recommendation_status",
    ]

    st.dataframe(
        filtered_df[display_columns],
        hide_index=True,
        use_container_width=True,
    )

    st.caption(
        f"Displaying {len(filtered_df)} of "
        f"{len(df)} supplier evaluations."
    )


    # --------------------------------------------------
    # Procurement governance
    # --------------------------------------------------

    st.divider()
    st.header("Procurement Governance")

    st.info(
        "All recommendations are analytical simulations. "
        "The platform does not issue purchase orders or "
        "authorize procurement transactions."
    )

    st.write(
        "**Evidence classification:** SYNTHETIC_UNVERIFIED"
    )

    st.write(
        "**Decision timestamp:** NOT_VERIFIED"
    )

    st.write(
        "**Purchasing authorization:** NOT_AUTHORIZED"
    )




def show_supplier_comparison():
    # --------------------------------------------------
    # Interactive supplier comparison
    # --------------------------------------------------

    st.divider()
    st.header("Interactive Supplier Comparison")
    st.caption("Compare supplier offers and review the evidence behind each eligibility outcome.")

    st.write(
        "Select a purchase requisition to review the "
        "requested product and compare supplier quotations."
    )

    requisition_options = sorted(
        df["requisition_id"].unique()
    )

    selected_requisition = st.selectbox(
        "Select Purchase Requisition",
        requisition_options,
    )

    comparison_df = df[
        df["requisition_id"] == selected_requisition
    ].copy()

    comparison_df = comparison_df.sort_values(
        ["total_cost_eur", "quotation_id"]
    )

    # --------------------------------------------------
    # Requisition details
    # --------------------------------------------------

    requisition = comparison_df.iloc[0]

    st.subheader("Purchase Requisition Details")

    info1, info2, info3, info4 = st.columns(4)

    info1.metric(
        "Product",
        requisition["product_name"],
    )

    info2.metric(
        "Requested Quantity",
        f"{int(requisition['requested_quantity'])} "
        f"{requisition['unit_of_measure']}",
    )

    info3.metric(
        "Required Delivery",
        requisition["required_delivery_date"],
    )

    info4.metric(
        "Supplier Quotations",
        len(comparison_df),
    )

    st.caption(
        f"Requisition: {selected_requisition} | "
        f"SKU: {requisition['sku']} | "
        f"Category: {requisition['product_category']} | "
        f"Request date: {requisition['request_date']}"
    )


    # --------------------------------------------------
    # Supplier quotation comparison
    # --------------------------------------------------

    st.subheader("Supplier Quotation Comparison")

    comparison_columns = [
        "supplier_name",
        "quotation_id",
        "total_cost_eur",
        "lead_time_days",
        "quality_score",
        "reliability_score",
        "evaluation_status",
    ]

    st.dataframe(
        comparison_df[comparison_columns],
        hide_index=True,
        use_container_width=True,
        column_config={
            "supplier_name": "Supplier",
            "quotation_id": "Quotation",
            "total_cost_eur": st.column_config.NumberColumn(
                "Total Cost (EUR)",
                format="€%.2f",
            ),
            "lead_time_days": st.column_config.NumberColumn(
                "Lead Time (Days)",
                format="%d",
            ),
            "quality_score": st.column_config.NumberColumn(
                "Quality (%)",
                format="%.2f",
            ),
            "reliability_score": st.column_config.NumberColumn(
                "Reliability (%)",
                format="%.2f",
            ),
            "evaluation_status": "Evaluation Status",
        },
    )


    # --------------------------------------------------
    # Supplier cost comparison
    # --------------------------------------------------

    st.subheader("Supplier Cost Comparison")

    cost_chart = comparison_df.set_index(
        "supplier_name"
    )["total_cost_eur"]

    st.bar_chart(cost_chart)


    # --------------------------------------------------
    # Delivery lead-time comparison
    # --------------------------------------------------

    st.subheader("Supplier Delivery Lead Times")

    lead_time_chart = comparison_df.set_index(
        "supplier_name"
    )["lead_time_days"]

    st.bar_chart(lead_time_chart)


    # --------------------------------------------------
    # Historical supplier performance
    # --------------------------------------------------

    st.subheader("Historical Supplier Performance")

    performance_chart = comparison_df[
        [
            "supplier_name",
            "quality_score",
            "reliability_score",
        ]
    ].set_index("supplier_name")

    st.bar_chart(performance_chart)

    st.caption(
        "Performance metrics are calculated from synthetic "
        "historical inspections and delivery records. "
        "They are not independently verified."
    )


    # --------------------------------------------------
    # Supplier eligibility explanations
    # --------------------------------------------------

    st.subheader("Supplier Eligibility Explanations")

    for _, supplier in comparison_df.iterrows():

        with st.expander(
            f"{supplier['supplier_name']} "
            f"({supplier['supplier_id']}) | "
            f"{supplier['evaluation_status']}"
        ):

            st.write(
                "**Quotation:**",
                supplier["quotation_id"],
            )

            st.write(
                "**Evaluation status:**",
                supplier["evaluation_status"],
            )

            st.write(
                "**Recommendation status:**",
                supplier["recommendation_status"],
            )

            reasons = supplier["reasons"]

            if pd.notna(reasons) and reasons:

                st.write("**Evaluation findings:**")

                for reason in reasons.split(";"):

                    description = REASON_DESCRIPTIONS.get(
                        reason,
                        reason.replace("_", " ").capitalize(),
                    )

                    st.write(f"- {description}")

            else:
                st.write(
                    "No blocking or review reasons recorded."
                )

            st.info(
                "This evaluation is analytical only. "
                "Purchasing authorization remains prohibited."
            )




def show_decision_audit():
    st.divider()
    st.header("Procurement Decision & Audit Trail")
    st.caption("Read-only decisions, human review records, and audit evidence.")

    st.write(
        "Review recorded procurement decisions, approval "
        "statuses, and historical audit events."
    )

    try:
        decisions_df, approvals_df, audit_df = (
            load_decision_records()
        )

    except Exception as error:
        st.error("Unable to load procurement decision records.")
        st.exception(error)
        st.stop()


    # --------------------------------------------------
    # Decision overview
    # --------------------------------------------------

    st.subheader("Decision Overview")

    decision_summary = (
        decisions_df["decision_status"]
        .value_counts()
        .rename_axis("Decision Status")
        .reset_index(name="Decisions")
    )

    st.dataframe(
        decision_summary,
        hide_index=True,
        use_container_width=True,
    )


    # --------------------------------------------------
    # Select requisition
    # --------------------------------------------------

    decision_requisition = st.selectbox(
        "Select Requisition for Decision Review",
        sorted(decisions_df["requisition_id"].unique()),
        key="decision_requisition",
    )

    selected_decisions = decisions_df[
        decisions_df["requisition_id"]
        == decision_requisition
    ]

    st.subheader("Recorded Procurement Decision")

    st.dataframe(
        selected_decisions[
            [
                "decision_id",
                "requisition_id",
                "decision_date",
                "decision_mode",
                "decision_status",
                "selected_quotation_id",
                "decision_reason",
                "approval_status",
            ]
        ],
        hide_index=True,
        use_container_width=True,
    )


    # --------------------------------------------------
    # Approval records
    # --------------------------------------------------

    st.subheader("Human Review & Approval Status")

    selected_approvals = approvals_df[
        approvals_df["requisition_id"]
        == decision_requisition
    ]

    st.dataframe(
        selected_approvals[
            [
                "approval_id",
                "approval_stage",
                "approver_role",
                "approval_status",
                "authorization_effect",
                "approval_requested_at",
            ]
        ],
        hide_index=True,
        use_container_width=True,
    )


    # --------------------------------------------------
    # Audit trail
    # --------------------------------------------------

    st.subheader("Decision Audit Trail")

    selected_audit = audit_df[
        audit_df["requisition_id"]
        == decision_requisition
    ]

    st.dataframe(
        selected_audit[
            [
                "audit_id",
                "event_date",
                "event_type",
                "actor",
                "previous_status",
                "new_status",
                "event_details",
                "evidence_classification",
            ]
        ],
        hide_index=True,
        use_container_width=True,
    )


    # --------------------------------------------------
    # Governance safeguards
    # --------------------------------------------------

    st.warning(
        "All procurement decisions are simulations. "
        "Approval records are pending human review. "
        "No purchasing authorization has been granted."
    )




def show_analyst_workspace():
    st.divider()
    st.header("Analyst Assessment Workspace")
    st.caption("Record analytical judgments without granting purchasing authorization.")

    st.write(
        "Document procurement assessments for human review. "
        "All records are simulations and do not authorize purchases."
    )

    assessment_requisition = st.selectbox(
        "Purchase Requisition",
        sorted(df["requisition_id"].unique()),
        key="assessment_requisition",
    )

    assessment_quotations = df[
        df["requisition_id"] == assessment_requisition
    ].copy()

    quotation_options = {
        row["quotation_id"]: (
            f"{row['quotation_id']} — "
            f"{row['supplier_name']} — "
            f"{row['evaluation_status']}"
        )
        for _, row in assessment_quotations.iterrows()
    }

    assessment_quotation = st.selectbox(
        "Supplier Quotation",
        list(quotation_options.keys()),
        format_func=lambda quotation_id: quotation_options[quotation_id],
        key="assessment_quotation",
    )

    selected_assessment_row = assessment_quotations[
        assessment_quotations["quotation_id"]
        == assessment_quotation
    ].iloc[0]

    evaluation_status = selected_assessment_row[
        "evaluation_status"
    ]

    st.write(
        "**Current evaluation status:**",
        evaluation_status,
    )

    if evaluation_status == "BLOCKED":

        st.error(
            "This quotation is blocked. It cannot be recommended."
        )

        allowed_statuses = ["NOT_RECOMMENDED"]

    elif evaluation_status == "REVIEW_REQUIRED":

        st.warning(
            "This quotation requires further review. "
            "It cannot be approved for purchasing."
        )

        allowed_statuses = [
            "REVIEW_REQUIRED",
            "NOT_RECOMMENDED",
        ]

    else:

        st.info(
            "This quotation is eligible for analysis only. "
            "Purchasing authorization is not permitted."
        )

        allowed_statuses = [
            "REVIEW_REQUIRED",
            "NOT_RECOMMENDED",
        ]


    with st.form("analyst_assessment_form"):

        analyst_name = st.text_input(
            "Analyst Name"
        )

        assessment_status = st.selectbox(
            "Assessment Status",
            allowed_statuses,
        )

        assessment_notes = st.text_area(
            "Assessment Notes",
            placeholder=(
                "Explain your assessment, relevant risks, "
                "and any additional evidence required."
            ),
            height=140,
        )

        submitted = st.form_submit_button(
            "Save Simulated Assessment"
        )


    if submitted:

        if not analyst_name.strip():

            st.error("Please enter the analyst's name.")

        elif not assessment_notes.strip():

            st.error("Please enter assessment notes.")

        elif (
            evaluation_status == "BLOCKED"
            and assessment_status != "NOT_RECOMMENDED"
        ):

            st.error(
                "Blocked quotations must be marked NOT_RECOMMENDED."
            )

        else:

            try:

                assessment_id = save_analyst_assessment(
                    requisition_id=assessment_requisition,
                    quotation_id=assessment_quotation,
                    analyst_name=analyst_name.strip(),
                    assessment_status=assessment_status,
                    assessment_notes=assessment_notes.strip(),
                )

                load_analyst_assessments.clear()

                st.success(
                    f"Simulated assessment #{assessment_id} "
                    "saved successfully."
                )

            except Exception as error:

                st.error("Unable to save the assessment.")
                st.exception(error)


    # --------------------------------------------------
    # Saved assessment history
    # --------------------------------------------------

    st.subheader("Saved Analyst Assessments")

    try:

        assessments_history = load_analyst_assessments()

        if assessments_history.empty:

            st.info(
                "No analyst assessments have been recorded yet."
            )

        else:

            st.dataframe(
                assessments_history,
                hide_index=True,
                use_container_width=True,
            )

    except Exception as error:

        st.error("Unable to load assessment history.")
        st.exception(error)


    st.caption(
        "Governance safeguard: all analyst assessments "
        "have decision_mode=SIMULATION and "
        "authorization_status=NOT_AUTHORIZED."
    )



def show_procurement_insights():
    """Analytical opportunities and risks; no purchasing authorization."""
    st.divider()
    st.header("Procurement Insights")
    st.caption(
        "Explore quotation spreads, supplier risk indicators, delivery comparisons, "
        "and requisitions requiring human review."
    )
    st.info(
        "All figures are based on synthetic, unverified data. Quotation spreads "
        "are hypothetical comparisons—not realized savings, supplier selections, "
        "or purchasing approvals."
    )

    try:
        insights = load_procurement_insights()
    except Exception as error:
        st.error("Unable to calculate procurement insights.")
        st.exception(error)
        return

    cost_df = pd.DataFrame(insights["cost_opportunities"])
    risk_df = pd.DataFrame(insights["supplier_risks"])
    delivery_df = pd.DataFrame(insights["delivery_insights"])
    bottleneck_df = pd.DataFrame(insights["procurement_bottlenecks"])

    total_spread = (
        float(cost_df["potential_cost_difference_eur"].sum())
        if not cost_df.empty else 0.0
    )
    blocked_suppliers = (
        int((risk_df["risk_level"] == "BLOCKED").sum())
        if not risk_df.empty else 0
    )
    review_requisitions = (
        int(bottleneck_df["requires_human_review"].sum())
        if not bottleneck_df.empty else 0
    )
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Requisitions Analyzed", len(cost_df))
    col2.metric("Sum of Quotation Spreads", f"€{total_spread:,.2f}")
    col3.metric("Suppliers with Blocked Quotes", blocked_suppliers)
    col4.metric("Requisitions Requiring Review", review_requisitions)
    st.caption(
        "The sum of spreads is a descriptive comparison across requisitions, "
        "not an achievable savings forecast."
    )

    st.divider()
    st.subheader("1. Cost Comparison Opportunities")
    st.write(
        "For each requisition, compare the lowest and highest valid quoted totals. "
        "The cheapest quote may be blocked or require review."
    )
    if cost_df.empty:
        st.info("No quotation cost comparisons are available.")
    else:
        cost_columns = [
            "requisition_id", "quotation_count", "lowest_quotation_id",
            "lowest_cost_eur", "lowest_evaluation_status",
            "highest_quotation_id", "highest_cost_eur",
            "potential_cost_difference_eur", "potential_cost_difference_pct",
        ]
        st.dataframe(
            cost_df[cost_columns], hide_index=True, use_container_width=True,
            column_config={
                "requisition_id": "Requisition",
                "quotation_count": "Quotes",
                "lowest_quotation_id": "Lowest Quote",
                "lowest_cost_eur": st.column_config.NumberColumn(
                    "Lowest Cost (EUR)", format="€%.2f"
                ),
                "lowest_evaluation_status": "Lowest Quote Status",
                "highest_quotation_id": "Highest Quote",
                "highest_cost_eur": st.column_config.NumberColumn(
                    "Highest Cost (EUR)", format="€%.2f"
                ),
                "potential_cost_difference_eur": st.column_config.NumberColumn(
                    "Quotation Spread (EUR)", format="€%.2f"
                ),
                "potential_cost_difference_pct": st.column_config.NumberColumn(
                    "Spread (%)", format="%.2f%%"
                ),
            },
        )
        st.bar_chart(
            cost_df.set_index("requisition_id")[[
                "lowest_cost_eur", "highest_cost_eur"
            ]]
        )

    st.divider()
    st.subheader("2. Supplier Risk Indicators")
    st.write(
        "Supplier risk levels summarize quotation evaluation statuses. "
        "These are evidence and eligibility flags, not independent risk ratings."
    )
    if risk_df.empty:
        st.info("No supplier risk indicators are available.")
    else:
        suppliers_by_id = (
            df[["supplier_id", "supplier_name"]]
            .drop_duplicates(subset=["supplier_id"])
        )
        risk_display = risk_df.merge(
            suppliers_by_id, on="supplier_id", how="left", validate="one_to_one"
        )
        st.dataframe(
            risk_display[[
                "supplier_name", "supplier_id", "quotation_count",
                "blocked_quotations", "review_required_quotations", "risk_level",
                "reason_occurrences",
            ]],
            hide_index=True, use_container_width=True,
        )
        for _, supplier in risk_display.iterrows():
            with st.expander(
                f"{supplier['supplier_name']} ({supplier['supplier_id']}) "
                f"— {supplier['risk_level']}"
            ):
                reasons = [
                    reason.strip()
                    for reason in str(supplier["risk_reasons"]).split(";")
                    if reason.strip()
                ]
                if reasons:
                    for reason in reasons:
                        st.write(
                            "- " + REASON_DESCRIPTIONS.get(
                                reason, reason.replace("_", " ").capitalize()
                            )
                        )
                else:
                    st.write("No evaluation flags recorded for this supplier.")

    st.divider()
    st.subheader("3. Delivery & Historical Reliability")
    st.write(
        "Quoted lead times are compared separately from historical delivery "
        "reliability; faster does not necessarily mean eligible."
    )
    if delivery_df.empty:
        st.info("No delivery comparisons are available.")
    else:
        st.dataframe(
            delivery_df[[
                "requisition_id", "quotation_count", "fastest_lead_time_days",
                "slowest_lead_time_days", "average_lead_time_days",
                "average_reliability_score",
            ]],
            hide_index=True, use_container_width=True,
        )
        st.bar_chart(
            delivery_df.set_index("requisition_id")[[
                "fastest_lead_time_days", "slowest_lead_time_days",
                "average_lead_time_days",
            ]]
        )
        st.caption(
            "Reliability scores derive from synthetic historical records and "
            "have not been independently verified."
        )

    st.divider()
    st.subheader("4. Procurement Bottlenecks")
    st.write(
        "Identify requisitions with no analytically eligible quotations and "
        "those requiring further supplier review."
    )
    if bottleneck_df.empty:
        st.info("No requisition bottleneck records are available.")
    else:
        st.dataframe(
            bottleneck_df[[
                "requisition_id", "total_quotations", "blocked_quotations",
                "review_required_quotations", "eligible_for_analysis",
                "bottleneck_status", "requires_human_review",
            ]],
            hide_index=True, use_container_width=True,
        )
        st.bar_chart(
            bottleneck_df.set_index("requisition_id")[[
                "blocked_quotations", "review_required_quotations",
                "eligible_for_analysis",
            ]]
        )

    st.divider()
    st.subheader("Procurement Governance")
    governance = insights["governance"]
    st.write(f"**Decision mode:** {governance['decision_mode']}")
    st.write(
        f"**Evidence classification:** {governance['evidence_classification']}"
    )
    st.write(f"**Decision timestamp:** {governance['decision_timestamp']}")
    st.write(f"**Purchasing authorization:** {governance['authorization_status']}")
    st.warning(
        "No quotation is automatically recommended for purchase, and this "
        "insights page cannot authorize or execute procurement transactions."
    )



def show_logistics_intelligence():
    """Read-only historical delivery performance; simulation data only."""
    st.divider()
    st.header("Logistics Intelligence")
    st.caption(
        "Supplier delivery punctuality, delays, and data-quality checks "
        "calculated from historical PostgreSQL records."
    )
    st.info(
        "Delivery records are synthetic and unverified. Historical performance "
        "is descriptive, not a forecast or purchasing authorization."
    )

    try:
        delivery_rows = load_logistics_delivery_performance()
    except Exception as error:
        st.error("Unable to load supplier delivery performance.")
        st.exception(error)
        return

    if not delivery_rows:
        st.info("No supplier delivery records are available.")
        return

    delivery_df = pd.DataFrame(delivery_rows)
    supplier_names = (
        df[["supplier_id", "supplier_name"]]
        .drop_duplicates(subset=["supplier_id"])
    )
    delivery_df = delivery_df.merge(
        supplier_names,
        on="supplier_id",
        how="left",
        validate="one_to_one",
    )
    delivery_df["supplier_name"] = delivery_df["supplier_name"].fillna(
        delivery_df["supplier_id"]
    )
    delivery_df["supplier_label"] = (
        delivery_df["supplier_name"] + " (" + delivery_df["supplier_id"] + ")"
    )

    completed = int(delivery_df["completed_deliveries"].sum())
    on_time = int(delivery_df["on_time_deliveries"].sum())
    late = int(delivery_df["late_deliveries"].sum())
    mismatches = int(delivery_df["on_time_flag_mismatches"].sum())
    overall_rate = (on_time / completed * 100) if completed else None

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Completed Deliveries", f"{completed:,}")
    kpi2.metric(
        "Overall On-Time Rate",
        f"{overall_rate:.2f}%" if overall_rate is not None else "N/A",
    )
    kpi3.metric("Late Deliveries", f"{late:,}")
    kpi4.metric("On-Time Flag Mismatches", f"{mismatches:,}")
    st.caption(
        "Overall on-time rate is weighted by completed deliveries. "
        "Early arrivals count as on time; delays are calendar days late. "
        "Only completed deliveries with both dates enter performance calculations."
    )

    st.divider()
    st.subheader("Supplier Delivery Performance")
    min_deliveries = st.slider(
        "Minimum completed deliveries for comparison",
        min_value=0,
        max_value=max(0, int(delivery_df["completed_deliveries"].max())),
        value=0,
        key="logistics_min_deliveries",
    )
    visible_df = delivery_df.loc[
        delivery_df["completed_deliveries"] >= min_deliveries
    ].copy()
    if visible_df.empty:
        st.info("No suppliers meet the selected delivery count threshold.")
    else:
        visible_df = visible_df.sort_values(
            ["on_time_delivery_rate_pct", "completed_deliveries"],
            ascending=[False, False],
            na_position="last",
        )
        st.dataframe(
            visible_df[[
                "supplier_label", "total_delivery_records",
                "completed_deliveries", "on_time_deliveries",
                "late_deliveries", "on_time_delivery_rate_pct",
                "average_delay_days", "maximum_delay_days",
                "on_time_flag_mismatches",
            ]],
            hide_index=True,
            use_container_width=True,
            column_config={
                "supplier_label": "Supplier",
                "total_delivery_records": "Total Records",
                "completed_deliveries": "Completed",
                "on_time_deliveries": "On Time",
                "late_deliveries": "Late",
                "on_time_delivery_rate_pct": st.column_config.NumberColumn(
                    "On-Time Rate", format="%.2f%%"
                ),
                "average_delay_days": st.column_config.NumberColumn(
                    "Average Delay (Days)", format="%.2f"
                ),
                "maximum_delay_days": "Max Delay (Days)",
                "on_time_flag_mismatches": "Flag Mismatches",
            },
        )

        st.subheader("On-Time Delivery Rate by Supplier")
        st.bar_chart(
            visible_df.set_index("supplier_label")[["on_time_delivery_rate_pct"]]
        )
        st.caption(
            "Percentages should be interpreted alongside delivery counts; "
            "small samples can produce misleadingly high rates."
        )

        st.subheader("Delivery Delay Comparison")
        st.bar_chart(
            visible_df.set_index("supplier_label")[[
                "average_delay_days", "maximum_delay_days"
            ]]
        )

    st.divider()
    st.subheader("Delivery Data Quality")
    missing_or_incomplete = int(
        (delivery_df["total_delivery_records"] - delivery_df["completed_deliveries"]).sum()
    )
    st.write(
        f"**Records excluded from completed-delivery metrics:** "
        f"{missing_or_incomplete:,}"
    )
    st.write(f"**Stored on-time flag disagreements:** {mismatches:,}")
    if mismatches:
        st.warning(
            "Some stored on-time flags disagree with the calculated dates. "
            "Review the underlying synthetic records."
        )
    else:
        st.success("No stored on-time flag disagreements were detected in completed records.")
    st.caption(
        "Excluded records include non-completed deliveries and completed "
        "deliveries missing a planned or actual date; these cases are not "
        "separately classified in this version."
    )

    st.divider()
    st.subheader("Logistics Governance")
    st.write("**Evidence classification:** SYNTHETIC_UNVERIFIED")
    st.write("**Purchasing authorization:** NOT_AUTHORIZED")
    st.warning(
        "This section provides read-only historical analytics. It does not "
        "track live shipments, predict arrival dates, or authorize purchases."
    )


def show_shipment_tracking():
    """Read-only shipment monitoring and chronological event history."""
    st.divider()
    st.header("Shipment Tracking")
    st.caption(
        "Operational shipment monitoring, carrier performance, and tracking "
        "milestones from synthetic PostgreSQL records."
    )
    st.info(
        "SIMULATION ONLY — Shipment movements and carrier names are fictional. "
        "No real transport booking, dispatch, or purchasing authorization occurs here."
    )

    refresh_col, note_col = st.columns([1, 3])
    with refresh_col:
        if st.button("Refresh shipment data", key="shipment_refresh"):
            load_shipment_monitoring.clear()
            load_shipment_tracking_records.clear()
            load_tracking_events.clear()
            st.rerun()
    with note_col:
        st.caption("Refresh after new simulated tracking events are recorded.")

    try:
        monitoring = load_shipment_monitoring()
        shipments = load_shipment_tracking_records()
    except Exception as error:
        st.error("Unable to load shipment tracking data.")
        st.exception(error)
        return

    kpis = monitoring["kpis"]
    if not shipments:
        st.info("No simulated shipments have been created yet.")
        return

    st.subheader("Shipment Operations Overview")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Shipments", kpis["total_shipments"])
    k2.metric("Active Shipments", kpis["active_shipments"])
    k3.metric("Overdue Shipments", kpis["overdue_shipments"])
    k4.metric("Exceptions", kpis["exception_shipments"])

    k5, k6, k7, k8 = st.columns(4)
    k5.metric("Delivered", kpis["delivered_shipments"])
    k6.metric("Operational Alerts", kpis["operational_alerts"])
    k7.metric("Data Quality Issues", kpis["data_quality_issues"])
    completed = kpis["evaluated_deliveries"]
    k8.metric(
        "On-Time Delivery Rate",
        f"{kpis['on_time_delivery_rate_pct']:.2f}%" if completed else "N/A",
    )
    st.caption(
        "On-time delivery rate is N/A until at least one delivered shipment "
        "has both estimated and actual delivery dates."
    )

    st.divider()
    st.subheader("Shipment Status Distribution")
    status_df = pd.DataFrame(
        [
            {"Status": status, "Shipments": count}
            for status, count in sorted(monitoring["status_distribution"].items())
        ]
    )
    if not status_df.empty:
        st.bar_chart(status_df.set_index("Status")["Shipments"])

    st.divider()
    st.subheader("Shipment Register")
    shipments_df = pd.DataFrame(shipments)
    status_options = ["All"] + sorted(
        shipments_df["shipment_status"].dropna().unique().tolist()
    )
    selected_status = st.selectbox(
        "Filter shipments by status", status_options, key="shipment_status_filter"
    )
    filtered_shipments = shipments_df if selected_status == "All" else (
        shipments_df[shipments_df["shipment_status"] == selected_status]
    )
    st.dataframe(
        filtered_shipments[[
            "shipment_id", "supplier_id", "tracking_number", "carrier_name",
            "transport_mode", "origin_location", "destination_location",
            "shipment_status", "dispatch_date", "estimated_delivery_date",
            "actual_delivery_date",
        ]],
        hide_index=True,
        use_container_width=True,
    )

    st.divider()
    st.subheader("Carrier Performance")
    carrier_df = pd.DataFrame(monitoring["carrier_performance"])
    if carrier_df.empty:
        st.info("No carrier performance records available.")
    else:
        carrier_display = carrier_df.copy()
        carrier_display["on_time_rate_pct"] = carrier_display.apply(
            lambda row: (
                f"{row['on_time_rate_pct']:.2f}%"
                if row["evaluated_deliveries"] else "N/A"
            ),
            axis=1,
        )
        st.dataframe(
            carrier_display[[
                "carrier_name", "total_shipments", "active_shipments",
                "completed_deliveries", "evaluated_deliveries",
                "on_time_rate_pct", "average_delay_days", "exception_shipments",
            ]],
            hide_index=True,
            use_container_width=True,
        )
        st.caption(
            "Carrier metrics are descriptive and synthetic. Compare on-time "
            "rates only where evaluated deliveries are available."
        )

    st.divider()
    st.subheader("Overdue Shipments & Operational Alerts")
    overdue_df = pd.DataFrame(monitoring["overdue_shipments"])
    if overdue_df.empty:
        st.success("No overdue open shipments at the monitoring date.")
    else:
        st.dataframe(overdue_df, hide_index=True, use_container_width=True)

    alerts_df = pd.DataFrame(monitoring["alerts"])
    if alerts_df.empty:
        st.info("No operational alerts are currently recorded.")
    else:
        st.dataframe(alerts_df, hide_index=True, use_container_width=True)

    st.divider()
    st.subheader("Tracking History")
    shipment_ids = sorted(shipments_df["shipment_id"].dropna().tolist())
    selected_shipment = st.selectbox(
        "Select shipment", shipment_ids, key="shipment_history_selection"
    )
    selected_row = shipments_df.loc[
        shipments_df["shipment_id"] == selected_shipment
    ].iloc[0]
    st.write(
        f"**Carrier:** {selected_row['carrier_name']}  |  "
        f"**Status:** {selected_row['shipment_status']}  |  "
        f"**Estimated delivery:** {selected_row['estimated_delivery_date']}"
    )
    try:
        events = load_tracking_events(selected_shipment)
    except Exception as error:
        st.error("Unable to load shipment tracking history.")
        st.exception(error)
        events = []
    if events:
        events_df = pd.DataFrame(events)
        st.dataframe(
            events_df[[
                "event_timestamp", "event_type", "event_location",
                "event_description", "recorded_by", "simulation_mode",
            ]],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("No tracking events are recorded for this shipment.")

    st.divider()
    st.subheader("Shipment Data Quality & Governance")
    quality_df = pd.DataFrame(monitoring["data_quality_issues"])
    if quality_df.empty:
        st.success("No shipment data-quality issues detected by the monitoring engine.")
    else:
        st.warning("Shipment data-quality issues require review.")
        st.dataframe(quality_df, hide_index=True, use_container_width=True)
    for field, value in monitoring["governance"].items():
        st.write(f"**{field.replace('_', ' ').title()}:** {value}")
    st.caption(
        "Shipment monitoring is separate from the 177 synthetic historical "
        "supplier delivery records shown under Logistics Intelligence."
    )


@st.cache_data(show_spinner="Calculating logistics risk intelligence...", ttl=60)
def load_logistics_risk_intelligence():
    """Read-only, explainable heuristic risk assessments."""
    return generate_logistics_risk_intelligence()


def show_logistics_risk_intelligence():
    """Present simulated shipment risk scores without changing operational data."""
    st.divider()
    st.header("Logistics Risk Intelligence")
    st.caption(
        "Explainable, rules-based shipment risk indicators using estimated "
        "delivery dates, shipment statuses, and unresolved exceptions."
    )
    st.warning(
        "SIMULATION ONLY — Risk scores are heuristic indicators, not "
        "validated probabilities or predictions. Evidence is synthetic "
        "and unverified; no operational actions or purchases are authorized."
    )

    if st.button("Refresh risk assessments", key="risk_refresh"):
        load_logistics_risk_intelligence.clear()
        st.rerun()

    try:
        report = load_logistics_risk_intelligence()
    except Exception as error:
        st.error("Unable to load logistics risk assessments.")
        st.exception(error)
        return

    assessments = report["shipments"]
    distribution = report["risk_distribution"]
    total = report["total_shipments"]

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Shipments Assessed", total)
    k2.metric("High Priority", report["high_priority_shipments"])
    k3.metric("Critical Risk", distribution["CRITICAL"])
    k4.metric("High Risk", distribution["HIGH"])
    st.caption(f"Assessment date: {report['assessment_date']} · Scores range from 0 to 100.")

    if not assessments:
        st.info("No shipments are available for risk assessment.")
        return

    st.divider()
    st.subheader("Risk Distribution")
    distribution_df = pd.DataFrame(
        [
            {"Risk Level": level, "Shipments": distribution[level]}
            for level in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
        ]
    )
    st.bar_chart(distribution_df.set_index("Risk Level"))

    st.divider()
    st.subheader("Shipment Risk Register")
    risk_filter = st.selectbox(
        "Filter by risk level",
        ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"],
        key="risk_level_filter",
    )
    filtered = [
        row for row in assessments
        if risk_filter == "All" or row["risk_level"] == risk_filter
    ]
    if not filtered:
        st.info("No shipments match the selected risk level.")
    else:
        register = pd.DataFrame(filtered)
        st.dataframe(
            register[[
                "shipment_id", "shipment_status", "estimated_delivery_date",
                "days_overdue", "unresolved_exception_count",
                "highest_exception_severity", "risk_score", "risk_level",
            ]],
            hide_index=True,
            use_container_width=True,
            column_config={
                "shipment_id": "Shipment",
                "shipment_status": "Shipment Status",
                "estimated_delivery_date": "Estimated Delivery",
                "days_overdue": "Days Overdue",
                "unresolved_exception_count": "Open Exceptions",
                "highest_exception_severity": "Highest Severity",
                "risk_score": st.column_config.ProgressColumn(
                    "Risk Score", min_value=0, max_value=100, format="%d"
                ),
                "risk_level": "Risk Level",
            },
        )

    st.divider()
    st.subheader("Explainable Risk Assessment")
    by_id = {row["shipment_id"]: row for row in assessments}
    selected_id = st.selectbox(
        "Select shipment to inspect",
        [row["shipment_id"] for row in assessments],
        key="risk_selected_shipment",
    )
    selected = by_id[selected_id]
    st.write(
        f"**Risk:** {selected['risk_level']} "
        f"({selected['risk_score']}/100)  |  "
        f"**Shipment status:** {selected['shipment_status']}"
    )
    if selected["risk_factors"]:
        st.dataframe(
            pd.DataFrame(selected["risk_factors"])[
                ["factor", "points", "description"]
            ],
            hide_index=True,
            use_container_width=True,
        )
        st.caption(
            "Displayed factor points may sum above 100; the final "
            "risk score is capped at 100."
        )
    else:
        st.success("No risk factors triggered by the current scoring rules.")

    st.divider()
    st.subheader("Scoring Methodology & Governance")
    st.write(
        "Overdue shipments: 1–2 days +20; 3–6 days +35; 7+ days +45. "
        "Shipment status EXCEPTION: +25. Highest unresolved exception: "
        "LOW +10, MEDIUM +20, HIGH +35, CRITICAL +50."
    )
    st.write(
        "**Risk bands:** LOW 0–19 · MEDIUM 20–39 · "
        "HIGH 40–69 · CRITICAL 70–100."
    )
    st.caption(
        "Only the highest-severity OPEN or INVESTIGATING exception contributes "
        "to active exception risk. RESOLVED and CLOSED exceptions do not. "
        "Scores are descriptive heuristics, not probability estimates."
    )
    for field, value in report["governance"].items():
        st.write(f"**{field.replace('_', ' ').title()}:** {value}")
    st.caption(
        "Read-only analytics. This page does not modify shipment or exception "
        "records, contact carriers, or authorize purchasing."
    )


if page == "Procurement Overview":
    show_overview()
elif page == "Supplier Comparison":
    show_supplier_comparison()
elif page == "Procurement Insights":
    show_procurement_insights()
elif page == "Logistics Intelligence":
    show_logistics_intelligence()
elif page == "Shipment Tracking":
    show_shipment_tracking()
elif page == "Shipment Exception Management":
    show_shipment_exception_management()
elif page == "Logistics Risk Intelligence":
    show_logistics_risk_intelligence()
elif page == "Logistics Risk Scenario Analysis":
    from src.dashboard.logistics_risk_scenario_page import (
        render_logistics_risk_scenario_page,
    )
    render_logistics_risk_scenario_page()
elif page == "Decision & Audit Trail":
    show_decision_audit()
else:
    show_analyst_workspace()
