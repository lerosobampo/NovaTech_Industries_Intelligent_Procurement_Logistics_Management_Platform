
from src.database.connection import get_connection


def get_supplier_status_at_date(supplier_id, as_of_date):
    """
    Retrieve the supplier status effective and recorded
    by the specified evaluation date.

    Synthetic historical records are unverified evidence.
    """
    query = """
        SELECT
            supplier_id,
            status,
            effective_from,
            effective_to,
            recorded_at,
            evidence_source
        FROM procurement.supplier_status_history
        WHERE supplier_id = %s
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


def get_supplier_compliance_at_date(
    supplier_id,
    category,
    as_of_date
):
    """
    Retrieve historical supplier compliance information.

    Only records effective, recorded, and not expired
    at the evaluation date are considered.

    Synthetic evidence does not authorize purchasing.
    """
    query = """
        SELECT
            supplier_id,
            category,
            approval_status,
            effective_from,
            effective_to,
            valid_until,
            recorded_at,
            evidence_source
        FROM procurement.supplier_compliance_history
        WHERE supplier_id = %s
          AND category = %s
          AND effective_from <= %s
          AND (effective_to IS NULL OR effective_to > %s)
          AND recorded_at < (%s::date + INTERVAL '1 day')
          AND (valid_until IS NULL OR valid_until >= %s)
        ORDER BY effective_from DESC, recorded_at DESC
        LIMIT 1;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (
                    supplier_id,
                    category,
                    as_of_date,
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


def get_supplier_compliance_record_at_date(
    supplier_id,
    category,
    as_of_date,
):
    """
    Retrieve the historical compliance record effective
    and recorded by the evaluation date.

    Includes expired and rejected records so the
    evaluation engine can explain blocking reasons.

    Synthetic evidence remains unverified.
    """
    query = """
        SELECT
            supplier_id,
            category,
            approval_status,
            effective_from,
            effective_to,
            valid_until,
            recorded_at,
            evidence_source
        FROM procurement.supplier_compliance_history
        WHERE supplier_id = %s
          AND category = %s
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
                    category,
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

