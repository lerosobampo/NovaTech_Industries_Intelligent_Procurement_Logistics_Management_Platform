
"""
NovaTech Industries
Supplier Evaluation Engine V5

PostgreSQL-backed supplier evaluation.

Features:
- PostgreSQL data loading
- Primary-key validation
- Requisition evaluation cutoffs
- Quotation cost calculations
- Historical supplier performance
- Supplier eligibility and blocking rules
- Weighted supplier scoring
- Supplier ranking

Historical evidence is synthetic and unverified.
This engine does not authorize purchasing.
"""

from collections import Counter, defaultdict
from datetime import timedelta
from decimal import Decimal

from src.database.evaluation_data_loader import (
    load_evaluation_data,
)

from src.analysis.evaluate_suppliers_v4 import (
    WEIGHTS,
    index,
    day,
    number,
    performance_at,
    history_at,
)


def evaluate():
    """
    Evaluate PostgreSQL-backed supplier quotations
    using the established V4 business rules.

    Purchasing authorization is never granted
    by this evaluation engine.
    """

    # --------------------------------------------------
    # 1. Load PostgreSQL datasets
    # --------------------------------------------------

    datasets = load_evaluation_data()

    # --------------------------------------------------
    # 2. Validate primary keys
    # --------------------------------------------------

    suppliers = index(
        datasets["suppliers"],
        ["supplier_id"],
        "suppliers",
    )

    products = index(
        datasets["products"],
        ["product_id"],
        "products",
    )

    requisitions = index(
        datasets["purchase_requisitions"],
        ["requisition_id"],
        "requisitions",
    )

    quotations = index(
        datasets["quotations"],
        ["quotation_id"],
        "quotations",
    )

    quotation_items = index(
        datasets["quotation_items"],
        ["quotation_id"],
        "quotation_items",
    )

    supplier_products = index(
        datasets["supplier_products"],
        ["supplier_id", "product_id"],
        "supplier_products",
    )

    deliveries = index(
        datasets["supplier_deliveries"],
        ["delivery_id"],
        "deliveries",
    )

    inspections = index(
        datasets["supplier_quality_inspections"],
        ["inspection_id"],
        "inspections",
    )

    print("V5 PostgreSQL data validation")
    print("-----------------------------")

    print("Suppliers:", len(suppliers))
    print("Products:", len(products))
    print("Requisitions:", len(requisitions))
    print("Quotations:", len(quotations))
    print("Quotation items:", len(quotation_items))

    print(
        "Supplier-product relationships:",
        len(supplier_products),
    )

    print("Deliveries:", len(deliveries))
    print("Quality inspections:", len(inspections))

    print()
    print("Database records loaded successfully.")

    # --------------------------------------------------
    # 3. Calculate requisition evaluation cutoffs
    # --------------------------------------------------

    cutoffs = {}

    for quotation in datasets["quotations"]:

        quotation_id = quotation["quotation_id"]
        requisition_id = quotation["requisition_id"]
        supplier_id = quotation["supplier_id"]

        if (
            (requisition_id,) not in requisitions
            or (quotation_id,) not in quotation_items
            or (supplier_id,) not in suppliers
        ):
            raise ValueError(
                f"{quotation_id}: missing foreign key"
            )

        issued = day(
            quotation["quotation_date"],
            f"{quotation_id}.quotation_date",
        )

        requested = day(
            requisitions[(requisition_id,)]["request_date"],
            f"{requisition_id}.request_date",
        )

        if issued >= requested:

            cutoffs[requisition_id] = max(
                cutoffs.get(requisition_id, issued),
                issued,
            )

    for (requisition_id,), requisition in requisitions.items():

        if requisition_id not in cutoffs:

            cutoffs[requisition_id] = day(
                requisition["request_date"],
                f"{requisition_id}.request_date",
            )

    print()
    print("V5 Evaluation Cutoffs")
    print("---------------------")

    for requisition_id in sorted(cutoffs):

        print(
            f"{requisition_id}: "
            f"{cutoffs[requisition_id].isoformat()}"
        )

    # --------------------------------------------------
    # 4. Calculate quotation costs
    # --------------------------------------------------

    quotation_costs = {}

    print()
    print("V5 Quotation Costs")
    print("------------------")

    for (quotation_id,), quotation in sorted(
        quotations.items()
    ):

        item = quotation_items[(quotation_id,)]

        quoted_quantity = number(
            item["quoted_quantity"],
            "quoted_quantity",
            positive=True,
        )

        unit_price = number(
            item["unit_price_eur"],
            "unit_price_eur",
        )

        total_cost = quoted_quantity * unit_price

        for field in (
            "freight_eur",
            "duties_eur",
            "other_fees_eur",
        ):

            total_cost += number(
                item[field],
                field,
            )

        if total_cost <= 0:

            raise ValueError(
                f"{quotation_id}: nonpositive total cost"
            )

        quotation_costs[quotation_id] = total_cost

        print(
            f"{quotation_id}: "
            f"EUR {total_cost:.2f}"
        )

    # --------------------------------------------------
    # 5. Calculate historical supplier performance
    # --------------------------------------------------

    supplier_performance = {}

    print()
    print("V5 Historical Supplier Performance")
    print("----------------------------------")

    for (quotation_id,), quotation in sorted(
        quotations.items()
    ):

        supplier_id = quotation["supplier_id"]
        requisition_id = quotation["requisition_id"]

        cutoff = cutoffs[requisition_id]

        performance = performance_at(
            supplier_id,
            cutoff,
            datasets["supplier_deliveries"],
            datasets["supplier_quality_inspections"],
        )

        supplier_performance[quotation_id] = performance

        quality = (
            f"{performance['quality_score']:.2f}"
            if performance["quality_score"] is not None
            else "N/A"
        )

        reliability = (
            f"{performance['reliability_score']:.2f}"
            if performance["reliability_score"] is not None
            else "N/A"
        )

        print(
            f"{quotation_id} | "
            f"{supplier_id} | "
            f"Quality={quality}% | "
            f"Reliability={reliability}% | "
            f"Inspected={performance['inspected_units']} | "
            f"Deliveries={performance['completed_deliveries']} | "
            f"Sufficient={performance['sufficient']}"
        )

    # --------------------------------------------------
    # 6. Evaluate supplier eligibility
    # --------------------------------------------------

    evaluations = []

    print()
    print("V5 Supplier Eligibility")
    print("-----------------------")

    for (quotation_id,), quotation in sorted(
        quotations.items()
    ):

        requisition_id = quotation["requisition_id"]
        supplier_id = quotation["supplier_id"]

        requisition = requisitions[(requisition_id,)]
        item = quotation_items[(quotation_id,)]

        product_id = requisition["product_id"]

        if (
            (product_id,) not in products
            or item["product_id"] != product_id
        ):

            raise ValueError(
                f"{quotation_id}: product mismatch"
            )

        category = products[(product_id,)]["category"]

        cutoff = cutoffs[requisition_id]

        issued = day(
            quotation["quotation_date"],
            f"{quotation_id}.quotation_date",
        )

        expiry = day(
            quotation["valid_until"],
            f"{quotation_id}.valid_until",
        )

        requested = day(
            requisition["request_date"],
            f"{requisition_id}.request_date",
        )

        needed = day(
            requisition["required_delivery_date"],
            f"{requisition_id}.required_delivery_date",
        )

        requested_quantity = number(
            requisition["requested_quantity"],
            "requested_quantity",
            True,
        )

        quoted_quantity = number(
            item["quoted_quantity"],
            "quoted_quantity",
            True,
        )

        lead_time = number(
            item["lead_time_days"],
            "lead_time_days",
            True,
        )

        blocked = []
        review = []

        # --------------------------------------------------
        # Quotation validation
        # --------------------------------------------------

        if issued < requested:

            blocked.append(
                "QUOTATION_PREDATES_REQUISITION"
            )

        if expiry < issued:

            blocked.append(
                "QUOTATION_EXPIRY_BEFORE_ISSUE"
            )

        if expiry < cutoff:

            blocked.append(
                "QUOTATION_EXPIRED_AT_CUTOFF"
            )

        if quotation["status"].strip().upper() != "RECEIVED":

            blocked.append(
                "INVALID_QUOTATION_STATUS"
            )

        if quoted_quantity < requested_quantity:

            blocked.append(
                "INSUFFICIENT_QUOTED_QUANTITY"
            )

        if issued + timedelta(days=int(lead_time)) > needed:

            blocked.append(
                "DELIVERY_AFTER_REQUIRED_DATE"
            )

        if (supplier_id, product_id) not in supplier_products:

            blocked.append(
                "SUPPLIER_PRODUCT_RELATIONSHIP_MISSING"
            )

        # --------------------------------------------------
        # Historical supplier status
        # --------------------------------------------------

        status_record, status_issue = history_at(
            [
                row
                for row in datasets["supplier_status_history"]
                if row["supplier_id"] == supplier_id
            ],
            cutoff,
            supplier_id,
            "SUPPLIER_STATUS",
        )

        # --------------------------------------------------
        # Historical category compliance
        # --------------------------------------------------

        compliance_record, compliance_issue = history_at(
            [
                row
                for row in datasets["supplier_compliance_history"]
                if (
                    row["supplier_id"] == supplier_id
                    and row["category"] == category
                )
            ],
            cutoff,
            (supplier_id, category),
            "CATEGORY_COMPLIANCE",
        )

        # --------------------------------------------------
        # Historical inventory
        # --------------------------------------------------

        inventory_record, inventory_issue = history_at(
            [
                row
                for row in datasets["supplier_inventory_history"]
                if (
                    row["supplier_id"] == supplier_id
                    and row["product_id"] == product_id
                )
            ],
            cutoff,
            (supplier_id, product_id),
            "INVENTORY",
        )

        # --------------------------------------------------
        # Record evidence limitations
        # --------------------------------------------------

        for record, issue in (
            (status_record, status_issue),
            (compliance_record, compliance_issue),
            (inventory_record, inventory_issue),
        ):

            if issue:
                review.append(issue)

        # --------------------------------------------------
        # Supplier status validation
        # --------------------------------------------------

        if status_record is not None:

            if status_record["status"].strip().upper() != "ACTIVE":

                blocked.append(
                    "INACTIVE_SUPPLIER"
                )

        # --------------------------------------------------
        # Category compliance validation
        # --------------------------------------------------

        if compliance_record is not None:

            if (
                compliance_record["approval_status"]
                .strip()
                .upper()
                != "APPROVED"
            ):

                blocked.append(
                    "CATEGORY_COMPLIANCE_NOT_APPROVED"
                )

            if day(
                compliance_record["valid_until"],
                "compliance.valid_until",
            ) < cutoff:

                blocked.append(
                    "CATEGORY_COMPLIANCE_EXPIRED"
                )

        # --------------------------------------------------
        # Inventory validation
        # --------------------------------------------------

        if inventory_record is not None:

            minimum_order = number(
                inventory_record["minimum_order_quantity"],
                "minimum_order_quantity",
                True,
            )

            available_stock = number(
                inventory_record["available_quantity"],
                "available_quantity",
            )

            if quoted_quantity < minimum_order:

                blocked.append(
                    "BELOW_MINIMUM_ORDER"
                )

            if quoted_quantity > available_stock:

                blocked.append(
                    "INSUFFICIENT_AVAILABLE_STOCK"
                )

        # --------------------------------------------------
        # Historical performance sufficiency
        # --------------------------------------------------

        performance = supplier_performance[quotation_id]

        if not performance["sufficient"]:

            review.append(
                "INSUFFICIENT_PERFORMANCE_HISTORY"
            )

        # --------------------------------------------------
        # Decision timestamp safeguard
        # --------------------------------------------------

        review.append(
            "DECISION_TIMESTAMP_NOT_VERIFIED"
        )

        # Preserve V4 reason ordering.
        reasons = list(dict.fromkeys(blocked + review))

        if blocked:

            evaluation_status = "BLOCKED"

        elif review:

            evaluation_status = "REVIEW_REQUIRED"

        else:

            evaluation_status = "ELIGIBLE_FOR_ANALYSIS"

        # --------------------------------------------------
        # Create evaluation record
        # --------------------------------------------------

        evaluation = {
            "quotation_id": quotation_id,
            "requisition_id": requisition_id,
            "supplier_id": supplier_id,
            "product_id": product_id,
            "category": category,
            "evaluation_as_of": cutoff.isoformat(),
            "cutoff_basis": "LATEST_QUOTATION_DATE_PROXY",
            "evidence_classification": "SYNTHETIC_UNVERIFIED",
            "total_cost_eur": (
                f"{quotation_costs[quotation_id]:.2f}"
            ),
            "lead_time_days": str(int(lead_time)),
            "inspected_units": str(
                performance["inspected_units"]
            ),
            "completed_deliveries": str(
                performance["completed_deliveries"]
            ),
            "quality_score": (
                f"{performance['quality_score']:.2f}"
                if performance["quality_score"] is not None
                else ""
            ),
            "reliability_score": (
                f"{performance['reliability_score']:.2f}"
                if performance["reliability_score"] is not None
                else ""
            ),
            "evaluation_status": evaluation_status,
            "reasons": ";".join(reasons),
            "cost_score": "",
            "delivery_score": "",
            "weighted_score": "",
            "recommendation_status": "NO_AUTOMATIC_APPROVAL",
        }

        evaluations.append(evaluation)

        print(
            f"{quotation_id} | "
            f"{supplier_id} | "
            f"{evaluation_status}"
        )

    # --------------------------------------------------
    # 7. Weighted supplier scoring and ranking
    # --------------------------------------------------

    eligible_groups = defaultdict(list)

    for evaluation in evaluations:

        if (
            evaluation["evaluation_status"]
            == "ELIGIBLE_FOR_ANALYSIS"
        ):

            eligible_groups[
                evaluation["requisition_id"]
            ].append(evaluation)

    for group in eligible_groups.values():

        min_cost = min(
            Decimal(row["total_cost_eur"])
            for row in group
        )

        min_lead = min(
            Decimal(row["lead_time_days"])
            for row in group
        )

        for row in group:

            cost_score = (
                Decimal("100")
                * min_cost
                / Decimal(row["total_cost_eur"])
            )

            delivery_score = (
                Decimal("100")
                * min_lead
                / Decimal(row["lead_time_days"])
            )

            quality_score = Decimal(
                row["quality_score"]
            )

            reliability_score = Decimal(
                row["reliability_score"]
            )

            weighted_score = (
                cost_score * WEIGHTS["cost"]
                + delivery_score * WEIGHTS["delivery"]
                + quality_score * WEIGHTS["quality"]
                + reliability_score * WEIGHTS["reliability"]
            )

            row["cost_score"] = (
                f"{cost_score:.2f}"
            )

            row["delivery_score"] = (
                f"{delivery_score:.2f}"
            )

            row["weighted_score"] = (
                f"{weighted_score:.2f}"
            )

        # Rank eligible suppliers by weighted score,
        # then cost, lead time, and quotation ID.
        group.sort(
            key=lambda row: (
                -Decimal(row["weighted_score"]),
                Decimal(row["total_cost_eur"]),
                Decimal(row["lead_time_days"]),
                row["quotation_id"],
            )
        )

        for position, row in enumerate(group):

            if position == 0:

                row["recommendation_status"] = (
                    "TOP_RANKED_PENDING_HUMAN_APPROVAL"
                )

            else:

                row["recommendation_status"] = (
                    "RANKED_ALTERNATIVE"
                )

    # --------------------------------------------------
    # 8. Evaluation summary
    # --------------------------------------------------

    counts = Counter(
        row["evaluation_status"]
        for row in evaluations
    )

    print()
    print("V5 Evaluation Summary")
    print("---------------------")

    print(
        "REVIEW_REQUIRED:",
        counts["REVIEW_REQUIRED"],
    )

    print(
        "BLOCKED:",
        counts["BLOCKED"],
    )

    print(
        "ELIGIBLE_FOR_ANALYSIS:",
        counts["ELIGIBLE_FOR_ANALYSIS"],
    )

    print(
        "Total quotations:",
        len(evaluations),
    )

    # --------------------------------------------------
    # 9. Simulation safeguards
    # --------------------------------------------------

    print()
    print("Cutoff basis: LATEST_QUOTATION_DATE_PROXY")
    print("Decision timestamp: NOT_VERIFIED")
    print("Historical evidence: SYNTHETIC_UNVERIFIED")
    print("Purchasing authorization: NOT_AUTHORIZED")

    # --------------------------------------------------
    # 10. Return results
    # --------------------------------------------------

    return {
        "datasets": datasets,
        "cutoffs": cutoffs,
        "quotation_costs": quotation_costs,
        "supplier_performance": supplier_performance,
        "evaluations": evaluations,
    }


if __name__ == "__main__":
    evaluate()
