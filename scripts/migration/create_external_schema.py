"""Crear el esquema gastobot y la tabla espejo de forma idempotente.

Destino por defecto: misma instancia de la app (GASTOSIA_DATABASE_*).
Override opcional: GASTOSIA_EXT_DATABASE_*.

Uso:
  uv run python scripts/migration/create_external_schema.py
  uv run python scripts/migration/create_external_schema.py --dry-run
"""

import argparse
import asyncio
import os
import sys
from urllib.parse import quote_plus

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DDL = [
    "CREATE SCHEMA IF NOT EXISTS gastobot",
    """
    CREATE TABLE IF NOT EXISTS gastobot.expense_records (
        id BIGSERIAL PRIMARY KEY,
        record_id UUID,
        source VARCHAR(20) NOT NULL DEFAULT 'app',
        month_label VARCHAR(20) NOT NULL,
        expense_date VARCHAR(20) NOT NULL DEFAULT '',
        category VARCHAR(255) NOT NULL DEFAULT '',
        description TEXT NOT NULL DEFAULT '',
        employee VARCHAR(255) NOT NULL DEFAULT '',
        paid_by VARCHAR(255) NOT NULL DEFAULT '',
        activities TEXT NOT NULL DEFAULT '',
        accounting_date VARCHAR(20) NOT NULL DEFAULT '',
        account VARCHAR(255) NOT NULL DEFAULT '',
        unit_price VARCHAR(50) NOT NULL DEFAULT '',
        quantity VARCHAR(50) NOT NULL DEFAULT '',
        include_taxes VARCHAR(50) NOT NULL DEFAULT '',
        tax_amount VARCHAR(50) NOT NULL DEFAULT '',
        total VARCHAR(50) NOT NULL DEFAULT '',
        estado VARCHAR(100) NOT NULL DEFAULT '',
        bank VARCHAR(100) NOT NULL DEFAULT '',
        transaction_type VARCHAR(50) NOT NULL DEFAULT '',
        group_code VARCHAR(50),
        consecutive INTEGER,
        final_description TEXT,
        synced_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS uq_gastobot_expense_records_record_id
        ON gastobot.expense_records (record_id)
        WHERE record_id IS NOT NULL
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS uq_gastobot_expense_records_group_consecutive
        ON gastobot.expense_records (group_code, consecutive)
        WHERE consecutive IS NOT NULL
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_gastobot_expense_records_month
        ON gastobot.expense_records (month_label)
    """,
]


def target_url() -> tuple[str, str]:
    ext_host = os.environ.get("GASTOSIA_EXT_DATABASE_HOST", "").strip()
    if ext_host:
        host = ext_host
        port = os.environ.get("GASTOSIA_EXT_DATABASE_PORT", "5432")
        name = os.environ["GASTOSIA_EXT_DATABASE_NAME"]
        user = os.environ["GASTOSIA_EXT_DATABASE_USER"]
        password = os.environ["GASTOSIA_EXT_DATABASE_PASSWORD"]
        label = f"{user}@{host}:{port}/{name} (override EXT)"
    else:
        host = os.environ["GASTOSIA_DATABASE_HOST"]
        port = os.environ["GASTOSIA_DATABASE_PORT"]
        name = os.environ["GASTOSIA_DATABASE_NAME"]
        user = os.environ["GASTOSIA_DATABASE_USER"]
        password = os.environ["GASTOSIA_DATABASE_PASSWORD"]
        label = f"{user}@{host}:{port}/{name}"
    url = (
        f"postgresql+asyncpg://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{name}"
    )
    return url, label


async def main(dry_run: bool) -> int:
    url, label = target_url()
    print(f"[schema] Destino: {label}")
    if dry_run:
        for statement in DDL:
            print("---\n" + statement.strip())
        print("[dry-run] Sin cambios en la base de datos")
        return 0

    engine = create_async_engine(url, pool_pre_ping=True)
    try:
        async with engine.begin() as conn:
            for statement in DDL:
                await conn.execute(text(statement))
        print("[schema] Esquema gastobot y tabla expense_records listos")
        return 0
    finally:
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    sys.exit(asyncio.run(main(args.dry_run)))
