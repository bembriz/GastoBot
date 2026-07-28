# Checklist — skill-quality-gate

## Pre-ejecución
- [ ] `uv` instalado y `uv --version` responde
- [ ] `uv.lock` presente en la raíz del proyecto
- [ ] `pyproject.toml` configurado con ruff, mypy, pytest, pytest-cov
- [ ] `gitleaks` instalado (`gitleaks --version`)
- [ ] Directorios `tests/unit/`, `tests/integration/`, `tests/e2e/` existen
- [ ] Base de datos de prueba `gastos_ia_test` accesible (para integración)
- [ ] Sin cambios sin commitear que puedan afectar resultados (o documentados)
- [ ] `.gitleaks.toml` configurado si hay allowlist necesaria

## Ejecución
- [ ] Paso 1: `uv sync --frozen` — OK
- [ ] Paso 2: `ruff check .` — sin errores
- [ ] Paso 2: `ruff format --check .` — ya formateado
- [ ] Paso 3: `mypy app/` — sin errores de tipo
- [ ] Paso 4: `pytest tests/unit/ --cov=app --cov-fail-under=90` — >= 90%, 0 fallos
- [ ] Paso 5: `pytest tests/integration/` — 0 fallos
- [ ] Paso 6: `pytest tests/e2e/` — 0 fallos
- [ ] Paso 7: `pip-audit` — 0 vulnerabilidades
- [ ] Paso 8: `gitleaks detect --source .` — sin leaks
- [ ] Paso 9: Resumen presentado al usuario
- [ ] Paso 9: Autorización "APROBADO" recibida

## Post-ejecución
- [ ] Evidencia JSON generada en `harness/evidence/{phase}/`
- [ ] Evidencia MD generada en `harness/evidence/{phase}/`
- [ ] Evidencia JSON válida contra schema
- [ ] Métricas de cada paso registradas (pass/fail, output)
- [ ] Cobertura final documentada
- [ ] Vulnerabilidades (si las hay) documentadas con justificación
- [ ] Secretos (si los hay) documentados con plan de remediación
- [ ] Timestamp de cada paso registrado
- [ ] Duración total del pipeline registrada
- [ ] Resultado final (APROBADO/RECHAZADO) documentado
