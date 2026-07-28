# Skill: skill-integration-tests

## Identity
Eres un ingeniero de testing de integración. Pruebas la interacción real entre componentes de la aplicación usando imágenes reales de `ejemplos/` y una base de datos PostgreSQL de prueba. Solo mockeas lo estrictamente inaccesible. Tu objetivo es validar que los módulos funcionan juntos correctamente en condiciones cercanas a producción.

## Context
Esta skill prueba el pipeline completo de procesamiento de Gastos IA con imágenes de tickets reales del directorio `ejemplos/` (~90 imágenes). Los tests de integración son el segundo escalón de la puerta de calidad (PRD §28) y validan que los componentes interactúan correctamente: detección → hash → cola → extracción → validación → transiciones de estado.

Se usa una base de datos PostgreSQL real de prueba (no la de producción). Ollama puede mockearse si no está disponible, pero las imágenes deben ser reales. Los tests deben cubrir edge cases: imágenes corruptas, duplicados, bloqueos SMB simulados, sin Internet, respuestas malformadas de Ollama, acceso concurrente a la cola.

## Preconditions
- `uv sync --frozen` ejecutado
- Tests unitarios pasando (cobertura >= 90%)
- PostgreSQL accesible para crear base de datos de prueba (`gastos_ia_test`)
- Directorio `ejemplos/` con imágenes reales de tickets
- Variables de entorno `GASTOSIA_DATABASE_*` apuntando a instancia de prueba (NO producción)
- Directorio `tests/integration/` existente con `conftest.py`
- Dependencias: pytest, pytest-asyncio, asyncpg, httpx

## Execution

### Step 1: Configurar base de datos de prueba
1. Verificar que existe una base de datos de prueba separada (`gastos_ia_test`):
   ```sql
   CREATE DATABASE gastos_ia_test OWNER gastos_app;
   ```
2. Aplicar migraciones para crear el esquema completo: `users`, `expense_records`, `image_files`, `extraction_runs`, `processing_queue`, `catalog_cache`, `sheet_sync`, `audit_events`, `system_settings`
3. Configurar `conftest.py` de integración:
   - Fixture `test_db_pool`: crea pool real de asyncpg a `gastos_ia_test`
   - Fixture `clean_db`: trunca todas las tablas antes de cada test
   - Fixture `test_app`: levanta FastAPI con TestClient usando la DB de prueba
   - Fixture `sample_images`: lista de rutas a imágenes de `ejemplos/`
   - Fixture `mock_ollama` (opcional): mockea llamadas HTTP a Ollama si no está disponible
4. Si Ollama está disponible, configurar para usar modelo real; si no, mock con respuestas predefinidas del PRD §7.2

### Step 2: Tests de pipeline de procesamiento

**2.1 Detección de imágenes**
- Simular copia de imagen a carpeta `pendientes/` de Ruben o Esme
- Verificar que el monitor detecta el archivo nuevo
- Verificar transición: DETECTADO → ESPERANDO_ARCHIVO_ESTABLE
- Verificar que archivos inestables (tamaño cambiante) permanecen en ESPERANDO_ARCHIVO_ESTABLE
- Verificar que tras 3 verificaciones estables pasa a EN_COLA
- Verificar asignación correcta de propietario según carpeta

**2.2 Cálculo de hash y duplicados**
- Calcular SHA-256 de imagen real
- Insertar mismo hash dos veces → verificar DUPLICADO_EXACTO
- Verificar que el duplicado se mueve a `errores/duplicados/`
- Verificar que el registro original se referencia en el duplicado
- Duplicado probable: misma fecha + monto + banco + descripción similar → verificar advertencia

**2.3 Cola FIFO**
- Insertar 5 imágenes en orden conocido
- Verificar orden de procesamiento por `enqueued_at` ASC, `record_id` ASC
- Verificar que solo una imagen está en ANALIZANDO a la vez
- Insertar imagen mientras otra se procesa → verificar que espera en EN_COLA
- Intentar enviar dos imágenes simultáneamente a Ollama → verificar que la segunda es rechazada
- Verificar atomicidad de `claim_next_job()` con locks

**2.4 Extracción multimodal**
- Enviar imagen real a Ollama (o mock)
- Verificar respuesta JSON válida con los 5 campos + confianza
- Verificar normalización: formato de fecha YYYY-MM-DD, monto float, banco string normalizado
- Verificar transición ANALIZANDO → LISTO_PARA_REVISION si confianza alta
- Verificar transición ANALIZANDO → REQUIERE_REVISION si confianza baja
- Probar con imagen corrupta → verificar ERROR_PROCESAMIENTO
- Probar con imagen no-ticket (paisaje, documento) → verificar manejo graceful
- Probar con respuesta Ollama malformada (no JSON, campos faltantes, tipos incorrectos)
- Probar timeout de Ollama → verificar manejo de timeout y reintento

**2.5 Transiciones de estado**
- Verificar todas las transiciones válidas del PRD §17
- Verificar que transiciones inválidas lanzan error
- Verificar persistencia de estado en PostgreSQL tras cada transición
- Probar reinicio simulado: trabajo en ANALIZANDO → kill worker → verificar recuperación a EN_COLA

**2.6 Operación con Google Sheets**
- Si hay conectividad a Google Sheets: probar inserción real en pestaña de prueba
- Si no hay conectividad: mockear gspread y verificar flujo offline
- Verificar PENDIENTE_DE_ENVIO cuando no hay Internet
- Verificar reintento al reconectar
- Verificar creación de pestaña mensual con 16 encabezados
- Verificar actualización de `_Control` tras envío
- Verificar actualización de registro existente
- Verificar movimiento entre meses (eliminar de mes anterior, insertar en nuevo)

### Step 3: Tests de concurrencia y resiliencia

**3.1 Acceso concurrente a la cola**
- Simular múltiples workers intentando `claim_next_job()` simultáneamente
- Verificar que solo uno obtiene el trabajo (PostgreSQL advisory lock)
- Verificar que los demás reciben None y esperan

**3.2 Bloqueos temporales SMB**
- Simular `PermissionError` al leer archivo → verificar que no se marca ERROR_PROCESAMIENTO
- Simular `OSError` con errno EACCES/EBUSY → verificar reintento en siguiente ciclo
- Verificar que el archivo permanece en ESPERANDO_ARCHIVO_ESTABLE

**3.3 Fallos de base de datos**
- Simular pérdida de conexión a PostgreSQL durante procesamiento
- Verificar que el worker maneja el error sin crash
- Verificar reintento de conexión con backoff
- Verificar que trabajos en ANALIZANDO se recuperan al reconectar

**3.4 Imágenes edge case**
- Imagen muy grande (>15 MB) → verificar rechazo con mensaje claro
- Imagen vacía (0 bytes) → verificar manejo sin crash
- Archivo no-imagen con extensión válida (.jpg falso) → verificar detección
- Imagen con EXIF corrupto → verificar que no bloquea el pipeline
- Imagen con orientación EXIF rotada → verificar corrección
- Muchas imágenes en `ejemplos/` → verificar que el monitor no se satura

### Step 4: Ejecutar tests de integración
1. Ejecutar:
   ```bash
   uv run pytest tests/integration/ -v --timeout=300
   ```
2. Verificar:
   - 0 tests fallidos
   - Tiempo total razonable (< 30 minutos con ~90 imágenes)
   - Sin deadlocks ni race conditions
   - Base de datos de prueba limpia al finalizar

### Step 5: Generar evidencia
1. Crear evidencia JSON y MD en `harness/evidence/{phase}/`
2. Incluir métricas:
   - Total de tests de integración
   - Tests pasados/fallidos
   - Imágenes procesadas exitosamente
   - Estados cubiertos
   - Tiempo promedio por imagen
   - Edge cases cubiertos

## Artifacts
- `harness/evidence/{phase}/integration-tests-{timestamp}.json`
- `harness/evidence/{phase}/integration-tests-{timestamp}.md`

## Quality Criteria
- 0 tests de integración fallidos
- Pipeline completo cubierto (detección → envío)
- Al menos 20 imágenes de `ejemplos/` procesadas en tests
- Todas las transiciones de estado válidas probadas
- Edge cases de concurrencia cubiertos
- Edge cases de archivos corruptos/no-válidos cubiertos
- Recuperación tras fallos cubierta
- Base de datos de prueba limpia tras ejecución
- Sin secretos en logs o evidencia
- Datos de prueba nunca escritos en base de datos de producción

## Edge Cases
- **Ollama no disponible:** mock completo con respuestas pregrabadas del PRD §7.2
- **PostgreSQL de prueba no accesible:** guiar creación de base `gastos_ia_test`
- **Imágenes de `ejemplos/` insuficientes:** generar imágenes sintéticas de tickets con Pillow
- **Timeout en procesamiento:** configurar `--timeout=300` por test; imágenes grandes pueden exceder
- **Colisión de tests paralelos:** usar `pytest-xdist` con `--dist=loadscope` o ejecutar secuencialmente
- **Limpieza de DB entre tests:** usar `TRUNCATE ... CASCADE` en fixture `clean_db` con orden correcto (evitar FK violations)
- **Variables de entorno para test db:** usar `.env.test` o fixture que sobreescribe `GASTOSIA_DATABASE_NAME=gastos_ia_test`

## References
- PRD §28 (Puerta de calidad)
- PRD §31.1 (Rendimiento)
- PRD §31.2 (Confiabilidad)
- PRD §9 (Flujo funcional)
- PRD §17 (Estados)
- PRD §15 (Duplicados)
- Related skills: `skill-unit-tests`, `skill-e2e-tests`, `skill-quality-gate`, `skill-database`, `skill-image-extraction`
