# Skill: skill-fase0-tecnica

## Identity
Eres un ingeniero de validación técnica responsable de ejecutar la Fase 0 del proyecto Gastos IA. Actúas con rigor científico: mides, comparas, documentas y generas evidencia objetiva. No asumes nada sin verificarlo.

## Context
Esta skill valida la viabilidad técnica del proyecto antes de escribir código de producción. La Fase 0 es prerrequisito absoluto para todas las fases posteriores (Fases 1-5). Sin su aprobación, el proyecto no avanza.

Valida cinco pilares técnicos definidos en el PRD:
- **Benchmark de modelo multimodal** (PRD §7, §32): comparar Qwen3-VL 2B vs 4B con 50+ imágenes de `ejemplos/`
- **PostgreSQL** (PRD §18): conectividad, creación de base/usuario, permisos
- **Google Sheets** (PRD §13): autenticación, lectura/escritura, pestañas
- **Importación de históricos** (PRD §13.4): carga de datos existentes a `_Control`
- **Mecanismo de secretos** (PRD §19): variables de entorno, `.env.example`, validación

## Preconditions
- Rama `arnes` activa y limpia
- PRD v1.2 aprobado (archivo `docs/PRD_Gastos_IA_v1_2.md` presente)
- Directorio `ejemplos/` con al menos 50 imágenes de comprobantes
- Ollama instalado y accesible (`ollama --version` responde)
- Servicio PostgreSQL accesible en la red
- Credencial de Google Sheets (JSON de cuenta de servicio) disponible fuera del repositorio
- Dependencias Python gestionadas con `uv` (`uv --version` responde)
- AGENTS.md cargado y fase Fase 0 en estado `pending`
- Directorio `harness/evidence/fase0/` existente

## Execution

### Step 0: Actualizar estado de fase
1. Leer el YAML frontmatter de `AGENTS.md`
2. Verificar que `phases.fase0.status == "pending"`
3. Cambiar `phases.fase0.status` a `"in_progress"`
4. Actualizar `harness/PROGRESS.md` con timestamp de inicio y ETA (8 horas estimadas)

### Step 1: Validación del mecanismo de secretos
**Objetivo:** Verificar que `.env.example` existe, que todas las variables requeridas están listadas sin valores reales, y que el mecanismo `os.environ.get()` funciona.

1. Leer `.env.example` y verificar que contiene las 14 variables listadas en PRD §19.2
2. Verificar que ninguna variable tiene valor real (solo `=` o valor placeholder como `changeme`)
3. Crear un script temporal `scripts/validation/validate_secrets.py` que:
   - Cargue variables desde un archivo `.env` de prueba (NO del repo)
   - Verifique que `os.environ.get("GASTOSIA_*")` funciona para cada variable
   - Valide que `GASTOSIA_SESSION_SECRET` tiene longitud >= 32 caracteres
   - Valide que `GASTOSIA_DATABASE_PASSWORD` no está vacío
   - Enmascare secretos en cualquier output (reemplazar con `***`)
   - Falle explícitamente si falta una variable obligatoria
4. Ejecutar el script con un `.env` de prueba creado en `/tmp/` (NO en el repositorio)
5. Eliminar el `.env` de prueba inmediatamente después
6. Generar evidencia `validacion-secretos.json` y `validacion-secretos.md`

### Step 2: Validación de PostgreSQL
**Objetivo:** Confirmar conectividad, permisos para crear base de datos y tablas, y ejecución de queries básicas.

1. Crear script `scripts/validation/validate_postgresql.py` que:
   - Use `asyncpg` (instalado via `uv add asyncpg` si es necesario)
   - Conecte usando variables de entorno `GASTOSIA_DATABASE_*`
   - Verifique versión de PostgreSQL (`SELECT version()`)
   - Intente crear base de datos `gastos_ia` (con `IF NOT EXISTS`)
   - Intente crear usuario `gastos_app` (con `IF NOT EXISTS`)
   - Otorgue permisos: CONNECT en `gastos_ia`, CREATE en schema `public`
   - Cree una tabla de prueba con columnas básicas y la elimine
   - Verifique que `pg_stat_activity` muestra la conexión
2. Ejecutar el script
3. Generar evidencia `validacion-postgresql.json` y `validacion-postgresql.md`
4. **Edge case:** Si PostgreSQL no es accesible, documentar error exacto (timeout, auth fail, host unreachable) y sugerir diagnóstico de red

### Step 3: Validación de Google Sheets
**Objetivo:** Verificar autenticación, acceso al spreadsheet, y capacidad de leer/escribir en pestañas.

1. Crear script `scripts/validation/validate_sheets.py` que:
   - Use `gspread` con cuenta de servicio (ruta desde `GASTOSIA_GOOGLE_CREDENTIALS_PATH`)
   - Abra el spreadsheet por `GASTOSIA_GOOGLE_SPREADSHEET_ID`
   - Liste todas las pestañas existentes
   - Lea `_Control` si existe, o la cree con los encabezados mínimos (PRD §13.4)
   - Cree una pestaña de prueba `_Test_Fase0` con 16 encabezados (PRD §13.1)
   - Escriba una fila de prueba con datos dummy
   - Lea la fila de vuelta y verifique integridad
   - Elimine la pestaña `_Test_Fase0`
   - Verifique permisos de la cuenta de servicio (debe ser editor, no owner)
2. Ejecutar el script
3. Generar evidencia `validacion-sheets.json` y `validacion-sheets.md`
4. **Edge case:** Si el spreadsheet no existe o la cuenta no tiene acceso, documentar el error y sugerir verificar la consola de Google Cloud

### Step 4: Importación de históricos
**Objetivo:** Cargar datos históricos de gastos a la hoja `_Control` para que sirvan como base de consecutivos.

1. Determinar fuente de históricos (preguntar al usuario si no está definida: archivo CSV, hoja de Sheets existente, o entrada manual)
2. Crear script `scripts/validation/import_historicos.py` que:
   - Lea la fuente de datos históricos
   - Valide campos mínimos: fecha, monto, descripción, grupo, consecutivo
   - Genere `image_hash` como `historic-{md5(row_key)}` (placeholder, no hash real de imagen)
   - Inserte cada registro en `_Control` con los campos definidos en PRD §13.4
   - Detecte y reporte duplicados por `image_hash` o `group_code + consecutive`
   - Calcule el consecutivo máximo por grupo existente
   - Reporte total de registros importados, duplicados encontrados, consecutivos máximos
3. Ejecutar el script con confirmación visual del usuario antes de insertar
4. Generar evidencia `importacion-historicos.json` y `importacion-historicos.md`
5. **Edge case:** Si no hay históricos, documentar que se parte de cero y que los consecutivos iniciarán en 1

### Step 5: Benchmark de modelos (Qwen3-VL 2B vs 4B)
**Objetivo:** Comparar objetivamente ambos modelos con 50+ imágenes reales del directorio `ejemplos/`.

1. Verificar que ambos modelos están disponibles en Ollama:
   ```bash
   ollama list | grep qwen3-vl
   ```
   Si no están, descargarlos:
   ```bash
   ollama pull qwen3-vl:2b
   ollama pull qwen3-vl:4b
   ```
2. Crear script `scripts/validation/benchmark_modelos.py` que:
   - Recorra todas las imágenes en `ejemplos/` (extensiones: .jpg, .jpeg, .png, .webp)
   - Para cada imagen, ejecute inferencia con AMBOS modelos (2B y 4B)
   - Use el prompt estructurado definido en PRD §7.2 (~/prompts/expense_extraction.md si existe, o el inline)
   - Mida tiempo de procesamiento por imagen por modelo
   - Valide JSON de respuesta (estructura, tipos de datos)
   - Compare campos extraídos contra ground truth (si existe archivo `ejemplos/ground_truth.json` o similar)
   - Si no hay ground truth, evalúe solo: validez JSON, coherencia de tipos, tiempos
   - Registre consumo de RAM del proceso ollama durante inferencia (via `ollama ps` o `/proc`)
   - Calcule métricas agregadas: exactitud por campo, % JSON válido, tiempo promedio, RAM pico
3. Ejecutar el script (puede tomar ~2-4 horas con 50 imágenes x 2 modelos)
4. Generar tabla comparativa en el reporte
5. Generar evidencia `benchmark-modelos.json` y `benchmark-modelos.md`
6. **Decisión requerida:** Si 4B supera los umbrales del PRD §32, recomendar 4B. Si no, recomendar 2B o evaluar alternativas.

### Step 6: Cierre de fase
1. Verificar que existen los 10 archivos de evidencia:
   - `evidence/fase0/benchmark-modelos.json`
   - `evidence/fase0/benchmark-modelos.md`
   - `evidence/fase0/validacion-postgresql.json`
   - `evidence/fase0/validacion-postgresql.md`
   - `evidence/fase0/validacion-sheets.json`
   - `evidence/fase0/validacion-sheets.md`
   - `evidence/fase0/importacion-historicos.json`
   - `evidence/fase0/importacion-historicos.md`
   - `evidence/fase0/validacion-secretos.json`
   - `evidence/fase0/validacion-secretos.md`
2. Ejecutar `skill-quality-gate` para verificar lint, tipos, tests
3. Cambiar `phases.fase0.status` a `"completed"` en AGENTS.md
4. Actualizar `harness/PROGRESS.md`
5. Presentar resumen ejecutivo al usuario con:
   - Modelo recomendado (2B vs 4B)
   - Resultados de cada validación (pass/fail)
   - Riesgos identificados
   - Solicitar GATE manual para avanzar a Fase 1

## Artifacts
- `harness/evidence/fase0/benchmark-modelos.json`
- `harness/evidence/fase0/benchmark-modelos.md`
- `harness/evidence/fase0/validacion-postgresql.json`
- `harness/evidence/fase0/validacion-postgresql.md`
- `harness/evidence/fase0/validacion-sheets.json`
- `harness/evidence/fase0/validacion-sheets.md`
- `harness/evidence/fase0/importacion-historicos.json`
- `harness/evidence/fase0/importacion-historicos.md`
- `harness/evidence/fase0/validacion-secretos.json`
- `harness/evidence/fase0/validacion-secretos.md`
- `scripts/validation/validate_secrets.py` (temporal, no versionado si contiene paths)
- `scripts/validation/validate_postgresql.py`
- `scripts/validation/validate_sheets.py`
- `scripts/validation/import_historicos.py`
- `scripts/validation/benchmark_modelos.py`

## Quality Criteria
- Las 14 variables de entorno del PRD §19.2 están documentadas en `.env.example`
- PostgreSQL acepta conexión, creación de BD/usuario, y queries básicas
- Google Sheets API autentica, lee y escribe correctamente
- Los históricos se importan sin duplicados y con consecutivos correctos
- El benchmark cubre >= 50 imágenes con ambos modelos
- El modelo recomendado cumple los umbrales mínimos del PRD §32 (o se documenta el fallback)
- Todos los scripts de validación se ejecutan sin errores de importación
- Ningún secreto, token o contraseña aparece en logs, outputs o archivos generados
- Evidencia JSON válida contra `harness/config/schemas/evidence.schema.json`
- Evidencia MD sigue `harness/config/schemas/evidence-markdown.schema.md`

## Edge Cases
- **Ollama no instalado:** guiar instalación con `curl -fsSL https://ollama.com/install.sh | sh`
- **Modelo no descargable por falta de espacio:** verificar disco (`df -h`), sugerir limpieza
- **PostgreSQL en host Windows sin acceso desde VM:** verificar firewall, `pg_hba.conf`, bind address
- **Google Sheets API quota exceeded:** implementar backoff exponencial, documentar límites
- **Imágenes corruptas en ejemplos/:** saltar con warning, no detener el benchmark
- **Ground truth incompleto o ausente:** evaluar solo métricas estructurales, documentar limitación
- **Tiempo de benchmark > 4 horas:** ofrecer benchmark reducido (25 imágenes) con flag `--quick`
- **Credencial de Google en ubicación no estándar:** validar que `GASTOSIA_GOOGLE_CREDENTIALS_PATH` apunta a archivo JSON válido

## References
- PRD §7 (Modelo multimodal), §7.2 (Salida esperada), §32 (Métricas de calidad)
- PRD §18 (PostgreSQL)
- PRD §13 (Google Sheets), §13.4 (Pestañas técnicas)
- PRD §19 (Variables de entorno y secretos)
- PRD §34 (Fases — Fase 0)
- Related skills: `skill-quality-gate`, `skill-git-safety`, `skill-database`, `skill-image-extraction`
