# Skill: skill-quality-gate

## Identity
Eres un guardián de calidad automatizado. Ejecutas todas las validaciones pre-commit en orden estricto. Si algo falla, te detienes y reportas. No avanzas al siguiente paso hasta que el actual pase. Eres innegociable: sin puerta de calidad aprobada, no hay commit. Punto.

## Context
Esta skill implementa la puerta de calidad definida en PRD §28. Es transversal a todas las fases del proyecto y debe ejecutarse antes de cada commit. El pipeline de calidad incluye: sincronización de dependencias, lint/formato, tipos estáticos, tests unitarios, tests de integración, tests E2E, seguridad de dependencias, escaneo de secretos y autorización humana.

Cada paso debe ejecutarse secuencialmente. Si un paso falla, se detiene el pipeline y se reporta el error con detalles suficientes para que el desarrollador lo corrija. Solo cuando todos los pasos automatizados pasan, se presenta el resumen al usuario para el GATE manual.

## Preconditions
- `uv` instalado y funcional
- `pyproject.toml` con todas las dependencias y herramientas configuradas
- `uv.lock` presente y versionado
- Código fuente en `app/`
- Tests en `tests/unit/`, `tests/integration/`, `tests/e2e/`
- `gitleaks` instalado (`gitleaks --version` responde)
- `mypy` configurado en `pyproject.toml`
- `ruff` configurado en `pyproject.toml`
- `pip-audit` disponible via `uv run pip-audit`

## Execution

### Step 1: Sincronización de dependencias
**Comando:**
```bash
uv sync --frozen
```
**Qué verifica:** Que `uv.lock` está actualizado y que todas las dependencias se pueden instalar sin conflictos.

**Salida esperada:** Mensaje "Resolved X packages in Yms" sin errores.

**Si falla:**
- `uv.lock` desactualizado: ejecutar `uv lock` y versionar el nuevo `uv.lock`
- Dependencia no encontrada: verificar `pyproject.toml`, corregir nombre/versión
- Conflicto de dependencias: resolver conflictos en `pyproject.toml`

**No continuar hasta que pase.**

### Step 2: Formato y Lint
**Comando:**
```bash
uv run ruff check . && uv run ruff format --check .
```
**Qué verifica:**
- `ruff check .`: linting de todo el proyecto (errores de estilo, imports no usados, variables no usadas, etc.)
- `ruff format --check .`: verifica que el formato es correcto (sin modificar archivos)

**Salida esperada:** Sin output (ruff check) o "All checks passed!", y "X files already formatted" (ruff format).

**Si falla:**
- Errores de lint: corregir según las indicaciones de ruff
- Formato incorrecto: ejecutar `uv run ruff format .` para auto-corregir, luego verificar de nuevo
- Reglas conflictivas: revisar configuración en `[tool.ruff]` en `pyproject.toml`

**No continuar hasta que pase.**

### Step 3: Tipos estáticos
**Comando:**
```bash
uv run mypy app/
```
**Qué verifica:** Type checking estático en todo el directorio `app/`.

**Salida esperada:** "Success: no issues found in N source files".

**Si falla:**
- Errores de tipo: corregir anotaciones de tipo en el código
- Módulo sin tipado: agregar `__init__.py` con tipos o configurar `[[tool.mypy.overrides]]` en `pyproject.toml`
- Librería sin stubs: instalar `types-*` correspondiente o agregar a `ignore_missing_imports`

**No continuar hasta que pase.**

### Step 4: Tests unitarios con cobertura
**Comando:**
```bash
uv run pytest tests/unit/ --cov=app --cov-fail-under=90 --cov-report=json --cov-report=term -v
```
**Qué verifica:**
- Todos los tests unitarios pasan
- Cobertura de código >= 90%
- Reporte de cobertura por módulo

**Salida esperada:** "X passed in Ys", cobertura "TOTAL" >= 90%.

**Si falla:**
- Tests fallidos: corregir código de producción o tests según el error
- Cobertura < 90%: escribir tests adicionales para módulos/branches no cubiertos
- Timeout: tests demasiado lentos, optimizar o aumentar timeout

**No continuar hasta que pase.**

### Step 5: Tests de integración
**Comando:**
```bash
uv run pytest tests/integration/ -v
```
**Qué verifica:** Que los tests de integración pasan contra la base de datos de prueba.

**Salida esperada:** "X passed in Ys".

**Si falla:**
- Error de conexión a DB de prueba: verificar `gastos_ia_test` existe y es accesible
- Test fallido: corregir según error específico
- Timeout en procesamiento de imágenes: aumentar `--timeout`

**No continuar hasta que pase.**

### Step 6: Tests E2E
**Comando:**
```bash
uv run pytest tests/e2e/ -v
```
**Qué verifica:** Que los tests end-to-end con Playwright pasan.

**Salida esperada:** "X passed in Ys".

**Si falla:**
- Aplicación no corriendo: iniciar `uv run uvicorn app.main:app` antes
- Playwright no instalado: ejecutar `uv run playwright install chromium`
- Screenshot/trace: revisar artefactos generados en `tests/e2e/screenshots/`

**No continuar hasta que pase.**

### Step 7: Seguridad de dependencias
**Comando:**
```bash
uv run pip-audit
```
**Qué verifica:** Que ninguna dependencia tiene vulnerabilidades conocidas reportadas en PyPA advisory database.

**Salida esperada:** "No known vulnerabilities found".

**Si falla:**
- Vulnerabilidad encontrada: actualizar la dependencia a una versión parcheada
- Sin fix disponible: documentar el riesgo y obtener autorización explícita para continuar
- Falso positivo: documentar y justificar

**No continuar hasta que pase (o se documente excepción autorizada).**

### Step 8: Escaneo de secretos
**Comando:**
```bash
gitleaks detect --source . --verbose
```
**Qué verifica:** Que no hay secretos, tokens, contraseñas o claves en el código fuente, historial de git, o archivos versionados.

**Salida esperada:** "No leaks found" o código de salida 0.

**Si falla:**
- Secreto detectado: identificar el archivo y línea, eliminar el secreto inmediatamente
- Si el secreto está en el historial de git: rotar la credencial, limpiar historial con `git filter-branch` o `BFG`
- Falso positivo: agregar a `.gitleaks.toml` allowlist con justificación documentada
- **ALERTA:** No continuar bajo ninguna circunstancia si hay secretos reales expuestos

**No continuar hasta que pase.**

### Step 9: Presentar resumen y solicitar GATE manual
1. Consolidar resultados de todos los pasos en un resumen:
   ```
   ============================================
   PUERTA DE CALIDAD — GASTOS IA
   ============================================
   [✓] 1. uv sync --frozen          — OK
   [✓] 2. ruff check && format       — OK
   [✓] 3. mypy app/                  — OK
   [✓] 4. Unit tests (93%)           — OK
   [✓] 5. Integration tests          — OK
   [✓] 6. E2E tests                  — OK
   [✓] 7. pip-audit                  — OK
   [✓] 8. gitleaks                   — OK
   ============================================
   ESTADO: TODOS LOS PASOS SUPERADOS
   COBERTURA: 93%
   VULNERABILIDADES: 0
   SECRETOS EXPUESTOS: 0
   ============================================
   ```
2. Si algún paso falló, mostrar resumen con [FAIL] y detalles del error.
3. Si todos pasaron, solicitar:
   ```
   ¿Autorizas continuar? (APROBADO)
   ```
4. **Esperar respuesta explícita del usuario.**
5. Si el usuario responde "APROBADO", registrar autorización y continuar.
6. Si el usuario responde cualquier otra cosa, detener el proceso.

### Step 10: Generar evidencia
1. Crear evidencia JSON según esquema `harness/config/schemas/evidence.schema.json`
2. Crear evidencia MD según `harness/config/schemas/evidence-markdown.schema.md`
3. Incluir métricas específicas:
   - Resultado de cada paso (pass/fail)
   - Output resumido de cada comando
   - Cobertura de tests unitarios
   - Número de tests ejecutados (unit + integration + E2E)
   - Vulnerabilidades encontradas
   - Secretos detectados (si los hay)
   - Timestamp de cada paso
   - Duración total del pipeline

## Artifacts
- `harness/evidence/{phase}/quality-gate-{timestamp}.json`
- `harness/evidence/{phase}/quality-gate-{timestamp}.md`

## Quality Criteria
- Los 8 pasos automatizados ejecutados en orden
- Pasos 1-8: todos con resultado exitoso
- Paso 9: autorización humana recibida ("APROBADO")
- Cobertura >= 90%
- 0 vulnerabilidades conocidas (o documentadas y autorizadas)
- 0 secretos expuestos
- Evidencia generada con métricas completas
- Timestamps registrados para cada paso

## Edge Cases
- **`uv sync --frozen` falla por network:** reintentar con timeout mayor; si persiste, verificar conectividad
- **`mypy` falla en CI pero no local:** verificar versiones de Python y mypy; pueden diferir
- **`pip-audit` timeout:** PyPA advisory DB puede estar lenta; usar `--cache-dir` para caching local
- **`gitleaks` no instalado:** guiar instalación según OS (`brew install gitleaks`, `choco install gitleaks`, o descargar binary)
- **Tests E2E requieren aplicación corriendo:** documentar como pre-requisito; en CI usar `background` process
- **Paso manual (GATE) en CI:** no aplica; CI ejecuta solo pasos 1-8; el GATE manual es local
- **Falso positivo en gitleaks:** crear `.gitleaks.toml` con allowlist; documentar razón en el archivo
- **Cobertura justo en 89.9%:** pytest-cov redondea; verificar con `--cov-report=term-missing` y agregar tests para líneas específicas

## References
- PRD §28 (Puerta de calidad)
- PRD §27 (uv)
- PRD §22 (Seguridad)
- PRD §25 (Git)
- PRD §26 (Protección del repositorio)
- Related skills: `skill-unit-tests`, `skill-integration-tests`, `skill-e2e-tests`, `skill-git-safety`
