
from datetime import date, datetime
from decimal import Decimal

from src.database.connection import get_connection


EVALUATION_TABLES = {
    "suppliers": "procurement.suppliers",
    "products": "procurement.products",
    "purchase_requisitions": "procurement.purchase_requisitions",
    "quotations": "procurement.quotations",
    "quotation_items": "procurement.quotation_items",
    "supplier_products": "procurement.supplier_products",
    "supplier_status_history": "procurement.supplier_status_history",
    "supplier_compliance_history": "procurement.supplier_compliance_history",
    "supplier_inventory_history": "logistics.supplier_inventory_history",
    "supplier_deliveries": "logistics.supplier_deliveries",
    "supplier_quality_inspections": "logistics.supplier_quality_inspections",
}


def normalize_value(value):
    """
    Convert PostgreSQL values into CSV-compatible strings.

    Historical timestamps are represented by their date
    component to preserve V4's date-level evaluation rules.
    """

    if value is None:
        return ""

    if isinstance(value, datetime):
        return value.date().isoformat()

    if isinstance(value, date):
        return value.isoformat()

    if isinstance(value, bool):
        return str(value).lower()

    if isinstance(value, Decimal):
        return str(value)

    return str(value)


def load_evaluation_data():
    """
    Load the 11 datasets required by the V4 evaluation logic.

    Read-only database access.
    No procurement decisions or purchasing authorizations.
    """

    datasets = {}

    with get_connection() as conn:
        with conn.cursor() as cur:
            for name, table in EVALUATION_TABLES.items():

                # Table names are fixed constants, not user input.
                cur.execute(f"SELECT * FROM {table}")

                columns = [
                    column.name
                    for column in cur.description
                ]

                rows = []

                for record in cur.fetchall():
                    rows.append({
                        column: normalize_value(value)
                        for column, value in zip(columns, record)
                    })

                datasets[name] = rows

    return datasets
