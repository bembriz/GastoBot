# Evidence Report — UAT Instructions

> **Skill:** `skill-uat-instructions`  
> **Fase:** `{phase}`  
> **Timestamp:** `{iso8601}`  
> **Estado:** `[PASADO | FALLADO]`  
> **Duración:** `{duration}`  

---

## Resumen Ejecutivo

{One-paragraph summary: instructivo HITL generado, número de escenarios cubiertos, entradas/salidas documentadas.}

---

## Métricas

| Métrica | Valor |
|---|---|
| Escenarios UAT | {N} |
| Pasos documentados | {N} |
| Entradas esperadas documentadas | {N} |
| Salidas esperadas documentadas | {N} |
| Criterios pass/fail | {N} |

---

## Escenarios UAT Cubiertos

| # | Escenario | Usuario | Pasos | Entradas | Salidas | Pass/Fail |
|---|---|---|---|---|---|---|
| 1 | Login Ruben | Ruben | {N} | {N} | {N} | {criteria} |
| 2 | Login Esme | Esme | {N} | {N} | {N} | {criteria} |
| 3 | Login fallido + bloqueo | Ruben | {N} | {N} | {N} | {criteria} |
| 4 | Pipeline imagen completo | Ruben | {N} | {N} | {N} | {criteria} |
| 5 | Pipeline imagen Esme | Esme | {N} | {N} | {N} | {criteria} |
| 6 | Validación formulario | Ruben | {N} | {N} | {N} | {criteria} |
| 7 | Duplicado exacto | Ruben | {N} | {N} | {N} | {criteria} |
| 8 | HTMX polling | Ambos | {N} | {N} | {N} | {criteria} |
| 9 | Catálogos (admin) | Ruben | {N} | {N} | {N} | {criteria} |
| 10 | Catálogos (bloqueado std.) | Esme | {N} | {N} | {N} | {criteria} |
| 11 | Historial | Ruben | {N} | {N} | {N} | {criteria} |
| 12 | Offline → online | Ruben | {N} | {N} | {N} | {criteria} |

---

## Verificaciones

### Pre-ejecución

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C1 | PRD sección 33 leída | {status} | {detail} |
| C2 | Ejemplos/imágenes disponibles | {status} | {detail} |

### Post-ejecución

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C1 | Manual generado (MD) | {status} | {path} |
| C2 | Todos los escenarios documentados | {status} | {N}/{N} |
| C3 | Entradas/salidas especificadas | {status} | {detail} |
| C4 | Criterios pass/fail definidos | {status} | {detail} |

---

## Artefactos Generados

| Archivo | Tipo | Descripción |
|---|---|---|
| `docs/UAT-Manual-Operativo.md` | Document | Manual HITL completo |
| `docs/UAT-Checklist.xlsx` | Spreadsheet | Checklist de verificación |

---

## Próximos Pasos

1. Entregar manual al equipo de QA
2. Ejecutar pruebas UAT siguiendo el instructivo
3. Reportar resultados en este template

---

*Reporte generado automáticamente por el arnés Gastos IA v1.0*
