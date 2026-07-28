# Evidence Report — Git Safety

> **Skill:** `skill-git-safety`  
> **Fase:** `{phase}`  
> **Timestamp:** `{iso8601}`  
> **Estado:** `[PASADO | FALLADO]`  
> **Duración:** `{duration}`  

---

## Resumen Ejecutivo

{One-paragraph: branch actual, archivos modificados, resultado de escaneo de secretos, mensaje de commit propuesto, autorización pendiente/recibida.}

---

## Resumen de Diff

| Métrica | Valor |
|---|---|
| **Branch** | `{branch}` |
| **Archivos modificados** | {N} |
| **Líneas agregadas** | +{N} |
| **Líneas eliminadas** | -{N} |
| **Commits pendientes** | {N} |

---

## Archivos por Tipo

| Tipo | Archivos | Cambios |
|---|---|---|
| Código fuente (app/) | {N} | {N} |
| Tests | {N} | {N} |
| Plantillas (templates/) | {N} | {N} |
| Configuración | {N} | {N} |
| Documentación | {N} | {N} |
| Scripts | {N} | {N} |
| Skills (harness/) | {N} | {N} |

---

## Archivos Modificados

| Archivo | Estado | Líneas +/− |
|---|---|---|
| `path/to/file` | `added/modified/deleted` | +{N}/-{N} |
| ... | ... | ... |

---

## Escaneo de Secretos

| Herramienta | Resultado | Hallazgos |
|---|---|---|
| gitleaks | {status} | {N} encontrados |

### Hallazgos (si los hay)

| Archivo | Línea | Tipo | Acción |
|---|---|---|---|
| {file} | {line} | {type} | {action} |

---

## Verificaciones de Seguridad

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C1 | No estás en main | {status} | Branch: {branch} |
| C2 | No hay .env reales staged | {status} | {detail} |
| C3 | No hay credentials/ staged | {status} | {detail} |
| C4 | No hay *.pem/*.key/*.p12 staged | {status} | {detail} |
| C5 | No hay service-account-*.json staged | {status} | {detail} |
| C6 | Escaneo gitleaks limpio | {status} | {N} hallazgos |
| C7 | .gitignore cubre patrones sensibles | {status} | {detail} |

---

## Mensaje de Commit Propuesto

```
{type}({scope}): {description}

{body}
```

---

## Autorización

| Estado | Detalle |
|---|---|
| GATE | **PENDIENTE** — Esperando "AUTORIZO COMMIT" |
| Push | **PENDIENTE** — Requiere autorización independiente |

---

## Próximos Pasos

1. Revisar diff manualmente
2. Responder "AUTORIZO COMMIT" para proceder
3. Autorización independiente requerida para push

---

*Reporte generado automáticamente por el arnés Gastos IA v1.0*
