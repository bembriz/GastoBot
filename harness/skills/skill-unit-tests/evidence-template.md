# Evidence Report — Unit Tests

> **Skill:** `skill-unit-tests`  
> **Fase:** `{phase}`  
> **Timestamp:** `{iso8601}`  
> **Estado:** `[PASADO | FALLADO]`  
> **Duración:** `{duration}`  

---

## Resumen Ejecutivo

{One-paragraph summary: total tests executed, pass/fail ratio, coverage achieved, modules tested.}

---

## Métricas

| Métrica | Valor | Objetivo |
|---|---|---|
| Tests totales | {N} | — |
| Tests pasados | {N} | 100% |
| Tests fallidos | {N} | 0 |
| Cobertura total | {N}% | >= 90% |
| Cobertura de ramas | {N}% | >= 85% |

---

## Cobertura por Módulo

| Módulo | Statements | Missing | Coverage | Status |
|---|---|---|---|---|
| `app/api/` | {N} | {N} | {N}% | {pass/fail} |
| `app/auth/` | {N} | {N} | {N}% | {pass/fail} |
| `app/catalogs/` | {N} | {N} | {N}% | {pass/fail} |
| `app/database/` | {N} | {N} | {N}% | {pass/fail} |
| `app/expenses/` | {N} | {N} | {N}% | {pass/fail} |
| `app/images/` | {N} | {N} | {N}% | {pass/fail} |
| `app/sheets/` | {N} | {N} | {N}% | {pass/fail} |
| `app/users/` | {N} | {N} | {N}% | {pass/fail} |

---

## Verificaciones

### Pre-ejecución

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C1 | uv sync completado | {status} | {detail} |
| C2 | pytest instalado | {status} | {detail} |
| C3 | pytest-cov instalado | {status} | {detail} |
| C4 | Código fuente en app/ existe | {status} | {detail} |

### Ejecución

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C1 | Tests api/ pasan | {status} | {detail} |
| C2 | Tests auth/ pasan | {status} | {detail} |
| C3 | Tests catalogs/ pasan | {status} | {detail} |
| C4 | Tests database/ pasan | {status} | {detail} |
| C5 | Tests expenses/ pasan | {status} | {detail} |
| C6 | Tests images/ pasan | {status} | {detail} |
| C7 | Tests sheets/ pasan | {status} | {detail} |
| C8 | Tests users/ pasan | {status} | {detail} |

### Post-ejecución

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C1 | Cobertura >= 90% | {status} | {coverage}% |
| C2 | 0 tests fallidos | {status} | {N} fallidos |
| C3 | Reportes generados | {status} | {paths} |

---

## Artefactos Generados

| Archivo | Tipo | Descripción |
|---|---|---|
| `htmlcov/index.html` | Report | Coverage HTML report |
| `coverage.json` | Data | Coverage JSON data |
| `tests/unit/test_*.py` | Source | Test files created/updated |

---

## Errores

| Código | Mensaje |
|---|---|
| {code} | {message} |

---

## Próximos Pasos

1. Ejecutar skill-integration-tests
2. Si coverage < 90%, agregar tests para módulos con baja cobertura

---

*Reporte generado automáticamente por el arnés Gastos IA v1.0*
