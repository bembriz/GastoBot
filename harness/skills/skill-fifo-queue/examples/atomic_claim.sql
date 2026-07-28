-- Ejemplo de SQL para reclamo atomico FIFO con SELECT FOR UPDATE SKIP LOCKED
-- PRD §9.2: Solo 1 trabajo en ANALIZANDO, orden FIFO estricto

-- ============================================================
-- RECLAMO ATOMICO DEL SIGUIENTE TRABAJO
-- Esta query garantiza que:
-- 1. Solo 1 trabajo se reclama a la vez (LIMIT 1)
-- 2. Dos workers no reclaman el mismo (SKIP LOCKED)
-- 3. Orden FIFO (enqueued_at ASC, record_id ASC)
-- 4. Actualizacion atomica (status, claimed_at, worker_id)
-- ============================================================

WITH next_job AS (
    SELECT pq.id, pq.record_id
    FROM processing_queue pq
    WHERE pq.status = 'EN_COLA'
    ORDER BY pq.enqueued_at ASC, pq.record_id ASC
    LIMIT 1
    FOR UPDATE SKIP LOCKED
)
UPDATE processing_queue
SET 
    status = 'ANALIZANDO',
    claimed_at = NOW(),
    worker_id = :worker_id,
    attempts = attempts + 1
FROM next_job
WHERE processing_queue.id = next_job.id
RETURNING processing_queue.id, processing_queue.record_id, processing_queue.enqueued_at;


-- ============================================================
-- RECUPERACION DE TRABAJOS STALE (ANALIZANDO > 30 min)
-- Se ejecuta al inicio del worker tras un reinicio
-- ============================================================

UPDATE processing_queue
SET 
    status = 'EN_COLA',
    claimed_at = NULL,
    worker_id = NULL
WHERE status = 'ANALIZANDO'
  AND claimed_at < NOW() - INTERVAL '30 minutes'
RETURNING id, record_id;


-- ============================================================
-- PREVENCION DE MULTIPLES WORKERS (advisory lock)
-- ============================================================

-- Al iniciar el worker, adquirir lock exclusivo de sesion
-- Si retorna FALSE, otro worker ya tiene el lock
SELECT pg_try_advisory_lock(42);  -- 42 = lock ID fijo para el worker

-- El lock se libera automaticamente al terminar la sesion
-- No es necesario pg_advisory_unlock() explicito


-- ============================================================
-- VERIFICACION: Solo 1 trabajo en ANALIZANDO
-- ============================================================

-- Esta query debe retornar 1 o 0
SELECT COUNT(*) as analizando_count
FROM processing_queue
WHERE status = 'ANALIZANDO';


-- ============================================================
-- VERIFICACION: Orden FIFO de trabajos en EN_COLA
-- ============================================================

SELECT record_id, enqueued_at, status
FROM processing_queue
WHERE status = 'EN_COLA'
ORDER BY enqueued_at ASC, record_id ASC;
