# Checklist — skill-database

## Pre-ejecucion
- [ ] PostgreSQL accesible y base `gastos_ia` existe
- [ ] Usuario `gastos_app` tiene permisos CREATE en schema public
- [ ] Variables `GASTOSIA_DATABASE_*` configuradas
- [ ] `uv add sqlalchemy[asyncio] asyncpg alembic` ejecutado
- [ ] Directorio `migrations/` creado
- [ ] Directorio `app/database/` creado

## Ejecucion
- [ ] `app/database/engine.py` con async engine, pool_size=5, pool_pre_ping=True
- [ ] `app/database/session.py` con `async_sessionmaker` y dependency `get_db`
- [ ] Alembic configurado con `target_metadata` async
- [ ] `alembic.ini` sin credenciales hardcodeadas
- [ ] Modelo `Base` y mixins (`TimestampMixin`, `SoftDeleteMixin`)
- [ ] Tabla `users` con 11 campos + indice unique username
- [ ] Tabla `expense_records` con 20+ campos + 4 indices
- [ ] Tabla `image_files` con 10 campos + indices
- [ ] Tabla `extraction_runs` con 9 campos + indice
- [ ] Tabla `processing_queue` con 9 campos + indice compuesto FIFO
- [ ] Tabla `catalog_cache` con 7 campos + indices
- [ ] Tabla `sheet_sync` con 6 campos + indice
- [ ] Tabla `audit_events` con 7 campos + indices
- [ ] Tabla `system_settings` con 5 campos + indice
- [ ] CHECK constraints en `users.role` y `expense_records.transaction_type`
- [ ] FK constraints con ON DELETE apropiado (RESTRICT para users, SET NULL o RESTRICT para otros)
- [ ] Indice `ix_processing_queue_status_enqueued` con orden ASC
- [ ] Indice `ix_expense_records_group_consecutive` UNIQUE parcial (WHERE NOT NULL)
- [ ] Migracion inicial generada con `--autogenerate`
- [ ] `alembic upgrade head` ejecutado sin errores
- [ ] `alembic downgrade -1` ejecutado sin errores (rollback)
- [ ] `alembic upgrade head` re-ejecutado (volver a ultima version)
- [ ] Script `verify_schema.py` lista todas las 9 tablas con columnas
- [ ] Todas las columnas tienen tipos correctos (UUID, TIMESTAMPTZ, NUMERIC, JSONB)
- [ ] `get_next_consecutive` usa advisory lock o SELECT FOR UPDATE
- [ ] Evidencia `schema-postgresql.json` y `schema-postgresql.md` generada

## Post-ejecucion
- [ ] `uv run alembic current` muestra la ultima migracion aplicada
- [ ] No hay warnings de Alembic sobre tipos no soportados
- [ ] `skill-quality-gate` ejecutado (al menos lint y tipos sobre los archivos creados)
- [ ] Archivos de evidencia validados contra schemas
- [ ] `harness/PROGRESS.md` actualizado
