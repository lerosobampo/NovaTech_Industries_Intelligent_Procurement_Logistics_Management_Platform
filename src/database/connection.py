
import os

import psycopg


def get_connection():
    """
    Create a connection to the NovaTech PostgreSQL database.

    Connection settings can be configured through environment
    variables without hardcoding credentials.
    """
    return psycopg.connect(
        dbname=os.getenv("DB_NAME", "novatech"),
        user=os.getenv("DB_USER") or None,
        host=os.getenv("DB_HOST") or None,
        port=os.getenv("DB_PORT") or None,
        password=os.getenv("DB_PASSWORD") or None,
    )
