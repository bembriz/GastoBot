# Checklist — skill-unit-tests

## Pre-ejecución
- [ ] `uv sync --frozen` ejecutado sin errores
- [ ] `tests/unit/` existe con subdirectorios para cada módulo de `app/`
- [ ] `tests/unit/conftest.py` existe con fixtures para async mock DB, Ollama, gspread
- [ ] pytest, pytest-cov, pytest-asyncio, pytest-mock en dependencias de desarrollo
- [ ] `asyncio_mode = "auto"` configurado en `pyproject.toml`
- [ ] Variables de entorno de prueba usan placeholders, no valores reales
- [ ] Ningún test importa credenciales reales o usa conexiones vivas

## Ejecución
- [ ] Tests `app/database/`: pool, connection, execute, fetch, transacciones, locks, health check
- [ ] Tests `app/auth/`: Argon2id, sesiones, cookies, bloqueo, permisos, rate limiting
- [ ] Tests `app/users/`: CRUD, soft delete, roles, cambio de contraseña
- [ ] Tests `app/images/`: extensiones, SHA-256, duplicados, EXIF, estabilidad, SMB locks
- [ ] Tests `app/expenses/`: estados, transiciones, consecutivos, descripción final, sincronización precio/total
- [ ] Tests `app/api/`: endpoints, status codes, auth required, validation, error handlers
- [ ] Tests `app/sheets/`: catálogos, pestañas mensuales, inserción, actualización, offline, rate limit
- [ ] Tests de ramas de error (no solo happy paths)
- [ ] Tests con null/empty/None inputs en todas las funciones
- [ ] Tests de race conditions (ANALIZANDO exclusivo, lock acquisition)
- [ ] Tests de recuperación tras error (transacciones, rollback)
- [ ] Cobertura total >= 90%
- [ ] Cada submódulo con cobertura individual >= 90%
- [ ] 0 tests fallidos

## Post-ejecución
- [ ] `coverage.json` generado
- [ ] `htmlcov/` generado
- [ ] Evidencia JSON generada en `harness/evidence/{phase}/`
- [ ] Evidencia MD generada en `harness/evidence/{phase}/`
- [ ] Evidencia JSON válida contra `harness/config/schemas/evidence.schema.json`
- [ ] Evidencia MD siguiendo `harness/config/schemas/evidence-markdown.schema.md`
- [ ] Métricas por módulo documentadas en evidencia
- [ ] Módulos con cobertura < 90% identificados con plan de acción
- [ ] Ningún secreto expuesto en outputs de test, logs o evidencia
