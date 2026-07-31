"""Bloqueo de consecutivos por grupo via PostgreSQL advisory lock.

Previene colisiones cuando dos workers intentan asignar
el mismo consecutivo para el mismo grupo simultaneamente.
"""

import hashlib

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def _group_lock_id(group_code: str) -> int:
    """Convertir group_code en un int de 64 bits para pg_advisory_xact_lock."""
    h = hashlib.md5(group_code.upper().encode())
    return int.from_bytes(h.digest()[:8], byteorder="big", signed=False)


async def get_next_consecutive(db: AsyncSession, group_code: str) -> int:
    """Obtener el siguiente consecutivo para un grupo con bloqueo atomico.

    Usa pg_advisory_xact_lock para serializar el acceso por grupo.
    El lock se libera automaticamente al terminar la transaccion.
    """
    lock_id = _group_lock_id(group_code)

    await db.execute(text("SELECT pg_advisory_xact_lock(:lock_id)"), {"lock_id": lock_id})

    result = await db.execute(
        text(
            "SELECT COALESCE(MAX(consecutive), 0) + 1 "
            "FROM expense_records "
            "WHERE group_code = :group"
        ),
        {"group": group_code.upper()},
    )
    next_val = result.scalar_one()
    return int(next_val)
