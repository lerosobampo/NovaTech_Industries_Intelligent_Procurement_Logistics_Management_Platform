
import unittest
from datetime import date
from unittest.mock import patch

from src.database.eligibility_assessment import (
    assess_supplier_eligibility,
)


class TestSupplierEligibility(unittest.TestCase):

    def setUp(self):

        self.product_patcher = patch(
            "src.database.eligibility_assessment.get_product_by_id",
            return_value={
                "product_id": "PRD004",
                "category": "Connectors",
            },
        )
        self.product_patcher.start()
        self.addCleanup(self.product_patcher.stop)

        self.status = {
            "status": "ACTIVE",
            "evidence_source": "SYNTHETIC_UNVERIFIED",
        }

        self.compliance = {
            "approval_status": "APPROVED",
            "evidence_source": "SYNTHETIC_UNVERIFIED",
        }

        self.compliance_record = {
            "approval_status": "APPROVED",
            "valid_until": None,
            "evidence_source": "SYNTHETIC_UNVERIFIED",
        }

        self.inventory = {
            "available_quantity": 401,
            "minimum_order_quantity": 20,
            "evidence_source": "SYNTHETIC_UNVERIFIED",
        }

    def assess(
        self,
        quantity=20,
        status=None,
        compliance=None,
        inventory=None,
        compliance_record=None,
    ):
        """
        Execute an eligibility assessment using mocked
        historical data.

        By default, compliance and compliance_record
        describe the same approval state.
        """

        selected_compliance = (
            self.compliance
            if compliance is None
            else compliance
        )

        selected_record = (
            self.compliance_record
            if compliance_record is None
            else compliance_record
        )

        # Keep the historical record consistent with the
        # selected compliance status unless the test
        # explicitly supplies a historical record.
        if (
            compliance is not None
            and compliance_record is None
        ):
            selected_record = {
                **self.compliance_record,
                "approval_status": compliance["approval_status"],
            }

        with (
            patch(
                "src.database.eligibility_assessment."
                "get_supplier_status_at_date",
                return_value=(
                    self.status if status is None else status
                ),
            ),
            patch(
                "src.database.eligibility_assessment."
                "get_supplier_compliance_at_date",
                return_value=selected_compliance,
            ),
            patch(
                "src.database.eligibility_assessment."
                "get_supplier_compliance_record_at_date",
                return_value=selected_record,
            ),
            patch(
                "src.database.eligibility_assessment."
                "get_inventory_at_date",
                return_value=(
                    self.inventory
                    if inventory is None else inventory
                ),
            ),
        ):
            return assess_supplier_eligibility(
                supplier_id="SUP004",
                product_id="PRD004",
                category="Connectors",
                requested_quantity=quantity,
                as_of_date="2026-10-15",
            )

    # --------------------------------------------------
    # Original tests
    # --------------------------------------------------

    def test_simulated_eligible(self):
        result = self.assess()

        self.assertEqual(
            result["assessment"],
            "SIMULATED_ELIGIBLE",
        )

    def test_insufficient_inventory(self):
        result = self.assess(quantity=500)

        self.assertEqual(
            result["assessment"],
            "INELIGIBLE",
        )

    def test_below_minimum_order(self):
        result = self.assess(quantity=10)

        self.assertEqual(
            result["assessment"],
            "INELIGIBLE",
        )

    def test_inactive_supplier(self):
        result = self.assess(
            status={
                "status": "INACTIVE",
                "evidence_source": "SYNTHETIC_UNVERIFIED",
            }
        )

        self.assertEqual(
            result["assessment"],
            "INELIGIBLE",
        )

    def test_unapproved_category(self):
        result = self.assess(
            compliance={
                "approval_status": "REJECTED",
                "evidence_source": "SYNTHETIC_UNVERIFIED",
            }
        )

        self.assertEqual(
            result["assessment"],
            "INELIGIBLE",
        )

        self.assertIn(
            "CATEGORY_COMPLIANCE_NOT_APPROVED",
            result["compliance_reasons"],
        )

    def test_missing_historical_evidence(self):
        # Explicitly mock all historical lookups as unavailable.
        with (
            patch(
                "src.database.eligibility_assessment."
                "get_supplier_status_at_date",
                return_value=None,
            ),
            patch(
                "src.database.eligibility_assessment."
                "get_supplier_compliance_at_date",
                return_value=None,
            ),
            patch(
                "src.database.eligibility_assessment."
                "get_supplier_compliance_record_at_date",
                return_value=None,
            ),
            patch(
                "src.database.eligibility_assessment."
                "get_inventory_at_date",
                return_value=None,
            ),
        ):
            result = assess_supplier_eligibility(
                "SUP004",
                "PRD004",
                "Connectors",
                20,
                "2025-12-31",
            )

        self.assertEqual(
            result["assessment"],
            "INSUFFICIENT_EVIDENCE",
        )

        self.assertIn(
            "CATEGORY_COMPLIANCE_HISTORY_MISSING",
            result["compliance_reasons"],
        )

    def test_never_authorizes_purchasing(self):
        for quantity in (10, 20, 500):
            result = self.assess(quantity=quantity)

            self.assertEqual(
                result["authorization_status"],
                "NOT_AUTHORIZED",
            )

            self.assertEqual(
                result["decision_mode"],
                "SIMULATION",
            )

    def test_product_category_mismatch(self):
        result = assess_supplier_eligibility(
            supplier_id="SUP004",
            product_id="PRD004",
            category="Sensors",
            requested_quantity=20,
            as_of_date="2026-10-15",
        )

        self.assertEqual(
            result["assessment"],
            "INELIGIBLE",
        )

        self.assertFalse(
            result["checks"]["product_category_valid"]
        )

        self.assertEqual(
            result["authorization_status"],
            "NOT_AUTHORIZED",
        )

    def test_nonexistent_product(self):
        with patch(
            "src.database.eligibility_assessment.get_product_by_id",
            return_value=None,
        ):
            result = assess_supplier_eligibility(
                supplier_id="SUP004",
                product_id="PRD999",
                category="Connectors",
                requested_quantity=20,
                as_of_date="2026-10-15",
            )

        self.assertEqual(
            result["assessment"],
            "INSUFFICIENT_EVIDENCE",
        )

        self.assertIsNone(
            result["checks"]["product_category_valid"]
        )

        self.assertEqual(
            result["authorization_status"],
            "NOT_AUTHORIZED",
        )

    # --------------------------------------------------
    # New historical compliance regression tests
    # --------------------------------------------------

    def test_expired_compliance(self):
        """
        An expired historical compliance record must
        block supplier eligibility.
        """

        result = self.assess(
            compliance_record={
                "approval_status": "EXPIRED",
                "valid_until": date(2026, 8, 31),
                "evidence_source": "SYNTHETIC_UNVERIFIED",
            },
            compliance={
                "approval_status": "EXPIRED",
                "evidence_source": "SYNTHETIC_UNVERIFIED",
            },
        )

        self.assertEqual(
            result["assessment"],
            "INELIGIBLE",
        )

        self.assertEqual(
            result["compliance_reasons"],
            [
                "CATEGORY_COMPLIANCE_NOT_APPROVED",
                "CATEGORY_COMPLIANCE_EXPIRED",
            ],
        )

        self.assertEqual(
            result["authorization_status"],
            "NOT_AUTHORIZED",
        )

    def test_approved_but_expired_compliance(self):
        """
        An APPROVED historical record must still be
        rejected when its validity has expired.
        """

        result = self.assess(
            compliance_record={
                "approval_status": "APPROVED",
                "valid_until": date(2026, 8, 31),
                "evidence_source": "SYNTHETIC_UNVERIFIED",
            },
        )

        self.assertEqual(
            result["assessment"],
            "INELIGIBLE",
        )

        self.assertIn(
            "CATEGORY_COMPLIANCE_EXPIRED",
            result["compliance_reasons"],
        )

        self.assertEqual(
            result["authorization_status"],
            "NOT_AUTHORIZED",
        )


if __name__ == "__main__":
    unittest.main()
