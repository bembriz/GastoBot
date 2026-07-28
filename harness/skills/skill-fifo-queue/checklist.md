# Checklist — skill-fifo-queue

## Pre-ejecucion
- [ ] `skill-database` completado (tabla `processing_queue` con indice FIFO)
- [ ] `skill-folder-monitor` completado (trabajos se encolan correctamente)
- [ ] Indice `ix_processing_queue_status_enqueued` existe
- [ ] Rama `arnes` activa

## Ejecucion — Worker
- [ ] `app/queue/worker.py` creado
- [ ] `FifoWorker` con `claim_next_job()`, `process_job()`, `run()`
- [ ] `claim_next_job()` usa SELECT FOR UPDATE SKIP LOCKED
- [ ] Orden de reclamo: enqueued_at ASC, record_id ASC
- [ ] `claim_next_job()` LIMIT 1 (solo un trabajo a la vez)
- [ ] `claim_next_job()` actualiza status, claimed_at, worker_id atomicamente
- [ ] `process_job()` llama a extraccion de imagen
- [ ] `process_job()` maneja exito (LISTO_PARA_REVISION/REQUIERE_REVISION)
- [ ] `process_job()` maneja error (ERROR_PROCESAMIENTO)
- [ ] `run()` es bucle infinito con sleep(5) en cola vacia
- [ ] `current_job` rastrea trabajo activo

## Ejecucion — Exclusion mutua
- [ ] `app/queue/lock.py` creado
- [ ] Lock file en `/tmp/gastosia-worker.lock` o advisory lock
- [ ] Segundo worker detecta lock y se niega a iniciar
- [ ] Mensaje claro: "Otro worker ya esta corriendo"

## Ejecucion — Recuperacion
- [ ] `recover_stale_jobs()` implementado
- [ ] Timeout configurable (default 30 min)
- [ ] Trabajos ANALIZANDO > timeout vuelven a EN_COLA
- [ ] `claimed_at` y `worker_id` se resetean
- [ ] `recover_stale_jobs()` se ejecuta en startup del worker

## Ejecucion — Transiciones de estado
- [ ] EN_COLA -> ANALIZANDO (reclamo)
- [ ] ANALIZANDO -> LISTO_PARA_REVISION (confianza >= 0.70)
- [ ] ANALIZANDO -> REQUIERE_REVISION (confianza < 0.70)
- [ ] ANALIZANDO -> ERROR_PROCESAMIENTO (fallo)
- [ ] ANALIZANDO -> EN_COLA (recuperacion stale)
- [ ] Cada transicion actualiza processing_queue Y expense_records
- [ ] Cada transicion registra audit_event

## Ejecucion — Integracion
- [ ] Worker inicia en startup de FastAPI
- [ ] `recover_stale_jobs()` se ejecuta antes del worker
- [ ] Endpoint `POST /expenses/{id}/retry` para admin
- [ ] Reintento solo en ERROR_PROCESAMIENTO

## Ejecucion — Pruebas
- [ ] `scripts/validation/test_fifo_queue.py` ejecutado
- [ ] Orden FIFO respetado (primer EN_COLA = primer ANALIZANDO)
- [ ] Solo 1 trabajo en ANALIZANDO a la vez
- [ ] SKIP LOCKED previene doble reclamo
- [ ] Recuperacion de stale jobs funcional
- [ ] Segundo worker rechazado
- [ ] Reintento manual funcional
- [ ] Estados sincronizados entre tablas

## Post-ejecucion
- [ ] Evidencia `cola-fifo.json` generada
- [ ] Evidencia `cola-fifo.md` generada
- [ ] `skill-quality-gate` ejecutado
- [ ] `harness/PROGRESS.md` actualizado
