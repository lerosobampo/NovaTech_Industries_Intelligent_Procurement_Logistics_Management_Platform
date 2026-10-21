
"""
NovaTech Industries
Logistics Risk Scenario Analysis — Streamlit Dashboard V1

Read-only shipment retrieval from PostgreSQL.
Hypothetical risk calculations occur in memory only.

Synthetic and unverified data.
No purchasing, dispatch, or operational authorization.
"""

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from src.database.connection import get_connection
from src.analysis.logistics_risk_scenarios import (
    analyze_risk_scenario,
    ScenarioValidationError,
)


SHIPMENT_STATUSES = [
    "CREATED",
    "DISPATCHED",
    "IN_TRANSIT",
    "EXCEPTION",
    "DELIVERED",
    "CANCELLED",
]

SEVERITIES = [
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
]


@st.cache_data(ttl=60)
def load_scenario_shipments():
    """Retrieve shipment records without modifying the database."""

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

            rows = cur.fetchall()

    return [
        {
            "shipment_id": row[0],
            "shipment_status": row[1],
            "estimated_delivery_date": row[2],
        }
        for row in rows
    ]


@st.cache_data(ttl=60)
def load_scenario_exceptions(shipment_id):
    """Retrieve unresolved exceptions for a selected shipment."""

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    shipment_id,
                    exception_status,
                    severity
                FROM logistics.shipment_exceptions
                WHERE shipment_id = %s
                  AND exception_status IN (
                      'OPEN',
                      'INVESTIGATING'
                  )
                ORDER BY exception_id
                """,
                (shipment_id,),
            )

            rows = cur.fetchall()

    return [
        {
            "shipment_id": row[0],
            "exception_status": row[1],
            "severity": row[2],
        }
        for row in rows
    ]


def render_risk_factors(title, factors):
    """Display an explanatory table of risk contributions."""

    st.markdown(f"**{title}**")

    if not factors:
        st.info("No active risk factors.")
        return

    factor_rows = [
        {
            "Risk factor": item["factor"],
            "Points": item["points"],
            "Explanation": item["description"],
        }
        for item in factors
    ]

    st.dataframe(
        pd.DataFrame(factor_rows),
        use_container_width=True,
        hide_index=True,
    )


def render_logistics_risk_scenario_page():
    """Render the independent Logistics Risk Scenario Analysis page."""

    st.title("Logistics Risk Scenario Analysis")

    st.caption(
        "NovaTech Industries | Synthetic demonstration data | "
        "Read-only what-if analysis"
    )

    st.warning(
        "SIMULATION ONLY — Scenario results are hypothetical "
        "heuristic assessments, not predictions or operational "
        "authorizations. No database records are modified."
    )

    try:
        shipments = load_scenario_shipments()
    except Exception as error:
        st.error(
            "Unable to load shipment records from PostgreSQL."
        )
        st.caption(f"Technical details: {error}")
        return

    if not shipments:
        st.info(
            "No shipments are available for scenario analysis."
        )
        return

    shipment_lookup = {
        shipment["shipment_id"]: shipment
        for shipment in shipments
    }

    selected_id = st.selectbox(
        "Select shipment",
        options=list(shipment_lookup),
        key="scenario_selected_shipment",
    )

    shipment = shipment_lookup[selected_id]

    try:
        exceptions = load_scenario_exceptions(selected_id)
    except Exception as error:
        st.error(
            "Unable to load unresolved shipment exceptions."
        )
        st.caption(f"Technical details: {error}")
        return

    st.subheader("Current Shipment Information")

    info_col1, info_col2, info_col3 = st.columns(3)

    info_col1.metric(
        "Shipment",
        shipment["shipment_id"],
    )

    info_col2.metric(
        "Current status",
        shipment["shipment_status"],
    )

    original_delivery = shipment["estimated_delivery_date"]

    info_col3.metric(
        "Estimated delivery",
        str(original_delivery)
        if original_delivery is not None
        else "Not available",
    )

    st.caption(
        f"Currently unresolved exceptions: {len(exceptions)}"
    )

    st.divider()

    st.subheader("Configure What-If Scenario")

    st.write(
        "Modify hypothetical shipment conditions below. "
        "These selections do not update PostgreSQL."
    )

    scenario_changes = {}

    change_status = st.checkbox(
        "Simulate a different shipment status",
        key="scenario_change_status",
    )

    if change_status:
        new_status = st.selectbox(
            "Hypothetical shipment status",
            options=SHIPMENT_STATUSES,
            index=SHIPMENT_STATUSES.index(
                shipment["shipment_status"]
            ),
            key="scenario_new_status",
        )

        scenario_changes["shipment_status"] = new_status

    change_delivery = st.checkbox(
        "Simulate a different estimated delivery date",
        key="scenario_change_delivery",
    )

    if change_delivery:
        initial_date = (
            original_delivery
            if original_delivery is not None
            else date.today() + timedelta(days=7)
        )

        new_delivery = st.date_input(
            "Hypothetical estimated delivery date",
            value=initial_date,
            key="scenario_new_delivery",
        )

        scenario_changes[
            "estimated_delivery_date"
        ] = new_delivery

    add_exception = st.checkbox(
        "Simulate a new unresolved exception",
        key="scenario_add_exception",
    )

    if add_exception:
        new_severity = st.selectbox(
            "Hypothetical exception severity",
            options=SEVERITIES,
            index=2,
            key="scenario_new_severity",
        )

        scenario_changes[
            "new_exception_severity"
        ] = new_severity

    override_severity = st.checkbox(
        "Simulate changing existing unresolved "
        "exception severities",
        disabled=not bool(exceptions),
        key="scenario_override_severity",
    )

    if override_severity and exceptions:
        severity_override = st.selectbox(
            "Hypothetical severity for existing "
            "unresolved exceptions",
            options=SEVERITIES,
            index=2,
            key="scenario_override_value",
        )

        scenario_changes[
            "override_exception_severity"
        ] = severity_override

    st.divider()

    run_analysis = st.button(
        "Run Scenario Analysis",
        type="primary",
        use_container_width=True,
    )

    if not run_analysis:
        st.info(
            "Configure a scenario and select "
            "'Run Scenario Analysis' to compare risks."
        )
        return

    try:
        result = analyze_risk_scenario(
            shipment=shipment,
            exceptions=exceptions,
            changes=scenario_changes,
            as_of_date=date.today(),
        )
    except ScenarioValidationError as error:
        st.error(f"Invalid scenario configuration: {error}")
        return
    except Exception:
        st.error(
            "Scenario analysis could not be completed."
        )
        return

    baseline = result["baseline"]
    scenario = result["scenario"]

    st.subheader("Baseline vs. Scenario Risk")

    baseline_col, scenario_col, delta_col = st.columns(3)

    baseline_col.metric(
        "Baseline risk score",
        baseline["risk_score"],
    )

    scenario_col.metric(
        "Scenario risk score",
        scenario["risk_score"],
    )

    delta_col.metric(
        "Risk score change",
        result["score_change"],
        delta=result["score_change"],
        delta_color="inverse",
    )

    comparison = pd.DataFrame([
        {
            "Assessment": "Baseline",
            "Risk score": baseline["risk_score"],
            "Risk level": baseline["risk_level"],
            "Days overdue": baseline["days_overdue"],
            "Unresolved exceptions":
                baseline["unresolved_exception_count"],
        },
        {
            "Assessment": "What-if scenario",
            "Risk score": scenario["risk_score"],
            "Risk level": scenario["risk_level"],
            "Days overdue": scenario["days_overdue"],
            "Unresolved exceptions":
                scenario["unresolved_exception_count"],
        },
    ])

    st.dataframe(
        comparison,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown(
        f"**Risk direction:** {result['risk_direction']}"
    )

    st.subheader("Risk Factor Breakdown")

    factor_col1, factor_col2 = st.columns(2)

    with factor_col1:
        render_risk_factors(
            "Baseline factors",
            baseline["risk_factors"],
        )

    with factor_col2:
        render_risk_factors(
            "Scenario factors",
            scenario["risk_factors"],
        )

    st.divider()

    st.subheader("Simulation Governance")

    governance = result["governance"]

    st.caption(
        f"Assessment date: {result['assessment_date']} | "
        f"Model: {governance['risk_model']}"
    )

    st.write(
        f"**Evidence classification:** "
        f"{governance['evidence_classification']}"
    )

    st.write(
        f"**Authorization:** "
        f"{governance['authorization_status']}"
    )

    st.write(
        f"**Scenario mode:** "
        f"{governance['scenario_mode']}"
    )

    st.write(
        f"**Database modifications:** "
        f"{governance['database_modifications']}"
    )

    st.write(
        f"**Forecast status:** "
        f"{governance['forecast_status']}"
    )


if __name__ == "__main__":
    render_logistics_risk_scenario_page()
