
"""
NovaTech Industries
Procurement Insights Engine — Automated Tests

Tests:
1. Cost opportunity calculations
2. Supplier risk classification
3. Delivery performance metrics
4. Procurement bottleneck detection
5. Missing numerical data
6. Governance safeguards

All test data is synthetic.
No database writes or purchasing authorization.
"""

import unittest

from src.analysis.procurement_insights import (
    calculate_cost_opportunities,
    calculate_supplier_risks,
    calculate_delivery_insights,
    calculate_procurement_bottlenecks,
)


def make_quotation(
    quotation_id,
    requisition_id,
    supplier_id,
    cost,
    lead_time,
    reliability,
    status,
    reasons="",
):
    """Create a controlled quotation for testing."""
    return {
        "quotation_id": quotation_id,
        "requisition_id": requisition_id,
        "supplier_id": supplier_id,
        "total_cost_eur": cost,
        "lead_time_days": lead_time,
        "reliability_score": reliability,
        "evaluation_status": status,
        "reasons": reasons,
    }


class TestProcurementInsights(unittest.TestCase):

    def setUp(self):
        self.evaluations = [
            make_quotation(
                "TEST_Q001",
                "TEST_REQ001",
                "TEST_SUP001",
                1000,
                5,
                95,
                "REVIEW_REQUIRED",
                "DECISION_TIMESTAMP_NOT_VERIFIED",
            ),
            make_quotation(
                "TEST_Q002",
                "TEST_REQ001",
                "TEST_SUP002",
                1500,
                10,
                85,
                "BLOCKED",
                "INACTIVE_SUPPLIER;CATEGORY_COMPLIANCE_EXPIRED",
            ),
            make_quotation(
                "TEST_Q003",
                "TEST_REQ002",
                "TEST_SUP001",
                2000,
                7,
                90,
                "ELIGIBLE_FOR_ANALYSIS",
            ),
        ]

    def test_cost_opportunity_calculation(self):
        results = calculate_cost_opportunities(
            self.evaluations
        )

        req001 = next(
            row for row in results
            if row["requisition_id"] == "TEST_REQ001"
        )

        self.assertEqual(req001["lowest_cost_eur"], 1000)
        self.assertEqual(req001["highest_cost_eur"], 1500)
        self.assertEqual(
            req001["potential_cost_difference_eur"],
            500,
        )
        self.assertAlmostEqual(
            req001["potential_cost_difference_pct"],
            33.33,
            places=2,
        )

    def test_cost_spread_is_not_authorized_savings(self):
        results = calculate_cost_opportunities(
            self.evaluations
        )

        for row in results:
            self.assertEqual(
                row["insight_classification"],
                "HYPOTHETICAL_QUOTATION_SPREAD",
            )
            self.assertEqual(
                row["authorization_status"],
                "NOT_AUTHORIZED",
            )

    def test_supplier_risk_classification(self):
        results = calculate_supplier_risks(
            self.evaluations
        )

        supplier_risks = {
            row["supplier_id"]: row
            for row in results
        }

        self.assertEqual(
            supplier_risks["TEST_SUP002"]["risk_level"],
            "BLOCKED",
        )
        self.assertEqual(
            supplier_risks["TEST_SUP002"]["blocked_quotations"],
            1,
        )
        self.assertIn(
            "INACTIVE_SUPPLIER",
            supplier_risks["TEST_SUP002"]["risk_reasons"],
        )

    def test_supplier_risk_aggregation(self):
        results = calculate_supplier_risks(
            self.evaluations
        )

        supplier = next(
            row for row in results
            if row["supplier_id"] == "TEST_SUP001"
        )

        self.assertEqual(supplier["quotation_count"], 2)
        self.assertEqual(
            supplier["review_required_quotations"],
            1,
        )
        self.assertEqual(
            supplier["risk_level"],
            "REVIEW_REQUIRED",
        )

    def test_delivery_performance_calculation(self):
        results = calculate_delivery_insights(
            self.evaluations
        )

        req001 = next(
            row for row in results
            if row["requisition_id"] == "TEST_REQ001"
        )

        self.assertEqual(
            req001["fastest_lead_time_days"],
            5,
        )
        self.assertEqual(
            req001["slowest_lead_time_days"],
            10,
        )
        self.assertEqual(
            req001["average_lead_time_days"],
            7.5,
        )
        self.assertEqual(
            req001["average_reliability_score"],
            90,
        )

    def test_procurement_bottleneck_detection(self):
        results = calculate_procurement_bottlenecks(
            self.evaluations
        )

        bottlenecks = {
            row["requisition_id"]: row
            for row in results
        }

        self.assertEqual(
            bottlenecks["TEST_REQ001"]["bottleneck_status"],
            "NO_ANALYTICALLY_ELIGIBLE_QUOTES",
        )

        self.assertEqual(
            bottlenecks["TEST_REQ002"]["bottleneck_status"],
            "ANALYTICAL_REVIEW_ONLY",
        )

        for row in results:
            self.assertTrue(
                row["requires_human_review"]
            )
            self.assertEqual(
                row["authorization_status"],
                "NOT_AUTHORIZED",
            )

    def test_missing_numeric_values(self):
        evaluations = [
            make_quotation(
                "TEST_Q004",
                "TEST_REQ003",
                "TEST_SUP003",
                None,
                None,
                None,
                "REVIEW_REQUIRED",
            )
        ]

        cost_results = calculate_cost_opportunities(
            evaluations
        )

        delivery_results = calculate_delivery_insights(
            evaluations
        )

        self.assertEqual(cost_results, [])
        self.assertIsNone(
            delivery_results[0]["average_lead_time_days"]
        )
        self.assertIsNone(
            delivery_results[0]["average_reliability_score"]
        )

    def test_single_quotation_has_zero_cost_spread(self):
        results = calculate_cost_opportunities(
            self.evaluations
        )

        req002 = next(
            row for row in results
            if row["requisition_id"] == "TEST_REQ002"
        )

        self.assertEqual(
            req002["potential_cost_difference_eur"],
            0,
        )
        self.assertEqual(
            req002["potential_cost_difference_pct"],
            0,
        )


if __name__ == "__main__":
    unittest.main()
