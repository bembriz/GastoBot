# Skill: skill-database

## Identity
Eres un ingeniero de base de datos especializado en PostgreSQL. Disenas esquemas normalizados, escribes migraciones reversibles, configuras indices y constraints, y garantizas la integridad y rendimiento del almacenamiento persistente.

## Context
Esta skill crea el schema completo de PostgreSQL para Gastos IA. Es la base sobre la que se construye TODO el resto del sistema. Un error aqui se propaga a todos los demas skills.

El diseno debe soportar:
- 9 tablas minimas (PRD §18): users, expense_records, image_files, extraction_runs, processing_queue, catalog_cache, sheet_sync, audit_events, system_settings
- Bloqueo de fila para consecutivos por grupo (PRD §12)
- Cola FIFO con reclamo atomico (PRD §9.2)
- Soft delete en catalogos
- Auditoria de todos los cambios de estado
- Conexion asincrona via SQLAlchemy + asyncpg

## Preconditions
- PostgreSQL accesible con base `gastos_ia` creada (validado en Fase 0)
- Usuario `gastos_app` con permisos CREATE en schema `public`
- Variables de entorno `GASTOSIA_DATABASE_*` configuradas
- `uv` con dependencias: `sqlalchemy[asyncio]`, `asyncpg`, `alembic`
- Rama `arnes` activa
- Directorio `migrations/` creado en raiz del proyecto

## Execution

### Step 1: Configurar SQLAlchemy y Alembic
1. Crear `app/database/__init__.py` vacio
2. Crear `app/database/engine.py`:
   - Configurar engine async con `create_async_engine`
   - URL desde variables de entorno: `postgresql+asyncpg://{GASTOSIA_DATABASE_USER}:{GASTOSIA_DATABASE_PASSWORD}@{GASTOSIA_DATABASE_HOST}:{GASTOSIA_DATABASE_PORT}/{GASTOSIA_DATABASE_NAME}`
   - Configurar pool_size=5, max_overflow=10, pool_pre_ping=True
   - NO hardcodear credenciales
3. Crear `app/database/session.py`:
   - `async_session` factory con `async_sessionmaker`
   - Dependency `get_db()` para FastAPI
4. Configurar Alembic:
   ```bash
   uv run alembic init migrations
   ```
   - Editar `migrations/env.py` para usar el engine async
   - Configurar `target_metadata` desde los modelos
   - Configurar `migrations/alembic.ini`: `sqlalchemy.url` desde variable de entorno (NO hardcodear)

### Step 2: Crear modelo base y mixins
1. Crear `app/database/models.py` con:
   - `Base = declarative_base()`
   - Mixin `TimestampMixin`: `created_at` (UTC, default now), `updated_at` (UTC, onupdate now)
   - Mixin `SoftDeleteMixin`: `is_active` (bool, default True), `deleted_at` (nullable timestamp)

### Step 3: Definir tabla `users`
Campos (PRD §18, §4):
- `id`: UUID, PK, default `uuid4`
- `username`: VARCHAR(50), UNIQUE, NOT NULL
- `password_hash`: VARCHAR(255), NOT NULL
- `role`: VARCHAR(20), NOT NULL, CHECK IN ('admin', 'standard')
- `is_active`: BOOLEAN, DEFAULT TRUE
- `created_at`: TIMESTAMPTZ, DEFAULT NOW()
- `last_login`: TIMESTAMPTZ, nullable
- `failed_attempts`: INTEGER, DEFAULT 0
- `locked_until`: TIMESTAMPTZ, nullable
- `password_change_required`: BOOLEAN, DEFAULT TRUE
- Indices: `ix_users_username` (UNIQUE)

### Step 4: Definir tabla `expense_records`
Campos (PRD §11, §12, §13.4, §17):
- `id`: UUID, PK
- `owner_id`: UUID, FK -> users.id, NOT NULL
- `image_hash`: VARCHAR(64), NOT NULL
- `transaction_date`: DATE, nullable
- `amount`: NUMERIC(12,2), nullable
- `ticket_description`: TEXT, nullable
- `bank`: VARCHAR(100), nullable
- `transaction_type`: VARCHAR(20), nullable, CHECK IN ('Transferencia', 'Credito', NULL)
- `confidence_json`: JSONB, nullable
- `group_code`: VARCHAR(50), nullable
- `consecutive`: INTEGER, nullable
- `final_description`: TEXT, nullable
- `category_id`: UUID, FK -> catalog_cache.id, nullable
- `account_id`: UUID, FK -> catalog_cache.id, nullable
- `status`: VARCHAR(30), NOT NULL, DEFAULT 'DETECTADO'
- `sheet_name`: VARCHAR(100), nullable
- `sheet_row`: INTEGER, nullable
- `source_filename`: VARCHAR(500), nullable
- `created_at`, `updated_at`: TIMESTAMPTZ
- `sent_at`: TIMESTAMPTZ, nullable
- Indices: `ix_expense_records_status`, `ix_expense_records_owner_id`, `ix_expense_records_image_hash` (UNIQUE), `ix_expense_records_group_consecutive` (group_code, consecutive, UNIQUE WHERE both NOT NULL)

### Step 5: Definir tabla `image_files`
Campos:
- `id`: UUID, PK
- `record_id`: UUID, FK -> expense_records.id, UNIQUE
- `original_path`: VARCHAR(1000), NOT NULL
- `optimized_path`: VARCHAR(1000), nullable
- `sha256_hash`: VARCHAR(64), NOT NULL, UNIQUE
- `file_size`: BIGINT, nullable
- `mime_type`: VARCHAR(50), nullable
- `width`: INTEGER, nullable
- `height`: INTEGER, nullable
- `exif_json`: JSONB, nullable
- `owner_folder`: VARCHAR(50), NOT NULL (Ruben/Esme)
- `created_at`: TIMESTAMPTZ
- Indices: `ix_image_files_sha256` (UNIQUE), `ix_image_files_owner_folder`

### Step 6: Definir tabla `extraction_runs`
Campos:
- `id`: UUID, PK
- `record_id`: UUID, FK -> expense_records.id, NOT NULL
- `model_name`: VARCHAR(50), NOT NULL
- `prompt_version`: VARCHAR(20), nullable
- `raw_response`: TEXT, nullable
- `parsed_json`: JSONB, nullable
- `is_valid_json`: BOOLEAN, DEFAULT FALSE
- `elapsed_ms`: INTEGER, nullable
- `error_message`: TEXT, nullable
- `created_at`: TIMESTAMPTZ
- Indice: `ix_extraction_runs_record_id`

### Step 7: Definir tabla `processing_queue`
Campos (PRD §9.2):
- `id`: UUID, PK
- `record_id`: UUID, FK -> expense_records.id, UNIQUE, NOT NULL
- `enqueued_at`: TIMESTAMPTZ, DEFAULT NOW(), NOT NULL
- `claimed_at`: TIMESTAMPTZ, nullable
- `completed_at`: TIMESTAMPTZ, nullable
- `worker_id`: VARCHAR(100), nullable
- `status`: VARCHAR(30), NOT NULL, DEFAULT 'EN_COLA'
- `priority`: INTEGER, DEFAULT 0
- `attempts`: INTEGER, DEFAULT 0
- `last_error`: TEXT, nullable
- Indices: `ix_processing_queue_status_enqueued` (status, enqueued_at ASC, record_id ASC) — CRITICO para reclamo FIFO

### Step 8: Definir tabla `catalog_cache`
Campos (PRD §10.5, §13.4):
- `id`: UUID, PK
- `catalog_type`: VARCHAR(20), NOT NULL (categoria/cuenta)
- `code`: VARCHAR(50), NOT NULL
- `description`: VARCHAR(255), NOT NULL
- `is_active`: BOOLEAN, DEFAULT TRUE
- `created_at`, `updated_at`: TIMESTAMPTZ
- `deleted_at`: TIMESTAMPTZ, nullable
- Indices: `ix_catalog_cache_type_active` (catalog_type, is_active), `ix_catalog_cache_type_code` (catalog_type, code, UNIQUE)

### Step 9: Definir tabla `sheet_sync`
Campos:
- `id`: UUID, PK
- `record_id`: UUID, FK -> expense_records.id, UNIQUE
- `sheet_name`: VARCHAR(100), NOT NULL
- `sheet_row`: INTEGER, NOT NULL
- `synced_at`: TIMESTAMPTZ, DEFAULT NOW()
- `sync_status`: VARCHAR(20) (inserted/updated/deleted)
- `sync_error`: TEXT, nullable
- Indice: `ix_sheet_sync_sheet_name_row` (sheet_name, sheet_row)

### Step 10: Definir tabla `audit_events`
Campos requeridos por PRD §21:
- `id`: UUID, PK
- `actor_id`: UUID, FK -> users.id, nullable (null para sistema)
- `record_id`: UUID, FK -> expense_records.id, nullable
- `event_type`: VARCHAR(50), NOT NULL
- `old_state`: JSONB, nullable
- `new_state`: JSONB, nullable
- `ip_address`: VARCHAR(45), nullable
- `created_at`: TIMESTAMPTZ, DEFAULT NOW()
- Indices: `ix_audit_events_record_id`, `ix_audit_events_actor_id`, `ix_audit_events_created_at`

### Step 11: Definir tabla `system_settings`
Campos:
- `id`: UUID, PK
- `key`: VARCHAR(100), UNIQUE, NOT NULL
- `value`: TEXT, NOT NULL
- `description`: TEXT, nullable
- `updated_at`: TIMESTAMPTZ
- `updated_by`: UUID, FK -> users.id, nullable
- Indice: `ix_system_settings_key` (UNIQUE)

### Step 12: Generar migracion inicial
1. Verificar que `target_metadata` en `migrations/env.py` importa todos los modelos
2. Generar migracion:
   ```bash
   uv run alembic revision --autogenerate -m "initial_schema"
   ```
3. Revisar el archivo generado en `migrations/versions/` — verificar que:
   - Todas las 9 tablas estan presentes
   - Constraints CHECK estan incluidos
   - FKs con ON DELETE correcto (RESTRICT o SET NULL segun corresponda)
   - Indices compuestos para la cola FIFO
4. Aplicar migracion:
   ```bash
   uv run alembic upgrade head
   ```
5. Verificar con `uv run alembic downgrade -1` que el rollback funciona
6. Volver a aplicar: `uv run alembic upgrade head`

### Step 13: Verificar schema
1. Crear script `scripts/validation/verify_schema.py` que:
   - Liste todas las tablas en schema `public`
   - Para cada tabla, liste columnas, tipos, constraints
   - Verifique que los indices existen
   - Inserte un registro de prueba en cada tabla y haga rollback
2. Ejecutar y verificar
3. Generar evidencia `schema-postgresql.json` y `schema-postgresql.md`

### Step 14: Configurar bloqueo de consecutivos
1. Crear `app/database/locking.py` con funcion:
   ```python
   async def get_next_consecutive(db: AsyncSession, group_code: str) -> int:
       # Usar advisory lock o SELECT FOR UPDATE
       # Bloquear fila en system_settings o tabla dedicada
       # Calcular max(consecutive) + 1
       # Retornar el siguiente consecutivo
   ```
2. Usar `pg_advisory_xact_lock` con hash del grupo para evitar deadlocks

## Artifacts
- `app/database/__init__.py`
- `app/database/engine.py`
- `app/database/session.py`
- `app/database/models.py`
- `app/database/locking.py`
- `migrations/env.py` (modificado)
- `migrations/alembic.ini` (modificado)
- `migrations/versions/{hash}_initial_schema.py`
- `scripts/validation/verify_schema.py`
- `harness/evidence/fase1/schema-postgresql.json`
- `harness/evidence/fase1/schema-postgresql.md`

## Quality Criteria
- Las 9 tablas existen en PostgreSQL con los campos especificados
- Todas las FKs, CHECKs, e indices existen
- La migracion `upgrade` y `downgrade` funcionan sin errores
- Los tipos de datos son correctos (UUID para PKs, TIMESTAMPTZ para fechas, NUMERIC para montos)
- `ix_processing_queue_status_enqueued` incluye (status, enqueued_at ASC, record_id ASC) para consulta FIFO
- `ix_expense_records_group_consecutive` es unique parcial (WHERE NOT NULL)
- La funcion `get_next_consecutive` usa bloqueo explicito
- Conexion async funciona con `async_session`
- NO hay credenciales hardcodeadas en `alembic.ini` o `engine.py`
- `uv run alembic upgrade head` ejecuta sin errores

## Edge Cases
- **Pool de conexiones agotado:** configurar `pool_size` y `max_overflow` adecuados (5 concurrentes max con 2 usuarios)
- **Migracion fallida a mitad:** usar transacciones de Alembic; si falla, hacer rollback completo
- **Colision de consecutivos:** el advisory lock por grupo previene esto; validar con test concurrente
- **UUID vs SERIAL para PKs:** usar UUID para evitar colisiones en entornos distribuidos futuros (aunque MVP es single-node)
- **JSONB vs TEXT para confidence_json:** usar JSONB para permitir queries por campos de confianza
- **Borrado de usuarios con registros:** FK con ON DELETE RESTRICT; no se puede borrar usuario con gastos
- **Cambio de schema en produccion:** documentar que requiere migracion manual aprobada

## References
- PRD §18 (PostgreSQL - lista de tablas minimas)
- PRD §12 (Descripcion y consecutivo - bloqueo logico)
- PRD §9.2 (Cola de procesamiento - indice FIFO)
- PRD §17 (Estados - valores y transiciones)
- PRD §13.4 (Pestanas tecnicas - campos de _Control)
- Related skills: `skill-authentication`, `skill-fifo-queue`, `skill-folder-monitor`, `skill-image-extraction`
