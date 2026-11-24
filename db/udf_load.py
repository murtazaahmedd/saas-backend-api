"""Apply the schema and every api.* function. Idempotent: safe to run on every deploy."""
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parent
UDF_FILES = ["udf/api/enforce.sql", "udf/api/users.sql", "udf/api/projects.sql", "udf/api/idempotency.sql"]


def migrate(dsn: str) -> None:
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute((ROOT / "schema.sql").read_text())
        for rel in UDF_FILES:
            conn.execute((ROOT / rel).read_text())


if __name__ == "__main__":
    import os
    migrate(os.environ["DATABASE_URL"])
    print("schema and api.* functions applied")
