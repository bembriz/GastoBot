"""Cola FIFO de procesamiento — un solo worker para extraccion multimodal.

Garantiza procesamiento secuencial estricto:
- Solo una imagen en ANALIZANDO a la vez
- Orden FIFO por enqueued_at ASC, id ASC
- Reclamo atomico con SELECT FOR UPDATE SKIP LOCKED
- Recuperacion de trabajos ANALIZANDO tras reinicio
"""

import asyncio
import contextlib
import os
import shutil
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ExpenseRecord, ExtractionRun, ImageFile, ProcessingQueue
from app.database.session import async_session
from app.expenses.extraction import extract_from_image

WORKER_ID = str(uuid.uuid4())[:8]
STALE_TIMEOUT_SECONDS = 600


def _move_to_procesados(original_path: str, owner_folder: str) -> str | None:
    try:
        src_dir = os.path.dirname(original_path)
        procesados_dir = os.path.join(os.path.dirname(src_dir), "procesados")
        os.makedirs(procesados_dir, exist_ok=True)
        filename = os.path.basename(original_path)
        dst = os.path.join(procesados_dir, filename)
        shutil.copy2(original_path, dst)
        os.remove(original_path)
        print(f"[Worker] Movido a procesados: {filename}")
        return dst
    except Exception as e:
        print(f"[Worker] Error moviendo archivo: {e}")
        return None


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
    job.claimed_at = datetime.now(UTC)
    job.worker_id = WORKER_ID
    job.attempts += 1

    record_result = await db.execute(select(ExpenseRecord).where(ExpenseRecord.id == job.record_id))
    record = record_result.scalar_one_or_none()
    if record:
        record.status = "ANALIZANDO"

    await db.commit()
    return job


async def recover_stale_jobs(db: AsyncSession) -> int:
    cutoff = datetime.now(UTC).timestamp() - STALE_TIMEOUT_SECONDS
    stale_cutoff = datetime.fromtimestamp(cutoff, tz=UTC)

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


async def complete_job(
    db: AsyncSession, job: ProcessingQueue, success: bool, error_msg: str | None = None
) -> None:
    job.completed_at = datetime.now(UTC)
    if success:
        job.status = "COMPLETADO"
        record_result = await db.execute(
            select(ExpenseRecord).where(ExpenseRecord.id == job.record_id)
        )
        record = record_result.scalar_one_or_none()
        if record:
            record.status = "REQUIERE_REVISION"
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
                    await complete_job(
                        db, job, success, None if success else "Error de procesamiento"
                    )
                else:
                    await asyncio.sleep(2)
        except Exception as e:
            print(f"[Worker] Error: {e}")
            await asyncio.sleep(5)


async def process_job(db: AsyncSession, job: ProcessingQueue) -> bool:
    record_result = await db.execute(select(ExpenseRecord).where(ExpenseRecord.id == job.record_id))
    record = record_result.scalar_one_or_none()
    if not record:
        return False

    image_result = await db.execute(select(ImageFile).where(ImageFile.record_id == record.id))
    image = image_result.scalar_one_or_none()
    if not image:
        return False

    image_path = image.optimized_path or image.original_path
    if not image_path or not os.path.exists(image_path):
        return False

    print(f"[Worker] Analizando imagen: {image_path}")
    extraction = await extract_from_image(image_path)

    engine = extraction.get("engine") or "?"
    if extraction.get("error_message"):
        print(f"[Worker] ERROR [{engine}] {extraction['error_message']}", flush=True)
    elif not extraction.get("is_valid_json"):
        print(f"[Worker] ADVERTENCIA [{engine}]: JSON invalido", flush=True)
    else:
        print(
            f"[Worker] OK [{engine}] en {extraction.get('elapsed_ms', 0)}ms",
            flush=True,
        )

    extraction_run = ExtractionRun(
        record_id=record.id,
        model_name=extraction.get("engine") or "desconocido",
        prompt_version="1.0",
        raw_response=extraction.get("raw_response", ""),
        parsed_json=extraction.get("parsed_json"),
        is_valid_json=extraction.get("is_valid_json", False),
        elapsed_ms=extraction.get("elapsed_ms", 0),
        error_message=extraction.get("error_message"),
    )
    db.add(extraction_run)

    if extraction.get("is_valid_json") and extraction.get("parsed_json"):
        parsed = extraction["parsed_json"]
        if parsed.get("transaction_date"):
            with contextlib.suppress(ValueError, TypeError):
                record.transaction_date = datetime.strptime(parsed["transaction_date"], "%Y-%m-%d")
        if parsed.get("amount"):
            record.amount = parsed["amount"]
        record.ticket_description = parsed.get("ticket_description")
        record.bank = parsed.get("bank")
        record.transaction_type = parsed.get("transaction_type")
        record.confidence_json = parsed.get("confidence")

    success = extraction.get("parsed_json") is not None

    if success and image.original_path:
        new_path = _move_to_procesados(image.original_path, image.owner_folder)
        if new_path:
            image.original_path = new_path

    await db.commit()
    return success


if __name__ == "__main__":
    asyncio.run(worker_loop())
