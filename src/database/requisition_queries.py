
from src.database.connection import get_connection


def get_all_requisitions():
    """
    Retrieve purchase requisitions from PostgreSQL.

    Returns:
        list[dict]: Purchase requisition records.
    """
    query = """
        SELECT
            requisition_id,
            product_id,
            requested_quantity,
            request_date,
            required_delivery_date,
            status
        FROM procurement.purchase_requisitions
        ORDER BY requisition_id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)

            columns = [
                column.name
                for column in cur.description
            ]

            return [
                dict(zip(columns, row))
                for row in cur.fetchall()
            ]


from src.database.supplier_queries import get_suppliers_by_product


def get_requisition_suppliers(requisition_id):
    """
    Retrieve a requisition and suppliers associated
    with its requested product.
    """
    query = """
        SELECT
            requisition_id,
            product_id,
            requested_quantity,
            request_date,
            required_delivery_date,
            status
        FROM procurement.purchase_requisitions
        WHERE requisition_id = %s;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (requisition_id,))
            row = cur.fetchone()

            if row is None:
                return None

            columns = [col.name for col in cur.description]
            requisition = dict(zip(columns, row))

    suppliers = get_suppliers_by_product(
        requisition["product_id"]
    )

    return {
        "requisition": requisition,
        "suppliers": suppliers,
    }


def get_requisition_evaluation_cutoff(requisition_id):
    """
    Calculate the V4-compatible evaluation cutoff.

    Uses the latest quotation date that is not earlier
    than the requisition request date.

    This is a proxy, not a verified decision timestamp.
    """
    query = """
        SELECT
            r.requisition_id,
            r.request_date,
            COALESCE(
                MAX(q.quotation_date) FILTER (
                    WHERE q.quotation_date >= r.request_date
                ),
                r.request_date
            ) AS evaluation_as_of
        FROM procurement.purchase_requisitions r
        LEFT JOIN procurement.quotations q
            ON q.requisition_id = r.requisition_id
        WHERE r.requisition_id = %s
        GROUP BY r.requisition_id, r.request_date;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (requisition_id,))

            row = cur.fetchone()

            if row is None:
                return None

            columns = [col.name for col in cur.description]
            return dict(zip(columns, row))

