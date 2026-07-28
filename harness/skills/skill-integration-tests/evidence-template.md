# Evidence Report — Integration Tests

> **Skill:** `skill-integration-tests`  
> **Fase:** `{phase}`  
> **Timestamp:** `{iso8601}`  
> **Estado:** `[PASADO | FALLADO]`  
> **Duración:** `{duration}`  

---

## Resumen Ejecutivo

{One-paragraph summary: integration scenarios tested, images used from ejemplos/, results achieved, edge cases verified.}

---

## Métricas

| Métrica | Valor |
|---|---|
| Escenarios totales | {N} |
| Escenarios pasados | {N} |
| Escenarios fallidos | {N} |
| Imágenes usadas | {N} de ejemplos/ |
| Tiempo promedio/escenario | {N}s |

---

## Escenarios Ejecutados

| # | Escenario | Estado | Imágenes | Tiempo | Detalle |
|---|---|---|---|---|---|
| 1 | Pipeline completo (detección → extracción → revisión) | {status} | {N} | {N}s | {detail} |
| 2 | Detección de duplicados (SHA-256) | {status} | {N} | {N}s | {detail} |
| 3 | Manejo de bloqueos SMB temporales | {status} | {N} | {N}s | {detail} |
| 4 | Cola FIFO (orden estricto) | {status} | {N} | {N}s | {detail} |
| 5 | Recuperación de trabajos ANALIZANDO | {status} | {N} | {N}s | {detail} |
| 6 | Operación sin Internet (offline) | {status} | {N} | {N}s | {detail} |
| 7 | Imágenes corruptas/inválidas | {status} | {N} | {N}s | {detail} |
| 8 | Concurrencia (múltiples imágenes) | {status} | {N} | {N}s | {detail} |
| 9 | Transiciones de estado completas | {status} | {N} | {N}s | {detail} |
| 10 | Respuesta malformada de Ollama | {status} | {N} | {N}s | {detail} |

---

## Resultados de Extracción (Muestra)

| Imagen | Fecha | Monto | Banco | Tipo | Confianza | OK |
|---|---|---|---|---|---|---|
| `PSAV-260209-1.jpeg` | 2026-02-09 | 700.00 | NU | Transferencia | 0.95 | {status} |
| `VAL-260207-1.jpeg` | ... | ... | ... | ... | ... | ... |

---

## Edge Cases Verificados

| Edge Case | Estado | Observación |
|---|---|---|
| Imagen vacía (0 bytes) | {status} | {detail} |
| Archivo no-imagen (.txt, .pdf) | {status} | {detail} |
| Imagen > 15 MB | {status} | {detail} |
| Carpetas vacías | {status} | {detail} |
| Pérdida de conexión PostgreSQL | {status} | {detail} |
| Ollama timeout | {status} | {detail} |

---

## Verificaciones

### Pre-ejecución

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C1 | Ejemplos/ contiene imágenes | {status} | {N} imágenes |
| C2 | PostgreSQL disponible | {status} | {detail} |
| C3 | Base de datos de test creada | {status} | {detail} |

### Post-ejecución

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C1 | 0 escenarios fallidos | {status} | {N} fallidos |
| C2 | 0 registros perdidos | {status} | {detail} |
| C3 | 0 duplicados incorrectos | {status} | {detail} |

---

## Artefactos Generados

| Archivo | Tipo | Descripción |
|---|---|---|
| `tests/integration/test_*.py` | Source | Tests de integración |
| `evidence/fase{phase}/integration-results-*.json` | Data | Resultados crudos |

---

## Errores

| Código | Mensaje |
|---|---|
| {code} | {message} |

---

## Próximos Pasos

1. Ejecutar skill-e2e-tests
2. Corregir escenarios fallidos antes de continuar

---

*Reporte generado automáticamente por el arnés Gastos IA v1.0*
