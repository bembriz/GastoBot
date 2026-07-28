# Evidence Report — Quality Gate

> **Skill:** `skill-quality-gate`  
> **Fase:** `{phase}`  
> **Timestamp:** `{iso8601}`  
> **Estado:** `[PASADO | FALLADO]`  
> **Duración:** `{duration}`  

---

## Resumen Ejecutivo

{One-paragraph: pasos ejecutados, cuáles pasaron/fallaron, decisión final (APROBADO/RECHAZADO).}

---

## Resultados por Paso

| # | Paso | Comando | Estado | Tiempo | Detalle |
|---|---|---|---|---|---|
| 1 | Dependencias sincronizadas | `uv sync --frozen` | {status} | {N}s | {detail} |
| 2 | Formato y lint | `uv run ruff check . && uv run ruff format --check .` | {status} | {N}s | {detail} |
| 3 | Tipos estáticos | `uv run mypy app/` | {status} | {N}s | {detail} |
| 4 | Tests unitarios (>=90%) | `uv run pytest tests/unit/ --cov=app --cov-fail-under=90` | {status} | {N}s | {detail} |
| 5 | Tests de integración | `uv run pytest tests/integration/` | {status} | {N}s | {detail} |
| 6 | Tests E2E | `uv run pytest tests/e2e/` | {status} | {N}s | {detail} |
| 7 | Seguridad dependencias | `uv run pip-audit` | {status} | {N}s | {detail} |
| 8 | Escaneo de secretos | `gitleaks detect --source . --verbose` | {status} | {N}s | {detail} |
| 9 | Autorización humana | Manual GATE | {status} | — | {detail} |

---

## Métricas Consolidadas

| Métrica | Valor | Objetivo | Status |
|---|---|---|---|
| Lint errors | {N} | 0 | {status} |
| Type errors | {N} | 0 | {status} |
| Unit test coverage | {N}% | >= 90% | {status} |
| Unit tests passed | {N}/{N} | 100% | {status} |
| Integration tests passed | {N}/{N} | 100% | {status} |
| E2E tests passed | {N}/{N} | 100% | {status} |
| Vulnerability alerts | {N} | 0 | {status} |
| Secrets found | {N} | 0 | {status} |

---

## Verificaciones

### Pre-ejecución

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C1 | Código compilable/importable | {status} | {detail} |
| C2 | Herramientas instaladas (ruff, mypy, pytest, gitleaks) | {status} | {detail} |

### Post-ejecución

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C1 | Todos los pasos pasaron | {status} | {N}/{N} |
| C2 | GATE humano recibido | {status} | {detail} |

---

## Errores

| Código | Paso | Mensaje |
|---|---|---|
| {code} | {step} | {message} |

---

## Decisión Final

**{APROBADO / RECHAZADO}**

{Razón de la decisión}

---

## Próximos Pasos

1. Si APROBADO: proceder con skill-git-safety para commit
2. Si RECHAZADO: corregir pasos fallidos y re-ejecutar

---

*Reporte generado automáticamente por el arnés Gastos IA v1.0*
