"""Motor async de PostgreSQL para Gastos IA."""

import os
from urllib.parse import quote_plus

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

DATABASE_HOST = os.environ["GASTOSIA_DATABASE_HOST"]
DATABASE_PORT = os.environ["GASTOSIA_DATABASE_PORT"]
DATABASE_NAME = os.environ["GASTOSIA_DATABASE_NAME"]
DATABASE_USER = os.environ["GASTOSIA_DATABASE_USER"]
DATABASE_PASSWORD = os.environ["GASTOSIA_DATABASE_PASSWORD"]

DB_USER = os.environ["GASTOSIA_DATABASE_USER"]
DB_PASS = os.environ["GASTOSIA_DATABASE_PASSWORD"]

if os.environ.get("GASTOSIA_USE_ADMIN_DB"):
    DB_USER = "postgres"
    DB_PASS = os.environ["GASTOSIA_POSTGRES_ADMIN_PASSWORD"]

DATABASE_URL = (
    f"postgresql+asyncpg://{quote_plus(DB_USER)}:{quote_plus(DB_PASS)}"
    f"@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
)

if os.environ.get("GASTOSIA_TEST"):
    # En tests cada test corre en su propio event loop (pytest-asyncio
    # loop_scope=function). Un QueuePool compartido deja conexiones ligadas
    # a loops muertos ("Future attached to a different loop"); NullPool
    # cierra la conexion al devolverla y elimina ese modo de fallo.
    engine = create_async_engine(DATABASE_URL, poolclass=NullPool, echo=False)
else:
    engine = create_async_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        echo=False,
    )
