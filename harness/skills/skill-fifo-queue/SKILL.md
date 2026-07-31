# Skill: skill-fifo-queue

## Identity
Eres un ingeniero de sistemas distribuidos especializado en colas de procesamiento y concurrencia. Implementas una cola FIFO persistente con exclusion mutua estricta, recuperacion ante fallos, y prevencion de condiciones de carrera. La integridad de la cola es mas importante que la velocidad.

## Context
Esta skill es el mecanismo mas critico del sistema. Garantiza que solo UNA imagen se envie a Ollama a la vez, respetando orden FIFO estricto, incluso tras reinicios del servicio o del servidor.

Requisitos del PRD §9.2:
- Solo un trabajo en estado ANALIZANDO en cualquier momento
- Orden: `enqueued_at ASC`, `record_id ASC` para desempates
- Reclamo atomico del siguiente trabajo (PostgreSQL advisory lock o SELECT FOR UPDATE SKIP LOCKED)
- Recuperacion de trabajos ANALIZANDO tras reinicio (stale jobs)
- Prevencion de multiples workers (lock file o DB lock)
- Persistencia total en PostgreSQL (sobrevive reinicios)
- Transiciones de estado auditadas

## Preconditions
- `skill-database` completado (tabla `processing_queue` con indice `ix_processing_queue_status_enqueued`)
- `skill-folder-monitor` completado (el monitor encola trabajos con estado EN_COLA)
- Tabla `processing_queue` tiene columnas: id, record_id, enqueued_at, claimed_at, completed_at, worker_id, status, priority, attempts
- `uv` con dependencias: SQLAlchemy async (ya instalado)
- Rama `arnes` activa

## Execution

### Step 1: Crear el worker FIFO
1. Crear `app/queue/__init__.py`
2. Crear `app/queue/worker.py`:

**Clase `FifoWorker`:**
```python
class FifoWorker:
    def __init__(self, db_session_factory, worker_id: str):
        self.db_factory = db_session_factory
        self.worker_id = worker_id
        self.running = False
        self.current_job: Optional[UUID] = None
    
    async def claim_next_job(self) -> Optional[processing_queue]:
        """Reclama atomicamente el siguiente trabajo EN_COLA."""
        # Usar SELECT FOR UPDATE SKIP LOCKED para atomicidad
        # Orden: enqueued_at ASC, record_id ASC
        # Solo 1 fila (LIMIT 1)
        # Actualizar: status='ANALIZANDO', claimed_at=NOW(), worker_id=self.worker_id
        # Retornar el trabajo reclamado o None
    
    async def process_job(self, job: processing_queue):
        """Procesa un trabajo: llama a Ollama, actualiza estados."""
        # 1. Actualizar expense_records.status = 'ANALIZANDO'
        # 2. Llamar a skill-image-extraction (extraer datos de imagen)
        # 3. Actualizar expense_records con datos extraidos
        # 4. Cambiar estado a LISTO_PARA_REVISION o REQUIERE_REVISION
        # 5. Marcar job como completado: completed_at=NOW(), status='COMPLETADO'
    
    async def run(self):
        """Bucle principal del worker."""
        self.running = True
        while self.running:
            job = await self.claim_next_job()
            if job:
                self.current_job = job.record_id
                try:
                    await self.process_job(job)
                except Exception as e:
                    # Manejar error: estado a ERROR_PROCESAMIENTO
                    # Registrar en audit_events
                    pass
                finally:
                    self.current_job = None
            else:
                await asyncio.sleep(5)  # Esperar si no hay trabajos
```

### Step 2: Implementar reclamo atomico
Esta es la parte MAS CRITICA. Debe usar SQL que garantice que dos workers no reclaman el mismo trabajo.

**Opcion A: SELECT FOR UPDATE SKIP LOCKED (recomendada)**
```sql
WITH next_job AS (
    SELECT pq.id, pq.record_id
    FROM processing_queue pq
    WHERE pq.status = 'EN_COLA'
    ORDER BY pq.enqueued_at ASC, pq.record_id ASC
    LIMIT 1
    FOR UPDATE SKIP LOCKED
)
UPDATE processing_queue
SET status = 'ANALIZANDO',
    claimed_at = NOW(),
    worker_id = :worker_id,
    attempts = attempts + 1
FROM next_job
WHERE processing_queue.id = next_job.id
RETURNING processing_queue.*;
```

**Opcion B: Advisory lock (alternativa)**
```sql
-- Adquirir lock exclusivo
SELECT pg_try_advisory_xact_lock(42);  -- lock ID fijo para la cola
-- Reclamar trabajo
-- ...
-- Lock se libera al hacer COMMIT
```

Implementar la Opcion A (SKIP LOCKED es mas simple y no requiere manejo manual de locks).

### Step 3: Prevenir multiples workers
Crear `app/queue/lock.py`:
1. Usar lock file en `/tmp/gastosia-worker.lock`:
   ```python
   import fcntl


   def acquire_worker_lock() -> bool:
       lock_file = open("/tmp/gastosia-worker.lock", "w")
       try:
           fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
           return True
       except BlockingIOError:
           return False
   ```
2. Alternativa: usar PostgreSQL advisory lock a nivel de sesion:
   ```sql
   SELECT pg_try_advisory_lock(1);  -- 1 = lock ID del worker
   ```
3. Si no se puede adquirir el lock, el worker debe salir con mensaje: "Otro worker ya esta corriendo"

### Step 4: Recuperacion de trabajos stale (ANALIZANDO tras reinicio)
Crear funcion `recover_stale_jobs()` que se ejecuta al inicio del worker:

```python
async def recover_stale_jobs(db: AsyncSession, timeout_minutes: int = 30):
    """
    Recupera trabajos que quedaron en ANALIZANDO tras un reinicio.

    Si un trabajo lleva > timeout_minutes en ANALIZANDO sin worker activo,
    asumir que el worker anterior murio y devolverlo a EN_COLA.
    """
    stale_threshold = datetime.utcnow() - timedelta(minutes=timeout_minutes)

    stale_jobs = await db.execute(
        update(ProcessingQueue)
        .where(ProcessingQueue.status == "ANALIZANDO", ProcessingQueue.claimed_at < stale_threshold)
        .values(status="EN_COLA", claimed_at=None, worker_id=None)
    )
    await db.commit()
    return stale_jobs.rowcount
```

### Step 5: Transiciones de estado
Implementar todas las transiciones validas:

```
EN_COLA -> ANALIZANDO (reclamo por worker)
ANALIZANDO -> LISTO_PARA_REVISION (extraccion exitosa, confianza >= 0.70)
ANALIZANDO -> REQUIERE_REVISION (extraccion exitosa, confianza < 0.70)
ANALIZANDO -> ERROR_PROCESAMIENTO (fallo en Ollama o parseo)
ANALIZANDO -> EN_COLA (recuperacion de stale job)
ERROR_PROCESAMIENTO -> EN_COLA (reintento manual por usuario)
```

Cada transicion debe:
1. Persistirse en `processing_queue.status`
2. Actualizar `expense_records.status` simultaneamente
3. Registrar `audit_events` (event_type='STATE_TRANSITION', old_state, new_state)

### Step 6: Integracion con el sistema
1. En `app/main.py`, en el evento `startup`:
   ```python
   @app.on_event("startup")
   async def start_worker():
       # Recuperar trabajos stale primero
       async with async_session() as db:
           recovered = await recover_stale_jobs(db)
           if recovered:
               logger.info(f"Recuperados {recovered} trabajos stale")
       
       # Iniciar worker
       worker = FifoWorker(async_session, worker_id=str(uuid4()))
       asyncio.create_task(worker.run())
   ```

### Step 7: Endpoint de reintento manual
Crear `POST /expenses/{record_id}/retry`:
- Solo admin (Ruben) puede reintentar
- Solo para registros en ERROR_PROCESAMIENTO
- Vuelve a EN_COLA (resetea `attempts` o lo incrementa)

### Step 8: Generar evidencia
1. Crear `scripts/validation/test_fifo_queue.py` que:
   - Pruebe que 2 trabajos EN_COLA se procesan en orden FIFO
   - Pruebe que solo 1 trabajo esta en ANALIZANDO a la vez
   - Pruebe que SELECT FOR UPDATE SKIP LOCKED previene doble reclamo
   - Simule reinicio: dejar trabajo en ANALIZANDO, reiniciar worker, verificar recuperacion
   - Pruebe que un segundo worker no puede iniciar (lock file o advisory lock)
   - Pruebe reintento manual de ERROR_PROCESAMIENTO
2. Ejecutar y generar evidencia

## Artifacts
- `app/queue/__init__.py`
- `app/queue/worker.py`
- `app/queue/lock.py`
- `scripts/validation/test_fifo_queue.py`
- `harness/evidence/fase1/cola-fifo.json`
- `harness/evidence/fase1/cola-fifo.md`

## Quality Criteria
- Solo 1 trabajo en ANALIZANDO en cualquier momento (verificar con query)
- Orden FIFO respetado: trabajos procesados en orden de enqueued_at
- Reclamo atomico: 2 workers simultaneos no reclaman el mismo trabajo
- Recuperacion: trabajos stale en ANALIZANDO vuelven a EN_COLA tras timeout
- Prevencion multi-worker: segundo worker detecta lock y se niega a iniciar
- Transiciones de estado auditadas en `audit_events`
- `processing_queue` y `expense_records` tienen estados sincronizados
- Worker maneja errores sin crashear (captura excepciones, sigue corriendo)

## Edge Cases
- **Worker crashea durante procesamiento:** el trabajo queda en ANALIZANDO; al reiniciar, `recover_stale_jobs` lo devuelve a EN_COLA
- **Dos workers inician simultaneamente:** lock file o advisory lock previene que el segundo inicie
- **DB connection loss durante reclamo:** la transaccion hace rollback, trabajo vuelve a EN_COLA
- **Ollama timeout (5 min):** worker captura TimeoutError, marca como ERROR_PROCESAMIENTO
- **Cola vacia:** worker espera 5s y vuelve a intentar (sin busy-waiting)
- **Trabajo con muchos intentos fallidos:** `attempts >= 3` -> dejar en ERROR_PROCESAMIENTO, no reintentar automaticamente
- **Reclamo simultaneo con SKIP LOCKED:** PostgreSQL garantiza que solo 1 sesion obtiene la fila

## References
- PRD §9.2 (Cola de procesamiento secuencial estricta - 10 reglas)
- PRD §17 (Estados y transiciones)
- PRD §31.2 (Confiabilidad - cola sobrevive reinicios)
- Related skills: `skill-database`, `skill-folder-monitor`, `skill-image-extraction`
