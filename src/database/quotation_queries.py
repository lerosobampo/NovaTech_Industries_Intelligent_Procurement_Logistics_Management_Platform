
from src.database.connection import get_connection


def get_all_quotations():
    """
    Retrieve quotations and their line items from PostgreSQL.

    Read-only query. Does not create or approve purchases.
    """
    query = """
        SELECT
            q.quotation_id,
            q.requisition_id,
            q.supplier_id,
            q.quotation_date,
            q.valid_until,
            q.currency,
            q.status,
            qi.product_id,
            qi.quoted_quantity,
            qi.unit_price_eur,
            qi.freight_eur,
            qi.duties_eur,
            qi.other_fees_eur,
            qi.lead_time_days
        FROM procurement.quotations q
        JOIN procurement.quotation_items qi
            ON q.quotation_id = qi.quotation_id
        ORDER BY q.quotation_id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)

            columns = [col.name for col in cur.description]

            return [
                dict(zip(columns, row))
                for row in cur.fetchall()
            ]


def get_quotations_by_requisition(requisition_id):
    """
    Retrieve quotations and line items for one requisition.

    Read-only. No purchasing authorization is issued.
    """
    query = """
        SELECT
            q.quotation_id,
            q.requisition_id,
            q.supplier_id,
            q.quotation_date,
            q.valid_until,
            q.currency,
            q.status,
            qi.product_id,
            qi.quoted_quantity,
            qi.unit_price_eur,
            qi.freight_eur,
            qi.duties_eur,
            qi.other_fees_eur,
            qi.lead_time_days
        FROM procurement.quotations q
        JOIN procurement.quotation_items qi
            ON q.quotation_id = qi.quotation_id
        WHERE q.requisition_id = %s
        ORDER BY q.quotation_id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (requisition_id,))

            columns = [col.name for col in cur.description]

            return [
                dict(zip(columns, row))
                for row in cur.fetchall()
            ]

