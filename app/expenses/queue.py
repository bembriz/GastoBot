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
from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ExpenseRecord, ExtractionRun, ImageFile, ProcessingQueue
from app.database.session import async_session
from app.expenses import activity
from app.expenses.extraction import extract_from_image

WORKER_ID = str(uuid.uuid4())[:8]
STALE_TIMEOUT_SECONDS = 600


def _move_to_procesados(original_path: str, owner_folder: str) -> str | None:
    try:
        src_dir = os.path.dirname(original_path)
        # GASTOSIA_PROCESSED_DIR permite fijar el destino (p. ej. unidad
        # secundaria en lenovosrv). Si no se define, se conserva el
        # comportamiento historico: hermano de la carpeta del dueño.
        configured_dir = os.environ.get("GASTOSIA_PROCESSED_DIR", "").strip()
        procesados_dir = configured_dir or os.path.join(os.path.dirname(src_dir), "procesados")
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


async def claim_next_job(
    db: AsyncSession, owner_id: uuid.UUID | None = None
) -> ProcessingQueue | None:
    stmt = (
        select(ProcessingQueue)
        .where(ProcessingQueue.status == "EN_COLA")
        .order_by(ProcessingQueue.enqueued_at.asc(), ProcessingQueue.id.asc())
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    if owner_id is not None:
        stmt = stmt.where(
            ProcessingQueue.record_id.in_(
                select(ExpenseRecord.id).where(ExpenseRecord.owner_id == owner_id)
            )
        )
    result = await db.execute(stmt)
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


async def reset_job_to_en_cola(db: AsyncSession, job: ProcessingQueue) -> None:
    job.status = "EN_COLA"
    job.claimed_at = None
    job.worker_id = None

    record_result = await db.execute(select(ExpenseRecord).where(ExpenseRecord.id == job.record_id))
    record = record_result.scalar_one_or_none()
    if record:
        record.status = "EN_COLA"

    await db.commit()


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
                job: ProcessingQueue | None = None
                # F1: seccion corta [decide + reclama] bajo el MISMO lock que
                # POST /expenses/process — sin este mutex un POST entre el
                # is_busy() y el commit del claim dejaba 2 ANALIZANDO (R008).
                # El lock NO se sostiene durante la extraccion (no conviene
                # bloquear al worker durante minutos un lote manual).
                async with activity.get_claim_lock():
                    if not activity.is_busy():
                        job = await claim_next_job(db)
                if job:
                    print(f"[Worker] Reclamado job {job.record_id} (intento {job.attempts})")
                    try:
                        success = await process_job(db, job)
                        await complete_job(
                            db, job, success, None if success else "Error de procesamiento"
                        )
                    except Exception as e:
                        # F3: un fallo NO debe dejar el job ANALIZANDO (el
                        # siguiente claim daria 2 ANALIZANDO). Igual que
                        # process_batch: evento de error + reset + re-raise
                        # (el re-raise cae al handler externo -> sleep 5 y
                        # limita el reintento inmediato).
                        print(f"[Worker] Error procesando job {job.record_id}: {e}")
                        activity.push_event("error", f"Error procesando job: {e}")
                        try:
                            await reset_job_to_en_cola(db, job)
                        except Exception as reset_err:
                            print(f"[Worker] Error reseteando job: {reset_err}")
                            activity.push_event("error", f"Error reseteando job: {reset_err}")
                        raise
                elif activity.is_busy():
                    await asyncio.sleep(1)
                else:
                    await asyncio.sleep(2)
        except Exception as e:
            print(f"[Worker] Error: {e}")
            await asyncio.sleep(5)


async def process_job(
    db: AsyncSession,
    job: ProcessingQueue,
    engine: str | None = None,
    on_event: Callable[[str, str], None] | None = None,
) -> bool:
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
    extract_on_event = (lambda msg: on_event("extraccion", msg)) if on_event is not None else None
    extraction = await extract_from_image(
        image_path, preferred_engine=engine, on_event=extract_on_event
    )

    used_engine = extraction.get("engine") or "?"
    if extraction.get("error_message"):
        print(f"[Worker] ERROR [{used_engine}] {extraction['error_message']}", flush=True)
    elif not extraction.get("is_valid_json"):
        print(f"[Worker] ADVERTENCIA [{used_engine}]: JSON invalido", flush=True)
    else:
        print(
            f"[Worker] OK [{used_engine}] en {extraction.get('elapsed_ms', 0)}ms",
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


async def process_batch(
    engine: str,
    owner_id: uuid.UUID | None,
    on_event: Callable[[str, str], None],
) -> int:
    """Procesa secuencialmente todos los jobs EN_COLA (opcionalmente de un dueno).

    Garantiza un solo ANALIZANDO a la vez (R008). Devuelve el numero de jobs
    procesados con exito. Si un job lanza excepcion, se emite evento de error,
    el job vuelve a EN_COLA (no queda atascado) y la excepcion se relanza;
    activity.clear_batch() siempre corre en el finally.
    """
    from app.expenses import activity

    processed = 0
    try:
        while True:
            async with async_session() as db:
                job = await claim_next_job(db, owner_id=owner_id)
                if not job:
                    break
                rec_result = await db.execute(
                    select(ExpenseRecord).where(ExpenseRecord.id == job.record_id)
                )
                rec = rec_result.scalar_one_or_none()
                fname = (rec.source_filename if rec else None) or str(job.record_id)
                activity.set_batch(str(job.record_id), fname, engine)
                on_event("info", f"Reclamado: {fname} (intento {job.attempts})")
                try:
                    ok = await process_job(db, job, engine=engine, on_event=on_event)
                    await complete_job(db, job, ok, None if ok else "Error de procesamiento")
                except Exception as e:
                    on_event("error", f"Error procesando {fname}: {e}")
                    try:
                        await reset_job_to_en_cola(db, job)
                    except Exception as reset_err:
                        on_event("error", f"No se pudo reiniciar el job {fname}: {reset_err}")
                    raise
                if ok:
                    processed += 1
        return processed
    finally:
        activity.clear_batch()


if __name__ == "__main__":
    asyncio.run(worker_loop())
