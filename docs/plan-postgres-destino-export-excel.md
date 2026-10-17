# Plan Ejecutivo — Envío a PostgreSQL externo + Exportación Excel por mes

> Fecha: 2026-10-17 (v3, integra: move de imágenes a `gastobot/enviadas/<mes>/` y migración desde Sheets) · Rama: `feature/envio-postgres-y-export-excel` (base: `cambios-y-correcciones-octubre-06`, commit `7838d4b`)
> Estado: PLAN — pendiente de aprobación del usuario. Despliegue a `lenovosrv` bloqueado hasta validación explícita.

---

## 1. Objetivo

1. **Reemplazar el envío a Google Sheets** (lento: latencia gspread + `sleep(1)` por fila) por escritura en **PostgreSQL**: la tabla espejo vivirá en la base **`gastos_ia`** del contenedor existente en `lenovosrv`, en un esquema nuevo `gastobot` (§4). En el dashboard el botón pasa de "Enviar seleccionados a Sheets" a **"Enviar a BD"**.
2. **Nueva sección en `https://gastos.local/`** para visualizar los registros enviados agrupados por mes y **descargar un Excel (.xlsx) por mes** con el mismo layout de 16 columnas que hoy se escribe en Sheets. Las pestañas del Excel se nombran con el mes de la fecha del gasto: `Julio-2026`, `Agosto-2026`, etc.
3. **Move de imagen al enviar (respetando lo existente):** se conserva tal cual el comportamiento actual —al terminar la extracción la imagen pasa de la bandeja SMB a `procesados` (`app/expenses/queue.py:207-210`). Lo nuevo: al presionar **"Enviar a BD"**, la imagen se traslada **de `procesados` a `gastobot/enviadas/<mes>/`** (p. ej. `gastobot/enviadas/Julio-2026/OP-2602 -1.jpeg`), con mes = fecha del gasto en formato `Julio-2026`. Base configurable vía `GASTOSIA_SENT_IMAGES_DIR`.
4. **Detalle con imagen:** desde la sección de reportes se abre el detalle de cada registro insertado en la BD y se ve la imagen correspondiente —la ubicada en `gastobot/enviadas/<mes>/`— servida por ruta autenticada.
5. **Migración de registros existentes:** los registros históricos y actuales del archivo Sheets **"Reporte de gastos 2026"** se cargan en la BD externa para que la nueva sección de visualización tenga el universo completo desde el día uno.
6. **Despliegue en unidad secundaria:** la unidad secundaria **ya existe** en `lenovosrv` (se verá y detectará su punto de montaje al momento del despliegue). En esa unidad vivirán `gastobot/enviadas/` y `procesados` (directorios a crear + bind-mounts en el contenedor). Variables ya definidas en `.envrc`.

## 2. Decisiones de diseño (supuestos a confirmar)

| # | Decisión | Detalle |
|---|----------|---------|
| D1 | **Reemplazo, no duplicado** | El envío escribe solo a PostgreSQL externo. El código de Sheets (`app/sheets/`) se conserva en el repo y queda conmutable con `GASTOSIA_SEND_TARGET=sheets` (rollback instantáneo sin redeploy de código). |
| D2 | **Máquina de estados intacta** | Se reutilizan los estados existentes: `PENDIENTE_DE_ENVIO → ENVIANDO → ENVIADO` / `ERROR_SHEETS`. Sin migración del CHECK constraint. El usuario verá los mismos estados en el dashboard. |
| D3 | **Consecutivo: fuente única en BD local** | El consecutivo por grupo se sigue calculando con el advisory lock local (`app/database/locking.py`) y el mismo valor se escribe en la BD externa. La tabla externa tendrá UNIQUE parcial `(group_code, consecutive) WHERE consecutive IS NOT NULL` e índice por mes. |
| D4 | **Idempotencia por `record_id`** | Cada fila externa lleva el UUID local del registro. El envío hace upsert: reenviar un registro no duplica filas. |
| D5 | **`sheet_name`/`sheet_row` reutilizados** | En `ENVIADO`, `sheet_name` guarda la etiqueta de mes (`Julio-2026`) y `sheet_row` queda NULL (no aplica). `SheetSync` registra cada envío (sin cambios de esquema). |
| D6 | **Sección "Reportes por mes": solo admin** | Consistente con Catálogos/Historial (links admin en `templates/base.html`). Ruben administra; Esme no ve la sección. |
| D8 | **Naming de mes: `Julio-2026`** | El usuario lo especificó así para el Excel y las carpetas de imágenes. Nota: el código actual de Sheets crea pestañas `Julio-26` (año 2 dígitos, `app/sheets/tabs.py:45`). El Excel y `gastobot/enviadas/` usan formato largo; el código de Sheets, si se reactiva, queda como está. |
| D9 | **Cadena de la imagen: bandeja → procesados (existente) → enviadas (nuevo)** | No se toca `queue.py`: tras la extracción la imagen sigue yendo a `procesados` como hoy. Lo nuevo es el segundo traslado al enviar: `procesados` → `GASTOSIA_SENT_IMAGES_DIR/<Julio-2026>/`. Si el archivo no está en `procesados` (p. ej. monitor sin mover), el sender lo toma desde donde esté (`ImageFile.original_path` vigente). |
| D10 | **Destinos configurables: `GASTOSIA_PROCESSED_DIR` y `GASTOSIA_SENT_IMAGES_DIR`** | `PROCESSED_DIR` respeta la lógica actual si no se define (hermano de la carpeta del dueño). `SENT_IMAGES_DIR` define la base de `gastobot/enviadas/`; el sender crea la subcarpeta del mes (`Julio-2026`) y traslada con `copy2` + remove (patrón trans-archivo ya usado). Se actualiza `ImageFile.original_path` en el mismo commit del envío. Si el move falla, el envío **no** se invalida: warning en log/auditoría, registro queda `ENVIADO` (la fila externa es la fuente crítica) y la imagen queda sirviéndose desde donde esté. |
| D11 | **Imagen servida por ruta autenticada** | Nuevo `GET /expenses/{id}/image` valida sesión y dueño/admin, lee `ImageFile.original_path` y responde el binario con `mime_type`. Sin URLs estáticas directas al filesystem. El detalle (`expense_detail.html`) y la vista de reportes la reutilizan con `<img>`. |
| D12 | **Migración Sheets → BD externa (backfill)** | Script `scripts/migration/import_sheets_to_external.py`: lee el spreadsheet "Reporte de gastos 2026" con gspread (mismo service account actual) y carga todas las filas de todas las pestañas mensuales en la tabla externa. Precedente directo: `scripts/migration/import_from_sheets.py` (importó 618 históricos + 8 actuales a PostgreSQL local en sep-2026). Reglas: (i) filas cargadas como históricas — `consecutive`/grupo no se exigen (los 517 pares grupo/consecutivo colisionados de históricos se importan sin el par, igual que se hizo con la BD local); el UNIQUE parcial de D3 no los bloquea; (ii) `record_id` NULL para filas sin registro local (no vienen de la app), con columna `source` (`'app'`/`'sheets_migration'`) para distinguir; (iii) idempotente: re-ejecutar no duplica (dedup por clave natural fecha+descripción+monto o por `record_id` cuando existe); (iv) se ejecuta contra la BD externa real solo con autorización del usuario (puede validarse primero contra `gastos_ia_ext_test` local). |
| D13 | **Destino: misma instancia, esquema `gastobot`** (definido por el usuario) | La tabla espejo vive en `gastos_ia` del contenedor `self-evaluating-trading-agent-postgres-1` de `lenovosrv`, en esquema nuevo `gastobot`. El sender **reusa el engine existente** de la app (misma instancia, tabla qualificada `gastobot.expense_records`): sin segundo pool ni hop de red. `GASTOSIA_EXT_DATABASE_*` queda como override opcional futuro. La unidad secundaria del servidor (imágenes) ya existe; se detecta su montaje en el despliegue. |

## 3. Cambios por módulo

### 3.1 Nuevo módulo `app/external/` — envío a PostgreSQL

| Archivo | Contenido |
|---|---|
| `app/external/engine.py` | **Reusa el engine de la app** (`app/database/engine.py`, misma instancia `gastos_ia`) escribiendo con tabla qualificada `gastobot.expense_records`. Engine propio con `GASTOSIA_EXT_DATABASE_*` solo se activa si el override futuro está configurado. |
| `app/external/models.py` | Tabla espejo `gastobot.expense_records` (metadatos SQLAlchemy, esquema="gastobot"): `record_id UUID NULL` (FK lógica al local; NULL en filas de migración), `source` (`'app'`/`'sheets_migration'`), `month_label` (`Julio-2026`), las **16 columnas del layout Sheets**, `group_code`, `consecutive`, `final_description`, `synced_at`. UNIQUE parcial `(group_code, consecutive) WHERE consecutive IS NOT NULL`, índice `(month_label)`. |
| `app/external/sender.py` | `send_expense(record_id, group_code)` con **la misma firma y contrato** que `app/sheets/sender.py:22`: valida → conectividad (`SELECT 1`, cache 30 s) → `ENVIANDO` → consecutivo local → descripción final → upsert externo → `ENVIADO` (`sheet_name=month_label`, `sent_at`) → `SheetSync` + `AuditEvent` → commit → **trasladar imagen a `GASTOSIA_SENT_IMAGES_DIR/<month_label>/`** (D9/D10). Excepción → `ERROR_SHEETS`. Sin `time.sleep` bloqueante. |
| `app/external/repository.py` | Upsert idempotente y consultas de apoyo para la sección de reportes. |
| `app/images/files.py` (nuevo) | `move_image_to_sent(image, month_label) -> str | None`: traslado trans-archivo desde `ImageFile.original_path` (típicamente `procesados/`) hacia `<GASTOSIA_SENT_IMAGES_DIR>/<month_label>/`, actualización de `original_path`. Nunca lanza excepción al caller. |

**`app/expenses/queue.py` NO se modifica** — el move post-extracción a `procesados` se respeta tal cual (decisión del usuario).

**Layout de las 16 columnas** (idéntico a `app/sheets/tabs.py:24-41`):
`Fecha del gasto, Categoria, Descripcion, Empleado, Pagado por, Actividades, Fecha contable, Cuenta, Precio unitario, Cantidad, Incluir impuestos, Importe de impuestos, Total, Estado, Banco, Transaccion`

**Enganche:** en `app/expenses/routes.py` (envío individual `:392` y bulk `:493`) se despacha según `GASTOSIA_SEND_TARGET` (default `postgres`). Un punto de cambio, sin tocar la máquina de estados ni el worker FIFO.

### 3.2 Nuevo módulo `app/reports/` — visualización y Excel

| Archivo | Contenido |
|---|---|
| `app/reports/routes.py` | `GET /reports` — sección con meses disponibles (agrupado por mes de `transaction_date` de registros `ENVIADO`, con conteo e importe total); `GET /reports/excel?month=YYYY-MM` — stream de `.xlsx` (Content-Disposition `reporte-Julio-2026.xlsx`); **detalle**: `GET /reports/{id}` reutiliza la vista de detalle del registro. Admin only. |
| `app/reports/excel.py` | openpyxl (ya en `pyproject.toml`, sin uso actual): un libro con una pestaña nombrada `Julio-2026`, fila 1 = headers de las 16 columnas, filas = mismos valores que `build_sheet_row` (`tabs.py:76-102`). |
| `app/expenses/routes.py` | Nuevo `GET /expenses/{id}/image` (D11): autenticado, dueño/admin, sirve el binario desde `ImageFile.original_path` con `mime_type`. |
| `templates/dashboard.html` | Renombrar botón "Enviar seleccionados a Sheets" → **"Enviar a BD"** (texto/confirmación HTMX); resto del flujo bulk igual. |
| `templates/reports.html` | Tabla por mes (con link a detalle de cada registro) + botón descargar, patrones HTMX existentes (polling no necesario; datos estáticos por mes). |
| `templates/expense_detail.html` | Bloque `<img src="/expenses/{id}/image">` con fallback si la imagen no existe (registros importados históricos sin archivo). |
| `templates/base.html` + `templates/dashboard.html` | Link/entrada "Reportes" en nav (admin) + sección visible en el dashboard. |

### 3.3 Configuración

- `.env.example`: `GASTOSIA_SEND_TARGET` (default `postgres`), `GASTOSIA_PROCESSED_DIR` y `GASTOSIA_SENT_IMAGES_DIR` (placeholders; ambas ya definidas en `.envrc` local), y `GASTOSIA_EXT_DATABASE_*` (override opcional futuro — hoy el destino es la misma instancia vía esquema `gastobot`, §4).
- Sin migraciones Alembic en la BD local (D2/D5; D10 solo actualiza `ImageFile.original_path`, columna existente). El esquema `gastobot` y su tabla se crean con script idempotente `scripts/migration/create_external_schema.py` (DDL con `IF NOT EXISTS`), ejecutable contra cualquier instancia.

## 4. Destino del envío — RESUELTO

**El usuario definió el destino:** la base **`gastos_ia`** del contenedor `self-evaluating-trading-agent-postgres-1` en `lenovosrv` (puerto publicado `127.0.0.1:5433`; desde la red Docker, alias `postgres:5432` — el mismo que ya usa la app). Es la **misma instancia PostgreSQL** donde vive la base operativa de la aplicación; no hay servidor remoto adicional.

Para no mezclar con las 9 tablas operativas existentes, el envío escribe en un **esquema nuevo `gastobot`** creado dentro de `gastos_ia`, con la tabla espejo `gastobot.expense_records` (16 columnas del layout + metadatos, D3/D4/D12). DDL idempotente vía `scripts/migration/create_external_schema.py`.

Ventaja arquitectónica: al ser la misma instancia, el sender externo puede reusar el engine/Pool existente de la app (`app/database/engine.py`) con nombre de tabla qualificado por esquema — sin segundo pool, sin hop de red adicional y con la misma atomicidad de la BD local. Las variables `GASTOSIA_EXT_DATABASE_*` quedan definidas en `.env.example` como **override opcional** por si en el futuro el destino migra a otra instancia (en ese caso se activaría engine propio en `app/external/engine.py`).

## 5. Migración de registros existentes desde Sheets

Antes del despliegue (y solo con autorización del usuario, ya que toca el spreadsheet real y la BD externa real), se ejecuta el backfill D12:

1. **Dry-run local**: el script corre en modo `--dry-run` contra `gastos_ia_ext_test` en `local-postgres-lab`: lista pestañas, cuenta filas por pestaña, reporta las que no caben en el layout o con fechas inválidas. Sin escribir en Sheets ni en la BD real.
2. **Validación de datos esperados**: ~618 históricos (de `_Control`/pestañas mensuales, según lo importado en sep-2026) + registros actuales de las pestañas vigentes.
3. **Ejecución real** (autorizada): carga idempotente en la BD externa. Las filas migradas quedan con `source='sheets_migration'` y son visibles en la sección "Reportes por mes" y en los Excel descargables.
4. **Imágenes de históricos:** solo los registros con `ImageFile` vinculado (5 de la importación sep-2026) tendrán imagen en el visor; el resto muestra el fallback "sin imagen". No se miguran archivos físicos de imágenes históricas (no existen localmente).

## 6. Plan de trabajo y verificación (local únicamente)

| Paso | Trabajo | Verificación |
|---|---|---|
| 0 | ~~Inspección BD externa~~ — **resuelto por el usuario (D13):** destino = esquema `gastobot` dentro de `gastos_ia`. Preparación: crear base aislada `gastos_ia_ext_test` en `local-postgres-lab` como simulacro del destino | Script DDL `create_external_schema.py` ejecutado OK en el simulacro local |
| 1 | Scaffold: `app/external/` (engine, models), env vars, `.env.example` | `ruff` + `mypy` clean |
| 2 | `app/external/sender.py` + dispatcher en rutas + `app/images/files.py` (move a `enviadas/<mes>/`) + renombrar botón a "Enviar a BD" | Unit tests con BD externa **mockeada** y filesystem tmp (move ok desde procesados, move falla sin invalidar envío); sin llamadas a Gemini/Kimi/Ollama |
| 3 | Prueba real contra `local-postgres-lab` (`127.0.0.1:5434`): base aislada `gastos_ia_ext_test` (rol `gastosia_opencode`, password efímero por env). Envío sintético `opencode-test-*`, upsert idempotente reenviado, unique parcial, imagen movida de `procesados` a `enviadas/Julio-2026/`, `original_path` actualizado, cleanup 0 filas y 0 archivos sintéticos | Reporte de filas + filesystem + 0 residuos |
| 4 | `app/reports/` (rutas + Excel) + `GET /expenses/{id}/image` + templates + nav | Unit tests del Excel (headers, pestaña `Julio-2026`, layout) y de la ruta de imagen (auth, dueño, 404 sin archivo); smoke HTTP local en `127.0.0.1:8010` |
| 5 | Script de migración `import_sheets_to_external.py` + dry-run contra `gastos_ia_ext_test` | Conteo de filas por pestaña reportado, 0 escrituras externas reales, sin tocar Sheets |
| 6 | Quality gate completo local | `uv sync --frozen` · `ruff check` · `ruff format --check` · `mypy app/` · `pytest --cov>=60%` · `pip-audit` |
| 7 | Prueba E2E local: app contra `local-postgres-lab`, login sintético, envío bulk a BD externa local con imágenes sintéticas en `GASTOSIA_SMB_BASE`, verificar cadena bandeja→procesados→enviadas y visualización de imagen en detalle, descarga Excel, verificación del archivo | Excel abre con layout correcto por mes; imagen visible en detalle desde `enviadas/<mes>/`; archivo físico en la carpeta del mes |
| 8 | **GATE — Validación del usuario** | El usuario aprueba el comportamiento local |
| 9 | (Solo tras aprobación) **Despliegue a `lenovosrv`**: respaldo pre-despliegue, rebuild imagen, crear esquema `gastobot` en `gastos_ia` (script idempotente contra el contenedor `self-evaluating-trading-agent-postgres-1`), **unidad secundaria (ya existe en el servidor)**: detectar su punto de montaje con `lsblk`/`findmnt`, crear en ella `/gastos-ia/procesados` y `/gastobot/enviadas`, agregar bind-mounts en `deployment/docker/docker-compose.yml`, `GASTOSIA_PROCESSED_DIR`/`GASTOSIA_SENT_IMAGES_DIR` apuntando a esas rutas. Verificar con `df -h` que ambos destinos están efectivamente en la unidad secundaria y **no** en el disco del SO (`touch` de prueba dentro del contenedor). **Migración real Sheets→esquema `gastobot`** (autorizada en §5). Validación producción sin tocar el resto de `gastos_ia` más allá de registro sintético limpiado | Pendiente — fuera de alcance hasta autorización (R002/R003/R006) |

**Restricciones durante todo el trabajo:** cero tokens de extracción IA (extracción mockeada), cero escrituras en `gastos_ia` de producción, datos sintéticos con prefijo `opencode-test-` y limpieza garantizada, `uv` exclusivo, sin commits sin autorización explícita, migración Sheets real solo con autorización del usuario.

## 7. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| El esquema `gastobot` colisiona o se mezcla con tablas operativas existentes | El esquema es nuevo y aislado dentro de `gastos_ia`; el DDL es idempotente (`IF NOT EXISTS`) y califica siempre con `gastobot.`; nunca toca las 9 tablas operativas |
| Reenvío duplica filas en la externa | Upsert por `record_id` (D4) + UNIQUE parcial (D3) |
| Históricos con par grupo/consecutivo colisionado (517) rompen el UNIQUE | UNIQUE es parcial `WHERE consecutive IS NOT NULL`; la migración importa históricos sin el par (igual que la importación sep-2026 a la BD local) |
| Rollback necesario tras desplegar | `GASTOSIA_SEND_TARGET=sheets` restaura el comportamiento anterior sin redeploy (D1) |
| La lentitud persiste por otro cuello (p. ej. consecutivo) | El sender nuevo es una inserción de ~ms en red local; el `sleep(1)` y latencia gspread desaparecen por completo del camino crítico |
| Excel con muchos registros por mes | openpyxl maneja miles de filas sin problema; meses típicos < 200 registros |
| Falla el move de imagen (SMB caído, disco lleno, permisos) | El envío ya committed no se invalida (D10): warning en log/auditoría, la imagen queda en `procesados` y la ruta sigue sirviéndose desde ahí; reintento manual vía reenvío (upsert idempotente) |
| En despliegue, procesados/enviadas quedan en el disco del SO por error de montaje | Checklist de despliegue incluye `findmnt`/`df -h` de ambos destinos y `touch` de prueba dentro del contenedor antes de validar |
| La migración Sheets lee/pega datos inesperados (pestañas nuevas, layout cambiado) | Dry-run obligatorio con conteo por pestaña antes de ejecutar; solo pestañas que casen con el layout de 16 columnas se cargan, las demás se reportan y omiten |
| Registros migrados sin imagen confunden al usuario en el visor | Fallback explícito "sin imagen disponible" en el detalle; solo 5 históricos tienen imagen vinculada |

## 8. Estimación

| Fase | Horas |
|---|---|
| 0–2 (external engine + sender + move a enviadas + tests) | 6.5 |
| 3 (prueba real contenedor local) | 2 |
| 4–5 (reportes, detalle/imagen, Excel, script migración + dry-run) | 6 |
| 6–7 (quality gate + E2E local) | 2 |
| 9 (despliegue + unidad secundaria + migración real, solo tras GATE) | 2.5 |
| **Total** | **~19 h** |

## 9. Criterio de aceptación del cambio

1. Enviar un registro desde el dashboard con "Enviar a BD" escribe exactamente una fila en la BD externa con las 16 columnas del layout y queda en `ENVIADO` con `sheet_name = "Julio-2026"`.
2. Reenviar el mismo registro no duplica fila (upsert) ni la imagen en `enviadas/`.
3. Si la BD externa está caída, el registro queda en `PENDIENTE_DE_ENVIO`/`ERROR_SHEETS` visible y se puede reintentar — sin pérdida de datos.
4. Tras el envío exitoso, la imagen física está en `GASTOSIA_SENT_IMAGES_DIR/Julio-2026/` y `ImageFile.original_path` refleja la nueva ruta; si el move falla, el registro sigue `ENVIADO`, la imagen queda en `procesados` sirviéndose desde ahí y el evento queda en log/auditoría.
5. El comportamiento post-extracción no cambia: la imagen sigue pasando a `procesados` al extraer, y el monitor no re-encola archivos (dedup por SHA-256).
6. La sección "Reportes por mes" lista los meses con registros enviados (incluidos los migrados desde Sheets); cada registro tiene detalle accesible con su imagen visible (ruta autenticada dueño/admin) o fallback "sin imagen".
7. La descarga `.xlsx` trae pestaña `Julio-2026`, headers idénticos a Sheets y los registros de ese mes.
8. La migración desde "Reporte de gastos 2026" carga los históricos y actuales en la BD externa de forma idempotente (re-ejecutar no duplica) sin tocar el spreadsheet.
9. Todos los quality gates locales en verde; sin consumo de tokens de IA; sin residuos sintéticos en ninguna base ni filesystem.
