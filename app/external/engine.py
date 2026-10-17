"""Engine del destino externo.

Por defecto reutiliza el engine de la app (misma instancia PostgreSQL,
tabla calificada gastobot.expense_records). Solo crea un engine propio si
GASTOSIA_EXT_DATABASE_HOST esta definido (override futuro).
"""

import os
import time
from urllib.parse import quote_plus

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database.engine import engine as app_engine

EXT_HOST = os.environ.get("GASTOSIA_EXT_DATABASE_HOST", "").strip()

_connectivity_checked_at = 0.0
_connectivity_online = True


def _build_override_engine() -> AsyncEngine:
    host = EXT_HOST
    port = os.environ.get("GASTOSIA_EXT_DATABASE_PORT", "5432")
    name = os.environ["GASTOSIA_EXT_DATABASE_NAME"]
    user = os.environ["GASTOSIA_EXT_DATABASE_USER"]
    password = os.environ["GASTOSIA_EXT_DATABASE_PASSWORD"]
    url = f"postgresql+asyncpg://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{name}"
    return create_async_engine(
        url,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        echo=False,
    )


external_engine: AsyncEngine = _build_override_engine() if EXT_HOST else app_engine
external_session = async_sessionmaker(external_engine, class_=AsyncSession, expire_on_commit=False)


async def verify_connectivity() -> bool:
    """Comprobar el destino con SELECT 1, cacheado 30 segundos."""
    global _connectivity_checked_at, _connectivity_online
    now = time.monotonic()
    if now - _connectivity_checked_at < 30:
        return _connectivity_online

    _connectivity_checked_at = now
    try:
        async with external_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        _connectivity_online = True
    except Exception:
        _connectivity_online = False
    return _connectivity_online
