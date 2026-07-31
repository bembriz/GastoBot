"""Crear usuarios iniciales Ruben (admin) y Esme (standard).

Ejecutar:
  GASTOSIA_RUBEN_INITIAL_PASSWORD=xxx GASTOSIA_ESME_INITIAL_PASSWORD=xxx \
  GASTOSIA_SESSION_SECRET=xxx \
  uv run python scripts/init_users.py
"""

import asyncio
import os
import sys

from sqlalchemy.dialects.postgresql import insert

from app.auth.password import hash_password
from app.database.engine import engine
from app.database.models import User
from app.database.session import async_session

MIN_PASSWORD_LENGTH = 8


async def init_users() -> int:
    ruben_pass = os.environ.get("GASTOSIA_RUBEN_INITIAL_PASSWORD", "")
    esme_pass = os.environ.get("GASTOSIA_ESME_INITIAL_PASSWORD", "")
    session_secret = os.environ.get("GASTOSIA_SESSION_SECRET", "")

    errors = []

    if not session_secret or len(session_secret) < 32:
        errors.append("GASTOSIA_SESSION_SECRET vacia o < 32 caracteres")

    if not ruben_pass or len(ruben_pass) < MIN_PASSWORD_LENGTH:
        errors.append(f"GASTOSIA_RUBEN_INITIAL_PASSWORD vacia o < {MIN_PASSWORD_LENGTH} caracteres")

    if not esme_pass or len(esme_pass) < MIN_PASSWORD_LENGTH:
        errors.append(f"GASTOSIA_ESME_INITIAL_PASSWORD vacia o < {MIN_PASSWORD_LENGTH} caracteres")

    if errors:
        for e in errors:
            print(f"[ERROR] {e}", file=sys.stderr)
        return 1

    hashed_ruben = hash_password(ruben_pass)
    hashed_esme = hash_password(esme_pass)

    users = [
        {"username": "Ruben", "role": "admin", "hash": hashed_ruben},
        {"username": "Esme", "role": "standard", "hash": hashed_esme},
    ]

    async with async_session() as db:
        for u in users:
            stmt = insert(User).values(
                username=u["username"],
                password_hash=u["hash"],
                role=u["role"],
                password_change_required=True,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["username"],
                set_=dict(
                    password_hash=stmt.excluded.password_hash,
                    role=u["role"],
                    password_change_required=True,
                ),
            )
            await db.execute(stmt)
            print(f"[OK] Usuario {u['username']} ({u['role']}) creado/actualizado")

        await db.commit()

    await engine.dispose()
    print("\n[OK] Usuarios iniciales configurados. Hash: Argon2id.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(init_users()))
