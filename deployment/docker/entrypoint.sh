#!/bin/sh
set -e

echo "[entrypoint] Aplicando migraciones alembic..."
uv run --no-sync alembic upgrade head

echo "[entrypoint] Iniciando uvicorn..."
exec uv run --no-sync uvicorn app.main:app --host 0.0.0.0 --port 8000
