# Evidencia: Despliegue de Aplicacion

- **Skill:** skill-installer
- **Fase:** 4
- **Timestamp:** 2026-07-29T15:15:00Z
- **Status:** passed

## Resumen

Aplicacion FastAPI desplegada exitosamente en la VM GastosIA mediante rsync desde la maquina de desarrollo. Dependencias instaladas con `uv sync --frozen` para produccion y `uv sync --extra dev` para desarrollo.

## Checks

| ID | Descripcion | Status |
|----|------------|--------|
| DEPLOY-01 | Directorio /opt/gastos-ia creado | passed |
| DEPLOY-02 | Codigo copiado via rsync | passed |
| DEPLOY-03 | uv sync --frozen (prod) | passed |
| DEPLOY-04 | uv sync --extra dev | passed |
| DEPLOY-05 | FastAPI importable | passed |

## Detalles

- **Path:** /opt/gastos-ia
- **Owner:** gastos-admin:gastos-admin
- **Python:** 3.12.3
- **uv:** 0.12.0
- **FastAPI:** 0.140.13
- **Datos transferidos:** ~1.7 MB
- **Exclusiones:** .git, __pycache__, .venv, .mypy_cache, .ruff_cache, .pytest_cache

## Observaciones

- No existen tests unitarios en el repositorio (se generaran en Fase 5).
- ruff reporta 283 errores preexistentes en el codigo (no introducidos por el despliegue).
- El directorio tests/ no existe en el repositorio.
