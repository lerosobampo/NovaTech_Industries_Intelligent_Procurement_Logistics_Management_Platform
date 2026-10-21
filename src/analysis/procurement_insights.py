
"""
NovaTech Industries
Procurement Insights Engine — V1

Generates analytical insights from the PostgreSQL-backed
Supplier Evaluation Engine V5.

All data is synthetic and unverified.
Cost differences are hypothetical, not realized savings.
No purchasing decisions are authorized.
"""

from collections import Counter
from statistics import mean

from src.analysis.evaluate_suppliers_v5 import evaluate


def _number(value):
    """Convert a numeric value safely, preserving missing values."""
    if value is None or value == "":
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _group_by_requisition(evaluations):
    """Group supplier quotations by purchase requisition."""
    grouped = {}

    for row in evaluations:
        requisition_id = row["requisition_id"]
        grouped.setdefault(requisition_id, []).append(row)

    return grouped


def calculate_cost_opportunities(evaluations):
    """
    Compare the lowest and highest quoted costs per requisition.

    These are hypothetical quotation spreads, not verified
    savings or actionable supplier recommendations.
    """
    insights = []

    for requisition_id, quotations in sorted(
        _group_by_requisition(evaluations).items()
    ):
        valid_costs = []

        for quotation in quotations:
            cost = _number(quotation.get("total_cost_eur"))

            if cost is not None and cost >= 0:
                valid_costs.append(
                    {
                        "quotation_id": quotation["quotation_id"],
                        "supplier_id": quotation["supplier_id"],
                        "total_cost_eur": cost,
                        "evaluation_status": quotation[
                            "evaluation_status"
                        ],
                    }
                )

        if not valid_costs:
            continue

        lowest = min(
            valid_costs,
            key=lambda row: (
                row["total_cost_eur"],
                row["quotation_id"],
            ),
        )

        highest = max(
            valid_costs,
            key=lambda row: (
                row["total_cost_eur"],
                row["quotation_id"],
            ),
        )

        spread = highest["total_cost_eur"] - lowest["total_cost_eur"]

        spread_pct = (
            spread / highest["total_cost_eur"] * 100
            if highest["total_cost_eur"] > 0
            else 0.0
        )

        insights.append(
            {
                "requisition_id": requisition_id,
                "quotation_count": len(valid_costs),
                "lowest_quotation_id": lowest["quotation_id"],
                "lowest_supplier_id": lowest["supplier_id"],
                "lowest_cost_eur": round(
                    lowest["total_cost_eur"], 2
                ),
                "lowest_evaluation_status": lowest[
                    "evaluation_status"
                ],
                "highest_quotation_id": highest["quotation_id"],
                "highest_supplier_id": highest["supplier_id"],
                "highest_cost_eur": round(
                    highest["total_cost_eur"], 2
                ),
                "potential_cost_difference_eur": round(
                    spread, 2
                ),
                "potential_cost_difference_pct": round(
                    spread_pct, 2
                ),
                "insight_classification": (
                    "HYPOTHETICAL_QUOTATION_SPREAD"
                ),
                "authorization_status": "NOT_AUTHORIZED",
            }
        )

    return insights


def calculate_supplier_risks(evaluations):
    """Summarize risk indicators by supplier."""
    grouped = {}

    for row in evaluations:
        supplier_id = row["supplier_id"]

        supplier = grouped.setdefault(
            supplier_id,
            {
                "supplier_id": supplier_id,
                "quotation_count": 0,
                "blocked_quotations": 0,
                "review_required_quotations": 0,
                "reason_counts": Counter(),
            },
        )

        supplier["quotation_count"] += 1

        status = row["evaluation_status"]

        if status == "BLOCKED":
            supplier["blocked_quotations"] += 1

        elif status == "REVIEW_REQUIRED":
            supplier["review_required_quotations"] += 1

        reasons = row.get("reasons") or ""

        for reason in reasons.split(";"):
            reason = reason.strip()

            if reason:
                supplier["reason_counts"][reason] += 1

    insights = []

    for supplier_id, supplier in sorted(grouped.items()):
        blocked = supplier["blocked_quotations"]
        review = supplier["review_required_quotations"]

        if blocked > 0:
            risk_level = "BLOCKED"
        elif review > 0:
            risk_level = "REVIEW_REQUIRED"
        else:
            risk_level = "NO_CURRENT_FLAGS"

        reason_counts = supplier["reason_counts"]

        insights.append(
            {
                "supplier_id": supplier_id,
                "quotation_count": supplier["quotation_count"],
                "blocked_quotations": blocked,
                "review_required_quotations": review,
                "risk_level": risk_level,
                "risk_reasons": ";".join(
                    sorted(reason_counts.keys())
                ),
                "reason_occurrences": sum(
                    reason_counts.values()
                ),
                "evidence_classification": (
                    "SYNTHETIC_UNVERIFIED"
                ),
            }
        )

    return insights


def calculate_delivery_insights(evaluations):
    """Compare quoted lead times and historical reliability."""
    insights = []

    for requisition_id, quotations in sorted(
        _group_by_requisition(evaluations).items()
    ):
        lead_times = [
            value
            for row in quotations
            if (
                value := _number(
                    row.get("lead_time_days")
                )
            ) is not None
            and value >= 0
        ]

        reliability_scores = [
            value
            for row in quotations
            if (
                value := _number(
                    row.get("reliability_score")
                )
            ) is not None
        ]

        insights.append(
            {
                "requisition_id": requisition_id,
                "quotation_count": len(quotations),
                "fastest_lead_time_days": (
                    min(lead_times) if lead_times else None
                ),
                "slowest_lead_time_days": (
                    max(lead_times) if lead_times else None
                ),
                "average_lead_time_days": (
                    round(mean(lead_times), 2)
                    if lead_times else None
                ),
                "average_reliability_score": (
                    round(mean(reliability_scores), 2)
                    if reliability_scores else None
                ),
                "delivery_evidence": (
                    "SYNTHETIC_UNVERIFIED"
                ),
            }
        )

    return insights


def calculate_procurement_bottlenecks(evaluations):
    """Identify requisitions that cannot proceed without review."""
    insights = []

    for requisition_id, quotations in sorted(
        _group_by_requisition(evaluations).items()
    ):
        statuses = Counter(
            row["evaluation_status"]
            for row in quotations
        )

        blocked = statuses["BLOCKED"]
        review = statuses["REVIEW_REQUIRED"]
        eligible = statuses["ELIGIBLE_FOR_ANALYSIS"]

        if eligible == 0:
            bottleneck_status = "NO_ANALYTICALLY_ELIGIBLE_QUOTES"
        elif review > 0 or blocked > 0:
            bottleneck_status = "PARTIAL_SUPPLIER_REVIEW_REQUIRED"
        else:
            bottleneck_status = "ANALYTICAL_REVIEW_ONLY"

        insights.append(
            {
                "requisition_id": requisition_id,
                "total_quotations": len(quotations),
                "blocked_quotations": blocked,
                "review_required_quotations": review,
                "eligible_for_analysis": eligible,
                "bottleneck_status": bottleneck_status,
                "requires_human_review": True,
                "authorization_status": "NOT_AUTHORIZED",
            }
        )

    return insights


def generate_procurement_insights():
    """Generate all insights using Supplier Evaluation Engine V5."""
    results = evaluate()
    evaluations = results["evaluations"]

    return {
        "cost_opportunities": calculate_cost_opportunities(
            evaluations
        ),
        "supplier_risks": calculate_supplier_risks(
            evaluations
        ),
        "delivery_insights": calculate_delivery_insights(
            evaluations
        ),
        "procurement_bottlenecks": calculate_procurement_bottlenecks(
            evaluations
        ),
        "governance": {
            "decision_mode": "SIMULATION",
            "evidence_classification": "SYNTHETIC_UNVERIFIED",
            "decision_timestamp": "NOT_VERIFIED",
            "authorization_status": "NOT_AUTHORIZED",
        },
    }


if __name__ == "__main__":
    insights = generate_procurement_insights()

    print("\nNOVATECH PROCUREMENT INSIGHTS")
    print("=" * 45)

    for category in (
        "cost_opportunities",
        "supplier_risks",
        "delivery_insights",
        "procurement_bottlenecks",
    ):
        records = insights[category]
        print(f"{category}: {len(records)} records")

    print("\nGovernance:")
    for key, value in insights["governance"].items():
        print(f"{key}: {value}")
