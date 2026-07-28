"""Cola FIFO de procesamiento — un solo worker para Ollama.

Garantiza procesamiento secuencial estricto:
- Solo una imagen en ANALIZANDO a la vez
- Orden FIFO por enqueued_at ASC, id ASC
- Reclamo atomico con SELECT FOR UPDATE SKIP LOCKED
- Recuperacion de trabajos ANALIZANDO tras reinicio
"""

import asyncio
import os
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ExpenseRecord, ExtractionRun, ProcessingQueue
from app.database.session import async_session

WORKER_ID = str(uuid.uuid4())[:8]
STALE_TIMEOUT_SECONDS = 600


async def claim_next_job(db: AsyncSession) -> ProcessingQueue | None:
    result = await db.execute(
        select(ProcessingQueue)
        .where(ProcessingQueue.status == "EN_COLA")
        .order_by(ProcessingQueue.enqueued_at.asc(), ProcessingQueue.id.asc())
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    job = result.scalar_one_or_none()

    if not job:
        return None

    job.status = "ANALIZANDO"
    job.claimed_at = datetime.now(timezone.utc)
    job.worker_id = WORKER_ID
    job.attempts += 1

    record_result = await db.execute(
        select(ExpenseRecord).where(ExpenseRecord.id == job.record_id)
    )
    record = record_result.scalar_one_or_none()
    if record:
        record.status = "ANALIZANDO"

    await db.commit()
    return job


async def recover_stale_jobs(db: AsyncSession) -> int:
    cutoff = datetime.now(timezone.utc).timestamp() - STALE_TIMEOUT_SECONDS
    stale_cutoff = datetime.fromtimestamp(cutoff, tz=timezone.utc)

    result = await db.execute(
        select(ProcessingQueue).where(
            ProcessingQueue.status == "ANALIZANDO",
            ProcessingQueue.claimed_at < stale_cutoff,
        )
    )
    stale_jobs = result.scalars().all()
    count = 0

    for job in stale_jobs:
        job.status = "EN_COLA"
        job.claimed_at = None
        job.worker_id = None

        record_result = await db.execute(
            select(ExpenseRecord).where(ExpenseRecord.id == job.record_id)
        )
        record = record_result.scalar_one_or_none()
        if record:
            record.status = "EN_COLA"
        count += 1

    if count:
        await db.commit()
    return count


async def complete_job(db: AsyncSession, job: ProcessingQueue, success: bool, error_msg: str | None = None) -> None:
    job.completed_at = datetime.now(timezone.utc)
    if success:
        job.status = "COMPLETADO"
        record_result = await db.execute(
            select(ExpenseRecord).where(ExpenseRecord.id == job.record_id)
        )
        record = record_result.scalar_one_or_none()
        if record:
            record.status = "LISTO_PARA_REVISION"
    else:
        job.status = "ERROR_PERMANENTE"
        job.last_error = error_msg
        record_result = await db.execute(
            select(ExpenseRecord).where(ExpenseRecord.id == job.record_id)
        )
        record = record_result.scalar_one_or_none()
        if record:
            record.status = "ERROR_PROCESAMIENTO"

    await db.commit()


async def worker_loop() -> None:
    print(f"[Worker] Iniciando worker FIFO {WORKER_ID}...")

    async with async_session() as db:
        recovered = await recover_stale_jobs(db)
        if recovered:
            print(f"[Worker] Recuperados {recovered} trabajos ANALIZANDO")

    while True:
        try:
            async with async_session() as db:
                job = await claim_next_job(db)
                if job:
                    print(f"[Worker] Reclamado job {job.record_id} (intento {job.attempts})")
                    success = await process_job(db, job)
                    await complete_job(db, job, success, None if success else "Error de procesamiento")
                else:
                    await asyncio.sleep(2)
        except Exception as e:
            print(f"[Worker] Error: {e}")
            await asyncio.sleep(5)


async def process_job(db: AsyncSession, job: ProcessingQueue) -> bool:
    """Procesar imagen con Ollama — placeholder, implementado en skill-image-extraction."""
    return True


if __name__ == "__main__":
    asyncio.run(worker_loop())
