# Evidence Report — skill-fifo-queue

> **Skill:** `skill-fifo-queue`
> **Fase:** `fase1`
> **Timestamp:** `{iso8601}`
> **Estado:** `[PASADO | FALLADO | PARCIAL]`
> **Duracion:** `{duration}`

---

## Resumen Ejecutivo

{Summary: FIFO queue implemented with SELECT FOR UPDATE SKIP LOCKED, single worker enforcement, stale job recovery, and state audit.}

---

## Metricas

| Metrica | Valor |
|---|---|
| Total de verificaciones | {N} |
| Pasadas | {N} |
| Fallidas | {N} |
| Max trabajos ANALIZANDO simultaneos | 1 |
| Orden procesamiento | FIFO (enqueued_at ASC, record_id ASC) |
| Timeout recuperacion stale | 30 min |
| Maximo intentos automaticos | 3 |
| Trabajos recuperados en pruebas | {N} |
| Errores | {N} |
| Advertencias | {N} |

---

## Verificaciones

### Pre-ejecucion

| # | Verificacion | Estado | Detalle |
|---|---|---|---|
| C1 | Tabla `processing_queue` con indice FIFO | {status} | ix_processing_queue_status_enqueued |
| C2 | `skill-folder-monitor` completado | {status} | Trabajos se encolan |
| C3 | Dependencias SQLAlchemy async | {status} | async session factory |

### Ejecucion — Reclamo atomico

| # | Verificacion | Estado | Detalle |
|---|---|---|---|
| C1 | SELECT FOR UPDATE SKIP LOCKED | {status} | Query SQL verificada |
| C2 | Orden FIFO (enqueued_at, record_id) | {status} | ASC ambos |
| C3 | LIMIT 1 | {status} | Solo 1 trabajo reclamado |
| C4 | Actualizacion atomica (status, claimed_at, worker_id) | {status} | En misma transaccion |
| C5 | RETURNING clause | {status} | Retorna trabajo reclamado |

### Ejecucion — Exclusion mutua

| # | Verificacion | Estado | Detalle |
|---|---|---|---|
| C1 | Lock file o advisory lock | {status} | /tmp/gastosia-worker.lock |
| C2 | Segundo worker detecta lock | {status} | Se niega a iniciar |
| C3 | Mensaje informativo | {status} | "Otro worker ya esta corriendo" |

### Ejecucion — Recuperacion

| # | Verificacion | Estado | Detalle |
|---|---|---|---|
| C1 | `recover_stale_jobs()` existe | {status} | Funcion implementada |
| C2 | Timeout configurable | {status} | Default 30 min |
| C3 | ANALIZANDO > timeout -> EN_COLA | {status} | claimed_at, worker_id reseteados |
| C4 | Se ejecuta en startup | {status} | Antes del worker |

### Ejecucion — Transiciones

| # | Verificacion | Estado | Detalle |
|---|---|---|---|
| C1 | EN_COLA -> ANALIZANDO | {status} | Reclamo exitoso |
| C2 | ANALIZANDO -> LISTO_PARA_REVISION | {status} | Confianza >= 0.70 |
| C3 | ANALIZANDO -> REQUIERE_REVISION | {status} | Confianza < 0.70 |
| C4 | ANALIZANDO -> ERROR_PROCESAMIENTO | {status} | Fallo en extraccion |
| C5 | ANALIZANDO -> EN_COLA | {status} | Recuperacion stale |
| C6 | Sincronizacion expense_records.status | {status} | Mismo estado en ambas tablas |
| C7 | audit_events registrado | {status} | event_type='STATE_TRANSITION' |

### Ejecucion — Pruebas

| # | Verificacion | Estado | Detalle |
|---|---|---|---|
| C1 | Orden FIFO: 3 trabajos en orden | {status} | enqueued_at verificado |
| C2 | Solo 1 ANALIZANDO | {status} | SELECT count(*) WHERE status='ANALIZANDO' = 1 |
| C3 | Doble reclamo prevenido | {status} | SKIP LOCKED evita colision |
| C4 | Recuperacion stale jobs | {status} | Trabajo vuelve a EN_COLA |
| C5 | Segundo worker rechazado | {status} | Lock file funciona |
| C6 | Reintento manual admin | {status} | POST /retry -> EN_COLA |
| C7 | Max 3 intentos automaticos | {status} | 4to fallo queda en ERROR |

---

## Artefactos Generados

| Archivo | Tipo | Descripcion |
|---|---|---|
| `app/queue/worker.py` | source | Worker FIFO |
| `app/queue/lock.py` | source | Prevencion multi-worker |
| `scripts/validation/test_fifo_queue.py` | script | Pruebas de cola |
| `harness/evidence/fase1/cola-fifo.json` | report | Evidencia JSON |
| `harness/evidence/fase1/cola-fifo.md` | report | Evidencia Markdown |

---

## Errores (si los hay)

| Codigo | Mensaje |
|---|---|
| `ERR_XXX` | {description} |

---

## Advertencias (si las hay)

- {warning}

---

## Proximos Pasos

1. Proceder con `skill-image-extraction`
2. Monitorear tiempo de procesamiento en condiciones reales
3. Ajustar timeout de stale jobs segun datos reales

---

## Precondiciones al Inicio

```json
{
  "database_skill_completed": true,
  "folder_monitor_skill_completed": true,
  "fifo_index_exists": true,
  "sqlalchemy_async_configured": true
}
```

---

*Reporte generado automaticamente por el arnes Gastos IA v1.0*
