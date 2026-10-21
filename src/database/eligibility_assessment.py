
from datetime import date

from src.database.supplier_queries import get_product_by_id

from src.database.eligibility_queries import (
    get_supplier_status_at_date,
    get_supplier_compliance_at_date,
    get_supplier_compliance_record_at_date,
)

from src.database.inventory_queries import get_inventory_at_date


def assess_supplier_eligibility(
    supplier_id,
    product_id,
    category,
    requested_quantity,
    as_of_date,
):
    """
    Assess supplier eligibility using historical synthetic data.

    This is a simulation only.
    It does not authorize purchasing.
    """

    evaluation_date = date.fromisoformat(str(as_of_date))

    # --------------------------------------------------
    # 1. Validate product and category
    # --------------------------------------------------

    product = get_product_by_id(product_id)

    if product is None:
        return {
            "supplier_id": supplier_id,
            "product_id": product_id,
            "category": category,
            "requested_quantity": requested_quantity,
            "evaluation_date": as_of_date,
            "assessment": "INSUFFICIENT_EVIDENCE",
            "checks": {"product_category_valid": None},
            "evidence_sources": {},
            "compliance_reasons": [],
            "decision_mode": "SIMULATION",
            "authorization_status": "NOT_AUTHORIZED",
            "reason": "Product not found in the product catalog",
        }

    if product["category"] != category:
        return {
            "supplier_id": supplier_id,
            "product_id": product_id,
            "category": category,
            "requested_quantity": requested_quantity,
            "evaluation_date": as_of_date,
            "assessment": "INELIGIBLE",
            "checks": {"product_category_valid": False},
            "evidence_sources": {},
            "compliance_reasons": [],
            "decision_mode": "SIMULATION",
            "authorization_status": "NOT_AUTHORIZED",
            "reason": (
                f"Category mismatch: expected {product['category']}, "
                f"received {category}"
            ),
        }

    # --------------------------------------------------
    # 2. Retrieve historical supplier information
    # --------------------------------------------------

    status = get_supplier_status_at_date(
        supplier_id,
        as_of_date,
    )

    compliance = get_supplier_compliance_at_date(
        supplier_id,
        category,
        as_of_date,
    )

    compliance_record = get_supplier_compliance_record_at_date(
        supplier_id,
        category,
        as_of_date,
    )

    inventory = get_inventory_at_date(
        supplier_id,
        product_id,
        as_of_date,
    )

    # --------------------------------------------------
    # 3. Evaluate historical compliance
    # --------------------------------------------------

    compliance_reasons = []

    if compliance_record is None:
        compliance_reasons.append(
            "CATEGORY_COMPLIANCE_HISTORY_MISSING"
        )

        category_approved = None

    else:
        approval_status = compliance_record[
            "approval_status"
        ]

        valid_until = compliance_record["valid_until"]

        expired = (
            valid_until is not None
            and valid_until < evaluation_date
        )

        if approval_status != "APPROVED":
            compliance_reasons.append(
                "CATEGORY_COMPLIANCE_NOT_APPROVED"
            )

        if expired:
            compliance_reasons.append(
                "CATEGORY_COMPLIANCE_EXPIRED"
            )

        category_approved = (
            approval_status == "APPROVED"
            and not expired
            and compliance is not None
        )

    # --------------------------------------------------
    # 4. Evaluate supplier eligibility
    # --------------------------------------------------

    checks = {
        "supplier_active": (
            None if status is None
            else status["status"] == "ACTIVE"
        ),
        "category_approved": category_approved,
        "inventory_sufficient": (
            None if inventory is None
            else inventory["available_quantity"]
            >= requested_quantity
        ),
        "minimum_order_met": (
            None if inventory is None
            else requested_quantity
            >= inventory["minimum_order_quantity"]
        ),
    }

    # --------------------------------------------------
    # 5. Determine assessment
    # --------------------------------------------------

    if False in checks.values():
        assessment = "INELIGIBLE"

    elif None in checks.values():
        assessment = "INSUFFICIENT_EVIDENCE"

    else:
        assessment = "SIMULATED_ELIGIBLE"

    # --------------------------------------------------
    # 6. Return simulated assessment
    # --------------------------------------------------

    return {
        "supplier_id": supplier_id,
        "product_id": product_id,
        "category": category,
        "requested_quantity": requested_quantity,
        "evaluation_date": as_of_date,
        "assessment": assessment,
        "checks": checks,
        "compliance_reasons": compliance_reasons,
        "evidence_sources": {
            "status": (
                status["evidence_source"]
                if status else None
            ),
            "compliance": (
                compliance_record["evidence_source"]
                if compliance_record else None
            ),
            "inventory": (
                inventory["evidence_source"]
                if inventory else None
            ),
        },
        "decision_mode": "SIMULATION",
        "authorization_status": "NOT_AUTHORIZED",
    }
