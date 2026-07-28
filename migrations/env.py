"""Alembic env.py — configuracion async para Gastos IA."""

import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from app.database.models import Base  # noqa: F401 — importa todos los modelos

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

DB_USER = os.environ.get("GASTOSIA_MIGRATION_USER", os.environ["GASTOSIA_DATABASE_USER"])
DB_PASS = os.environ.get("GASTOSIA_MIGRATION_PASSWORD", os.environ["GASTOSIA_DATABASE_PASSWORD"])
DATABASE_URL = (
    f"postgresql+asyncpg://"
    f"{DB_USER}:{DB_PASS}"
    f"@{os.environ['GASTOSIA_DATABASE_HOST']}:{os.environ['GASTOSIA_DATABASE_PORT']}"
    f"/{os.environ['GASTOSIA_DATABASE_NAME']}"
)
config.set_main_option("sqlalchemy.url", DATABASE_URL)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
