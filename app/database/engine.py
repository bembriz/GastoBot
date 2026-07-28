"""Motor async de PostgreSQL para Gastos IA."""

import os
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_HOST = os.environ["GASTOSIA_DATABASE_HOST"]
DATABASE_PORT = os.environ["GASTOSIA_DATABASE_PORT"]
DATABASE_NAME = os.environ["GASTOSIA_DATABASE_NAME"]
DATABASE_USER = os.environ["GASTOSIA_DATABASE_USER"]
DATABASE_PASSWORD = os.environ["GASTOSIA_DATABASE_PASSWORD"]

DATABASE_URL = (
    f"postgresql+asyncpg://{DATABASE_USER}:{DATABASE_PASSWORD}"
    f"@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
)

engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=False,
)
