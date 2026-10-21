
"""
NovaTech Industries
Synthetic Data Importer — V1

Imports the V3 synthetic dataset into a dedicated PostgreSQL
demonstration database.

Safety:
- Only allows the database named novatech_demo.
- Refuses to import into populated destination tables.
- Uses a single transaction with automatic rollback on failure.
- Never deletes, truncates, or updates existing records.
- Supports CSV-only dry-run validation.

Run from the project root:

    python scripts/load_synthetic_data.py --dry-run

    DB_NAME=novatech_demo python scripts/load_synthetic_data.py
"""

import argparse
import csv
import os
import sys
from pathlib import Path

import psycopg
from psycopg import sql


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIRECTORY = PROJECT_ROOT / "data" / "synthetic" / "v3"

ALLOWED_DATABASE = "novatech_demo"

IMPORT_ORDER = [
    ("procurement", "suppliers"),
    ("procurement", "products"),
    ("procurement", "supplier_products"),
    ("procurement", "supplier_compliance"),
    ("procurement", "purchase_requisitions"),
    ("logistics", "supplier_deliveries"),
    ("logistics", "supplier_quality_inspections"),
    ("logistics", "supplier_inventory_history"),
    ("procurement", "supplier_status_history"),
    ("procurement", "supplier_compliance_history"),
    ("procurement", "quotations"),
    ("procurement", "quotation_items"),
    ("procurement", "procurement_decisions"),
    ("procurement", "procurement_approvals"),
    ("procurement", "procurement_decision_audit"),
]


class ImportValidationError(Exception):
    """Raised when data or database safety validation fails."""


def load_csv_dataset(table_name):
    """Read and validate one synthetic CSV dataset."""

    path = DATA_DIRECTORY / f"{table_name}.csv"

    if not path.is_file():
        raise ImportValidationError(
            f"Required CSV file not found: {path}"
        )

    with path.open(
        mode="r",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ImportValidationError(
                f"CSV has no header: {path.name}"
            )

        columns = list(reader.fieldnames)

        if len(columns) != len(set(columns)):
            raise ImportValidationError(
                f"Duplicate CSV columns: {path.name}"
            )

        if any(not column for column in columns):
            raise ImportValidationError(
                f"Invalid CSV header: {path.name}"
            )

        records = []

        for row_number, row in enumerate(reader, start=2):
            if None in row:
                raise ImportValidationError(
                    f"Unexpected extra fields in "
                    f"{path.name}, row {row_number}"
                )

            if any(value is None for value in row.values()):
                raise ImportValidationError(
                    f"Missing CSV fields in "
                    f"{path.name}, row {row_number}"
                )

            records.append(
                tuple(
                    None if row[column] == "" else row[column]
                    for column in columns
                )
            )

    return columns, records


def validate_datasets():
    """Validate all datasets without accessing PostgreSQL."""

    datasets = {}
    total_records = 0

    for schema_name, table_name in IMPORT_ORDER:
        columns, records = load_csv_dataset(table_name)

        datasets[(schema_name, table_name)] = (
            columns,
            records,
        )

        total_records += len(records)

        print(
            f"[CSV OK] {schema_name}.{table_name}: "
            f"{len(records)} records"
        )

    print(
        f"\nValidated {len(datasets)} datasets "
        f"containing {total_records} records."
    )

    return datasets


def get_demo_connection():
    """Connect only to the explicitly authorized demo database."""

    configured_name = os.getenv("DB_NAME")

    if configured_name != ALLOWED_DATABASE:
        raise ImportValidationError(
            "Database safety check failed. "
            f"Set DB_NAME={ALLOWED_DATABASE} explicitly. "
            "The existing novatech database is not permitted."
        )

    connection = psycopg.connect(
        dbname=configured_name,
        user=os.getenv("DB_USER") or None,
        host=os.getenv("DB_HOST") or None,
        port=os.getenv("DB_PORT") or None,
        password=os.getenv("DB_PASSWORD") or None,
    )

    with connection.cursor() as cursor:
        cursor.execute("SELECT current_database()")
        actual_database = cursor.fetchone()[0]

    if actual_database != ALLOWED_DATABASE:
        connection.close()
        raise ImportValidationError(
            "Connected to an unexpected database. "
            "Import cancelled."
        )

    return connection


def validate_database_tables(cursor, datasets):
    """Check table columns and ensure destination tables are empty."""

    for (schema_name, table_name), (
        csv_columns,
        records,
    ) in datasets.items():

        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = %s
              AND table_name = %s
            ORDER BY ordinal_position
            """,
            (schema_name, table_name),
        )

        database_columns = [
            row[0] for row in cursor.fetchall()
        ]

        if not database_columns:
            raise ImportValidationError(
                f"Destination table missing: "
                f"{schema_name}.{table_name}"
            )

        if set(csv_columns) != set(database_columns):
            raise ImportValidationError(
                f"Column mismatch for "
                f"{schema_name}.{table_name}. "
                f"CSV: {csv_columns}; "
                f"Database: {database_columns}"
            )

        cursor.execute(
            sql.SQL(
                "SELECT EXISTS (SELECT 1 FROM {}.{})"
            ).format(
                sql.Identifier(schema_name),
                sql.Identifier(table_name),
            )
        )

        if cursor.fetchone()[0]:
            raise ImportValidationError(
                f"Destination table is not empty: "
                f"{schema_name}.{table_name}. "
                "Import cancelled."
            )

        print(
            f"[DB OK] {schema_name}.{table_name}: "
            "schema matches; table empty"
        )


def import_datasets(datasets):
    """Import all datasets within a single database transaction."""

    with get_demo_connection() as connection:
        with connection.cursor() as cursor:

            validate_database_tables(
                cursor,
                datasets,
            )

            print("\nStarting transactional import...\n")

            total_inserted = 0

            for (schema_name, table_name), (
                columns,
                records,
            ) in datasets.items():

                insert_statement = sql.SQL(
                    "INSERT INTO {}.{} ({}) VALUES ({})"
                ).format(
                    sql.Identifier(schema_name),
                    sql.Identifier(table_name),
                    sql.SQL(", ").join(
                        sql.Identifier(column)
                        for column in columns
                    ),
                    sql.SQL(", ").join(
                        sql.Placeholder()
                        for _ in columns
                    ),
                )

                cursor.executemany(
                    insert_statement,
                    records,
                )

                total_inserted += len(records)

                print(
                    f"[IMPORTED] {schema_name}.{table_name}: "
                    f"{len(records)} records"
                )

        # The connection context commits only if no exception occurs.

    print(
        f"\nImport completed successfully. "
        f"{total_inserted} synthetic records loaded."
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Safely import NovaTech V3 synthetic data "
            "into novatech_demo."
        )
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate CSV datasets without accessing PostgreSQL.",
    )

    arguments = parser.parse_args()

    try:
        datasets = validate_datasets()

        if arguments.dry_run:
            print(
                "\nDRY RUN COMPLETE — "
                "No database connection or modifications."
            )
            return 0

        import_datasets(datasets)
        return 0

    except (
        ImportValidationError,
        psycopg.Error,
        OSError,
        csv.Error,
    ) as error:
        print(
            f"\nIMPORT FAILED: {error}",
            file=sys.stderr,
        )
        print(
            "No partial import will be committed "
            "if the transaction failed.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
