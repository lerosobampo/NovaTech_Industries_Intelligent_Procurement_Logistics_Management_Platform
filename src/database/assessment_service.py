
"""
NovaTech Industries
Procurement Analyst Assessment Service — V1

Validates and saves simulated analyst assessments.

Safeguards:
- Quotations must belong to the selected requisition.
- Blocked quotations cannot be recommended.
- Only supported assessment statuses are accepted.
- All assessments remain simulations.
- Purchasing authorization is never granted.
"""

from src.database.connection import get_connection
from src.analysis.evaluate_suppliers_v5 import evaluate


ALLOWED_ASSESSMENT_STATUSES = {
    "REVIEW_REQUIRED",
    "NOT_RECOMMENDED",
}


def save_analyst_assessment(
    requisition_id,
    quotation_id,
    analyst_name,
    assessment_status,
    assessment_notes,
):
    """
    Validate and save a simulated procurement assessment.

    Returns the newly created assessment ID.

    Does not modify procurement decisions, approvals,
    audit records, or purchasing authorization.
    """

    # --------------------------------------------------
    # 1. Validate input
    # --------------------------------------------------

    requisition_id = requisition_id.strip()
    quotation_id = quotation_id.strip()
    analyst_name = analyst_name.strip()
    assessment_status = assessment_status.strip().upper()
    assessment_notes = assessment_notes.strip()

    if not requisition_id:
        raise ValueError("Requisition ID is required.")

    if not quotation_id:
        raise ValueError("Quotation ID is required.")

    if not analyst_name:
        raise ValueError("Analyst name is required.")

    if not assessment_notes:
        raise ValueError("Assessment notes are required.")

    if assessment_status not in ALLOWED_ASSESSMENT_STATUSES:
        raise ValueError(
            f"Invalid assessment status: {assessment_status}"
        )

    # --------------------------------------------------
    # 2. Retrieve current evaluation results
    # --------------------------------------------------

    evaluation_results = evaluate()["evaluations"]

    matching_evaluations = [
        row
        for row in evaluation_results
        if (
            row["requisition_id"] == requisition_id
            and row["quotation_id"] == quotation_id
        )
    ]

    if len(matching_evaluations) != 1:
        raise ValueError(
            "Quotation not found for the selected requisition."
        )

    evaluation = matching_evaluations[0]

    evaluation_status = evaluation["evaluation_status"]

    # --------------------------------------------------
    # 3. Enforce eligibility restrictions
    # --------------------------------------------------

    if evaluation_status == "BLOCKED":

        if assessment_status != "NOT_RECOMMENDED":
            raise ValueError(
                "Blocked quotations can only receive "
                "NOT_RECOMMENDED assessments."
            )

    elif evaluation_status not in {
        "REVIEW_REQUIRED",
        "ELIGIBLE_FOR_ANALYSIS",
    }:
        raise ValueError(
            f"Unsupported evaluation status: {evaluation_status}"
        )

    # --------------------------------------------------
    # 4. Save assessment to PostgreSQL
    # --------------------------------------------------

    with get_connection() as conn:
        with conn.cursor() as cur:

            # Verify the quotation-requisition relationship
            # again against PostgreSQL.
            cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM procurement.quotations
                    WHERE quotation_id = %s
                      AND requisition_id = %s
                )
                """,
                (quotation_id, requisition_id),
            )

            if not cur.fetchone()[0]:
                raise ValueError(
                    "Quotation-requisition relationship "
                    "could not be verified."
                )

            cur.execute(
                """
                INSERT INTO procurement.analyst_assessments (
                    requisition_id,
                    quotation_id,
                    analyst_name,
                    assessment_status,
                    assessment_notes,
                    decision_mode,
                    authorization_status
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    'SIMULATION',
                    'NOT_AUTHORIZED'
                )
                RETURNING assessment_id
                """,
                (
                    requisition_id,
                    quotation_id,
                    analyst_name,
                    assessment_status,
                    assessment_notes,
                ),
            )

            assessment_id = cur.fetchone()[0]

        conn.commit()

    return assessment_id
