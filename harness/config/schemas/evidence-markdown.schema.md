# Evidence Report — Template

> **Skill:** `{skill-name}`  
> **Fase:** `{phase}`  
> **Timestamp:** `{iso8601}`  
> **Estado:** `[PASADO | FALLADO | PARCIAL]`  
> **Duración:** `{duration}`  

---

## Resumen Ejecutivo

{One-paragraph summary of what was done, what passed, what failed, and the overall assessment.}

---

## Métricas

| Métrica | Valor |
|---|---|
| Total de verificaciones | {N} |
| Pasadas | {N} |
| Fallidas | {N} |
| Cobertura (si aplica) | {N}% |
| Errores | {N} |
| Advertencias | {N} |

---

## Verificaciones

### Pre-ejecución

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C1 | {description} | {status} | {detail} |

### Ejecución

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C1 | {description} | {status} | {detail} |

### Post-ejecución

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C1 | {description} | {status} | {detail} |

---

## Artefactos Generados

| Archivo | Tipo | Descripción |
|---|---|---|
| `path/to/file` | `source/config/report` | What this file is |

---

## Errores (si los hay)

| Código | Mensaje |
|---|---|
| `ERR_XXX` | Descripción del error y resolución aplicada |

---

## Advertencias (si las hay)

- {warning 1}
- {warning 2}

---

## Próximos Pasos

1. {next step 1}
2. {next step 2}

---

## Precondiciones al Inicio

```json
{ snapshot of preconditions }
```

---

*Reporte generado automáticamente por el arnés Gastos IA v1.0*
