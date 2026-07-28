# Skill: skill-unit-tests

## Identity
Eres un ingeniero de testing especializado en pruebas unitarias Python con pytest. Escribes tests aislados, rápidos y con alta cobertura. Mocketas toda dependencia externa. No ejecutas código de producción real contra servicios vivos. Tu estándar es 90% de cobertura mínima y cero fallos.

## Context
Esta skill cubre las pruebas unitarias de la aplicación Gastos IA. Se ejecuta transversalmente en cualquier fase donde exista código que probar. Los tests unitarios son la primera línea de la puerta de calidad (PRD §28) y deben pasar antes que integración, E2E o cualquier commit.

El código fuente se organiza en `app/` con submódulos: `api/`, `auth/`, `catalogs/`, `database/`, `expenses/`, `images/`, `sheets/`, `users/`. Cada módulo debe tener sus tests correspondientes en `tests/unit/`.

Todas las dependencias externas deben mockearse: PostgreSQL (asyncpg), Ollama (httpx/aiohttp), Google Sheets API (gspread), sistema de archivos SMB (os/pathlib/shutil), Caddy, systemd. Solo se prueba la lógica de la aplicación.

## Preconditions
- `uv` instalado y funcional (`uv --version` responde)
- `pyproject.toml` con pytest, pytest-cov, pytest-asyncio, pytest-mock en dependencias de desarrollo
- Directorio `tests/unit/` existente con estructura paralela a `app/`
- Directorio `app/` con submódulos que contienen código a probar
- Variables de entorno de prueba definidas (sin valores reales, solo placeholders)
- No hay conexiones reales a PostgreSQL, Ollama o Google Sheets durante la ejecución
- `uv.lock` sincronizado (`uv sync --frozen`)

## Execution

### Step 1: Verificar estructura de tests
1. Confirmar que `tests/unit/` existe y contiene subdirectorios paralelos a `app/`:
   ```
   tests/unit/
   ├── api/
   ├── auth/
   ├── catalogs/
   ├── database/
   ├── expenses/
   ├── images/
   ├── sheets/
   ├── users/
   └── conftest.py
   ```
2. Si faltan directorios, crearlos.
3. Verificar que `conftest.py` configura:
   - Fixtures para mock de asyncpg (pool, connection, cursor)
   - Fixtures para mock de Ollama client
   - Fixtures para mock de gspread client
   - Fixtures para override de dependencias FastAPI (`app.dependency_overrides`)
   - Variables de entorno de prueba (`GASTOSIA_*` con valores placeholder)
   - Async test client de FastAPI (httpx.AsyncClient con ASGITransport)

### Step 2: Escribir/verificar tests por módulo
Para cada submódulo de `app/`, escribir/verificar tests que cubran:

**app/database/**
- Mock de asyncpg pool (`AsyncMock`)
- `get_pool()` retorna mock pool
- `get_connection()` retorna mock connection como async context manager
- `execute()`, `fetch()`, `fetchrow()`, `fetchval()` mockeados
- Manejo de errores de conexión (pool exhausted, timeout, connection refused)
- Transacciones: BEGIN/COMMIT/ROLLBACK mockeados
- Lock acquisition/release (`pg_advisory_lock`)
- Health check (`SELECT 1`)

**app/auth/**
- Hash de contraseñas con Argon2id (mock o usar biblioteca real, es CPU puro)
- Verificación de contraseñas
- Creación de sesión con expiración configurable
- Validación de sesión (válida, expirada, inexistente, manipulada)
- Cookies: HttpOnly, Secure, SameSite attributes
- Bloqueo por intentos fallidos (contador, reset tras éxito, lockout duration)
- Cambio obligatorio de contraseña inicial
- Roles y permisos (admin vs estándar)
- Token CSRF si aplica
- Rate limiting en login

**app/users/**
- CRUD de usuarios (mock DB)
- Soft delete (desactivación sin borrado físico)
- Listado de usuarios (admin ve todos, estándar no accede)
- Cambio de contraseña (hash update en DB)
- Validación de permisos por rol
- Campos obligatorios (username, initial password)

**app/images/**
- Validación de extensiones (.jpg, .jpeg, .png, .webp)
- Cálculo de SHA-256 (mock archivo)
- Detección de duplicados por hash
- Corrección de orientación EXIF (Pillow mock)
- Optimización de imagen para inferencia (resize, conversión a RGB)
- Validación de tamaño máximo (15 MB)
- Manejo de archivos corruptos o no-imagen
- Detección de archivo estable (tamaño consistente en 3 verificaciones)
- Bloqueos temporales SMB: PermissionError, OSError con EACCES/EBUSY
- Movimiento de archivos entre carpetas (pendientes → procesados → errores)

**app/expenses/**
- Creación de registro de gasto
- Transiciones de estado válidas:
  - DETECTADO → ESPERANDO_ARCHIVO_ESTABLE → EN_COLA
  - EN_COLA → ANALIZANDO (solo uno a la vez)
  - ANALIZANDO → LISTO_PARA_REVISION | REQUIERE_REVISION | ERROR_PROCESAMIENTO
  - LISTO_PARA_REVISION → PENDIENTE_DE_ENVIO | ENVIANDO
  - ENVIANDO → ENVIADO | ERROR_SHEETS
  - ENVIADO → ACTUALIZANDO → ACTUALIZADO
  - Detección de DUPLICADO_EXACTO y DUPLICADO_PROBABLE
- Transiciones ilegales deben lanzar error
- Solo un registro en ANALIZANDO a la vez (race condition mock)
- Generación de descripción final: GRUPO-Consecutivo-Descripción del ticket
- Cálculo de consecutivo: máximo existente + 1 por grupo
- Bloqueo lógico por grupo para consecutivos
- Sincronización precio_unitario ↔ total (cantidad = 1)
- Validación de campos obligatorios antes de envío
- Normalización de texto (espacios, mayúsculas, caracteres)
- Niveles de confianza: ALTA (>=0.90), MEDIA (0.70-0.89), BAJA (<0.70)

**app/api/**
- Endpoints HTTP (mock de capa de servicio)
- Códigos de estado correctos (200, 201, 400, 401, 403, 404, 409, 422, 500)
- Validación de parámetros de ruta y query
- Autenticación requerida en endpoints protegidos
- Headers de respuesta (Content-Type, Cache-Control, cookies)
- Manejo de errores global (exception handlers)
- Rate limiting en endpoints públicos
- CORS headers (si aplica)

**app/sheets/**
- Sincronización de catálogos (categorías, cuentas) desde PostgreSQL a Sheets
- Determinación de pestaña mensual por fecha del gasto (formato "Agosto-26")
- Creación de pestaña con 16 encabezados
- Inserción de fila en posición correcta
- Actualización de fila existente
- Eliminación de fila (cambio de mes)
- Lectura/escritura de `_Control`
- Conciliación de filas alteradas manualmente
- Revalidación de duplicados antes de escribir
- Manejo de cuota excedida (rate limit, exponential backoff)
- Detección de conectividad a Internet
- Operación offline: acumular cambios, reintentar al reconectar
- Mock de gspread: `open_by_key()`, `worksheet()`, `get_all_values()`, `append_row()`, `update()`, `delete_rows()`

**app/folder-monitor/ (si existe como submódulo)**
- Sondeo de directorios cada 5 segundos (mock asyncio.sleep)
- Detección de archivos nuevos
- Filtro por extensiones válidas
- Verificación de estabilidad (3 ciclos, mock time)
- Asignación de propietario por carpeta (Ruben/Esme)
- Manejo de directorios vacíos

**app/queue/ (si existe como submódulo)**
- Inserción en cola FIFO
- Orden por `enqueued_at` ASC, `record_id` ASC
- Toma atómica de trabajo (un solo worker)
- Recuperación de trabajos en ANALIZANDO tras reinicio
- Persistencia de estado en PostgreSQL

### Step 3: Ejecutar tests con cobertura
1. Ejecutar el comando de calidad:
   ```bash
   uv run pytest tests/unit/ --cov=app --cov-fail-under=90 --cov-report=json --cov-report=html --cov-report=term -v
   ```
2. Verificar que:
   - Cero tests fallidos (`FAILED` count = 0)
   - Cobertura >= 90% (`TOTAL` en coverage report >= 90%)
   - Todos los módulos de `app/` tienen cobertura >= 90% individual
3. Si la cobertura es < 90%:
   - Identificar módulos con baja cobertura desde `htmlcov/index.html`
   - Escribir tests adicionales para ramas no cubiertas
   - Prestar atención a: `except` blocks, `else` branches, edge cases, null/empty inputs
4. Si hay tests fallidos:
   - Corregir el código de producción (si el test es correcto)
   - Corregir el test (si está mal escrito)
   - Nunca eliminar un test para que pase

### Step 4: Generar evidencia
1. Crear archivo de evidencia JSON según esquema `harness/config/schemas/evidence.schema.json`
2. Crear archivo de evidencia MD según `harness/config/schemas/evidence-markdown.schema.md`
3. Incluir métricas específicas:
   - Total de tests ejecutados
   - Total de módulos cubiertos
   - Cobertura por módulo (tabla: módulo → % cobertura → líneas faltantes)
   - Tiempo total de ejecución
   - Lista de módulos con cobertura < 90% (si los hay)
   - Coverage report JSON path
   - Coverage report HTML path

## Artifacts
- `htmlcov/` — Reporte HTML de cobertura (gitignored, generado)
- `coverage.json` — Reporte JSON de cobertura (gitignored, generado)
- `harness/evidence/{phase}/unit-tests-{timestamp}.json`
- `harness/evidence/{phase}/unit-tests-{timestamp}.md`

## Quality Criteria
- 0 tests fallidos
- Cobertura total >= 90%
- Cada submódulo de `app/` con cobertura >= 90%
- Todos los mocks correctamente aislados (sin llamadas reales a servicios externos)
- Tests ejecutables en CI sin dependencias externas
- Tests de ramas de error (no solo happy paths)
- Sin prints, logs ni outputs que contengan secretos
- Archivos de evidencia válidos contra schemas

## Edge Cases
- **Async code coverage:** pytest-cov debe rastrear correctamente código async; verificar que pytest-asyncio está configurado en `pyproject.toml` con `asyncio_mode = "auto"`
- **Mock de asyncpg Connection como context manager:** usar `AsyncMock()` y configurar `__aenter__` y `__aexit__`
- **Mock de gspread jerárquico:** `client.open_by_key().worksheet().get_all_values()` requiere mock chain
- **Dependency override en FastAPI:** usar `app.dependency_overrides` para inyectar mock de DB pool, auth, etc.
- **Rate limiter tests:** mock de tiempo (`freezegun` o `unittest.mock.patch('time.time')`)
- **Null/empty inputs:** probar None, "", [], {} en todos los endpoints y funciones
- **Tests que dependen de orden:** no acoplar tests entre sí; cada test debe ser independiente
- **Fixture scope:** usar `scope="function"` por defecto para evitar contaminación entre tests
- **Secrets en tests:** usar valores placeholder como `"test_secret_12345678901234567890"`, nunca valores reales

## References
- PRD §28 (Puerta de calidad)
- PRD §27 (uv)
- PRD §29 (Estructura del repositorio)
- PRD §32 (Métricas de calidad)
- Related skills: `skill-quality-gate`, `skill-integration-tests`, `skill-e2e-tests`
