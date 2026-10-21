
from src.database.connection import get_connection


def get_inventory_at_date(supplier_id, product_id, as_of_date):
    """
    Retrieve the latest inventory record known and effective
    at the specified date.

    Historical synthetic evidence is not purchasing authorization.
    """
    query = """
        SELECT
            supplier_id,
            product_id,
            available_quantity,
            minimum_order_quantity,
            effective_from,
            effective_to,
            recorded_at,
            evidence_source
        FROM logistics.supplier_inventory_history
        WHERE supplier_id = %s
          AND product_id = %s
          AND effective_from <= %s
          AND (effective_to IS NULL OR effective_to > %s)
          AND recorded_at < (%s::date + INTERVAL '1 day')
        ORDER BY effective_from DESC, recorded_at DESC
        LIMIT 1;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    supplier_id,
                    product_id,
                    as_of_date,
                    as_of_date,
                    as_of_date,
                ),
            )

            row = cur.fetchone()

            if row is None:
                return None

            columns = [col.name for col in cur.description]
            return dict(zip(columns, row))
