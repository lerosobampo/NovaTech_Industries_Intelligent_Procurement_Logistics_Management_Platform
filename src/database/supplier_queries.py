
from src.database.connection import get_connection


def get_all_suppliers():
    """
    Retrieve all suppliers from the PostgreSQL database.

    Returns:
        list[dict]: Supplier records.
    """
    query = """
        SELECT
            supplier_id,
            supplier_name,
            country,
            status
        FROM procurement.suppliers
        ORDER BY supplier_id;
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

def get_suppliers_by_product(product_id):
    """
    Retrieve suppliers associated with a specific product.

    Args:
        product_id (str): Product identifier.

    Returns:
        list[dict]: Supplier-product records.
    """
    query = """
        SELECT
            s.supplier_id,
            s.supplier_name,
            s.country,
            s.status,
            sp.product_id,
            sp.minimum_order_quantity,
            sp.available_quantity
        FROM procurement.supplier_products sp
        JOIN procurement.suppliers s
            ON sp.supplier_id = s.supplier_id
        WHERE sp.product_id = %s
        ORDER BY s.supplier_id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (product_id,))

            columns = [
                column.name
                for column in cur.description
            ]

            return [
                dict(zip(columns, row))
                for row in cur.fetchall()
            ]


def get_product_by_id(product_id):
    """
    Retrieve a product and its official category
    from the PostgreSQL product catalog.
    """
    query = """
        SELECT
            product_id,
            sku,
            product_name,
            category,
            unit_of_measure
        FROM procurement.products
        WHERE product_id = %s;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (product_id,))

            row = cur.fetchone()

            if row is None:
                return None

            columns = [col.name for col in cur.description]
            return dict(zip(columns, row))
