# Evidence Report — skill-fase1-nucleo

> **Skill:** `skill-fase1-nucleo`
> **Fase:** `fase1`
> **Timestamp:** `{iso8601}`
> **Estado:** `[PASADO | FALLADO | PARCIAL]`
> **Duracion:** `{duration}`

---

## Resumen Ejecutivo

{One-paragraph summary of Fase 1 execution: all 5 sub-skills executed in order, their results, quality gate outcome, and whether the core is ready for Fase 2.}

---

## Metricas Consolidadas

| Metrica | Valor |
|---|---|
| Skills ejecutados | 5 |
| Skills pasados | {N} |
| Skills fallados | {N} |
| Total verificaciones | {N} |
| Verificaciones pasadas | {N} |
| Verificaciones fallidas | {N} |
| Tablas PostgreSQL creadas | {N} |
| Endpoints de autenticacion | {N} |
| Cobertura de tests | {N}% |
| Errores | {N} |
| Advertencias | {N} |

---

## Resultados por Skill

### 1. skill-database

| Metrica | Valor |
|---|---|
| Estado | {status} |
| Tablas creadas | {N} |
| Migraciones | {N} |
| Indices | {N} |
| Duracion | {duration} |

### 2. skill-authentication

| Metrica | Valor |
|---|---|
| Estado | {status} |
| Usuarios creados | {N} |
| Algoritmo hash | Argon2id |
| Sesiones configuradas | {si/no} |
| Rate limiting | {si/no} |
| Duracion | {duration} |

### 3. skill-folder-monitor

| Metrica | Valor |
|---|---|
| Estado | {status} |
| Carpetas monitoreadas | {N} |
| Intervalo sondeo | 5s |
| Bloqueos SMB manejados | {si/no} |
| Validacion EXIF | {si/no} |
| Duracion | {duration} |

### 4. skill-fifo-queue

| Metrica | Valor |
|---|---|
| Estado | {status} |
| Exclusion mutua | {si/no} |
| Recuperacion tras reinicio | {si/no} |
| Atomicidad | {si/no} |
| Prevencion multi-worker | {si/no} |
| Duracion | {duration} |

### 5. skill-image-extraction

| Metrica | Valor |
|---|---|
| Estado | {status} |
| JSON valido % | {N}% |
| Prompt version | {version} |
| Campos extraidos | 5 |
| Timeout configurado | {N}s |
| Duracion | {duration} |

---

## Puerta de Calidad

| Verificacion | Estado | Detalle |
|---|---|---|
| Dependencias sincronizadas (`uv sync --frozen`) | {status} | {detail} |
| Formato y lint (`ruff`) | {status} | {detail} |
| Tipos estaticos (`mypy`) | {status} | {detail} |
| Tests unitarios (>=90%) | {status} | {coverage}% |
| Tests de integracion | {status} | {detail} |
| Seguridad de dependencias | {status} | {detail} |
| Escaneo de secretos | {status} | {detail} |

---

## Artefactos Generados

| Archivo | Tipo | Skill |
|---|---|---|
| `evidence/fase1/schema-postgresql.json` | report | database |
| `evidence/fase1/schema-postgresql.md` | report | database |
| `evidence/fase1/sistema-autenticacion.json` | report | authentication |
| `evidence/fase1/sistema-autenticacion.md` | report | authentication |
| `evidence/fase1/monitor-carpetas.json` | report | folder-monitor |
| `evidence/fase1/monitor-carpetas.md` | report | folder-monitor |
| `evidence/fase1/cola-fifo.json` | report | fifo-queue |
| `evidence/fase1/cola-fifo.md` | report | fifo-queue |
| `evidence/fase1/extraccion-imagenes.json` | report | image-extraction |
| `evidence/fase1/extraccion-imagenes.md` | report | image-extraction |
| `evidence/fase1/resumen-fase1.json` | report | fase1-nucleo |
| `evidence/fase1/resumen-fase1.md` | report | fase1-nucleo |

---

## Errores (si los hay)

| Codigo | Skill | Mensaje |
|---|---|---|
| `ERR_XXX` | {skill} | {description} |

---

## Advertencias (si las hay)

- {warning}

---

## Proximos Pasos

1. Obtener autorizacion GATE manual para Fase 1
2. Si Fase 1 aprobada, iniciar `skill-fase2-interfaz`
3. Planificar despliegue de tablas en entorno de produccion
4. Verificar que modelo Ollama responde consistentemente

---

## Precondiciones al Inicio

```json
{
  "fase0_completed": true,
  "branch": "arnes",
  "postgresql_accessible": true,
  "ollama_running": true,
  "modelo_seleccionado": "{qwen3-vl:2b|qwen3-vl:4b}",
  "uv_version": "{version}"
}
```

---

*Reporte generado automaticamente por el arnes Gastos IA v1.0*
