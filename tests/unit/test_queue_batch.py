"""Tests del filtro por dueno y del batch runner."""

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from app.database.models import ExpenseRecord, ExtractionRun, ImageFile, ProcessingQueue
from app.expenses import activity, queue

_created_record_ids: list[uuid.UUID] = []


@pytest_asyncio.fixture(autouse=True)
async def _cleanup_created_records(db_session):
    yield
    ids = list(_created_record_ids)
    _created_record_ids.clear()
    if ids:
        await db_session.execute(delete(ProcessingQueue).where(ProcessingQueue.record_id.in_(ids)))
        await db_session.execute(delete(ExpenseRecord).where(ExpenseRecord.id.in_(ids)))
        await db_session.commit()


async def _mk_record(db, owner_id):
    r = ExpenseRecord(
        owner_id=owner_id,
        image_hash=f"h{uuid.uuid4().hex[:10]}",
        status="EN_COLA",
        source_filename=f"f{uuid.uuid4().hex[:6]}.jpg",
    )
    db.add(r)
    await db.flush()
    q = ProcessingQueue(record_id=r.id, status="EN_COLA")
    db.add(q)
    await db.commit()
    _created_record_ids.append(r.id)
    return r, q


async def test_claim_respects_owner(db_session, test_admin_user, test_standard_user):
    await _mk_record(db_session, test_standard_user.id)
    # admin no debe reclamar el job de standard
    job = await queue.claim_next_job(db_session, owner_id=test_admin_user.id)
    assert job is None
    # el dueno si
    job = await queue.claim_next_job(db_session, owner_id=test_standard_user.id)
    assert job is not None


async def test_reset_job_returns_to_en_cola(db_session, test_standard_user):
    r, q = await _mk_record(db_session, test_standard_user.id)
    job = await queue.claim_next_job(db_session, owner_id=test_standard_user.id)
    assert job.status == "ANALIZANDO"
    await queue.reset_job_to_en_cola(db_session, job)
    await db_session.refresh(job)
    assert job.status == "EN_COLA"


async def test_process_batch_claim_waits_on_shared_claim_lock(db_session, test_standard_user):
    await _mk_record(db_session, test_standard_user.id)

    lock = activity.get_claim_lock()
    await lock.acquire()
    claim = AsyncMock(side_effect=queue.claim_next_job)
    fake_process = AsyncMock(return_value=True)
    activity.clear_batch()
    try:
        with (
            patch("app.expenses.queue.claim_next_job", new=claim),
            patch("app.expenses.queue.process_job", new=fake_process),
        ):
            task = asyncio.create_task(
                queue.process_batch("gemini", test_standard_user.id, lambda kind, msg: None)
            )
            await asyncio.sleep(0.05)
            claim.assert_not_awaited()
            assert not task.done()
            lock.release()
            n = await task
        assert n == 1
    finally:
        if lock.locked():
            lock.release()
        activity.clear_batch()


async def test_process_batch_counts_successes_and_events(db_session, test_standard_user):
    await _mk_record(db_session, test_standard_user.id)
    await _mk_record(db_session, test_standard_user.id)

    async def fake_process_job(db, job, engine=None, on_event=None):
        assert engine == "gemini"
        assert on_event is not None
        on_event("info", "fake-progreso")
        return True

    events: list[tuple[str, str]] = []
    activity.clear_batch()
    with patch("app.expenses.queue.process_job", new=AsyncMock(side_effect=fake_process_job)):
        n = await queue.process_batch(
            "gemini",
            test_standard_user.id,
            lambda kind, msg: events.append((kind, msg)),
        )

    assert n == 2
    assert activity.is_busy() is False
    assert any(kind == "info" and "Reclamado" in msg for kind, msg in events)
    assert ("info", "fake-progreso") in events


async def test_process_batch_respects_owner(db_session, test_admin_user, test_standard_user):
    await _mk_record(db_session, test_admin_user.id)
    await _mk_record(db_session, test_standard_user.id)

    async def fake_process_job(db, job, engine=None, on_event=None):
        return True

    with patch("app.expenses.queue.process_job", new=AsyncMock(side_effect=fake_process_job)):
        n = await queue.process_batch("gemini", test_standard_user.id, lambda kind, msg: None)

    assert n == 1

    admin_jobs = await db_session.execute(
        select(ProcessingQueue)
        .join(ExpenseRecord, ExpenseRecord.id == ProcessingQueue.record_id)
        .where(ExpenseRecord.owner_id == test_admin_user.id)
    )
    admin_job = admin_jobs.scalar_one()
    assert admin_job.status == "EN_COLA"


async def test_process_batch_failure_not_counted(db_session, test_standard_user):
    _, q = await _mk_record(db_session, test_standard_user.id)

    async def fake_process_job(db, job, engine=None, on_event=None):
        return False

    activity.clear_batch()
    with patch("app.expenses.queue.process_job", new=AsyncMock(side_effect=fake_process_job)):
        n = await queue.process_batch("kimi", test_standard_user.id, lambda kind, msg: None)

    assert n == 0
    await db_session.refresh(q)
    assert q.status == "ERROR_PERMANENTE"
    assert activity.is_busy() is False


async def test_process_batch_exception_resets_job_and_clears_state(db_session, test_standard_user):
    _, q = await _mk_record(db_session, test_standard_user.id)
    record_id = q.record_id

    events: list[tuple[str, str]] = []
    activity.clear_batch()
    with (
        patch(
            "app.expenses.queue.process_job",
            new=AsyncMock(side_effect=RuntimeError("boom")),
        ),
        pytest.raises(RuntimeError, match="boom"),
    ):
        await queue.process_batch(
            "gemini",
            test_standard_user.id,
            lambda kind, msg: events.append((kind, msg)),
        )

    # el job no queda atascado en ANALIZANDO: vuelve a EN_COLA
    await db_session.refresh(q)
    assert q.status == "EN_COLA"
    assert q.claimed_at is None
    assert q.worker_id is None
    # el record del job tambien vuelve a EN_COLA
    rec = await db_session.get(ExpenseRecord, record_id)
    assert rec is not None and rec.status == "EN_COLA"
    # el estado del lote se limpio y hubo evento de error
    assert activity.is_busy() is False
    assert activity.get_state()["record_id"] is None
    assert any(kind == "error" and "boom" in msg for kind, msg in events)


async def test_process_batch_resets_job_when_session_is_poisoned(db_session, test_standard_user):
    """F5: error de BD en el flush deja la sesion rolled-back.

    ``process_job`` escribe un ``transaction_type`` invalido (viola
    ``ck_expense_records_transaction_type``) y hace flush, por lo que SQLAlchemy
    envenena la ``AsyncSession`` y propaga ``IntegrityError``. El handler de
    ``process_batch`` debe hacer rollback antes de resetear el job; si no, el
    reset tambien falla y el job queda atascado en ANALIZANDO.
    """
    _, q = await _mk_record(db_session, test_standard_user.id)
    record_id = q.record_id

    async def fake_process_job(db, job, engine=None, on_event=None):
        record = await db.get(ExpenseRecord, job.record_id)
        assert record is not None
        record.transaction_type = "invalido"
        await db.flush()
        raise AssertionError("el flush debio violar el CHECK")

    events: list[tuple[str, str]] = []
    activity.clear_batch()
    with (
        patch("app.expenses.queue.process_job", new=AsyncMock(side_effect=fake_process_job)),
        pytest.raises(IntegrityError),
    ):
        await queue.process_batch(
            "gemini",
            test_standard_user.id,
            lambda kind, msg: events.append((kind, msg)),
        )

    await db_session.refresh(q)
    assert q.status == "EN_COLA"
    assert q.claimed_at is None
    assert q.worker_id is None
    rec = await db_session.get(ExpenseRecord, record_id)
    assert rec is not None and rec.status == "EN_COLA"
    assert activity.is_busy() is False
    assert any(kind == "error" for kind, _ in events)


async def _process_job_commit_failure_setup(tmp_path, monkeypatch):
    processed = tmp_path / "procesados"
    monkeypatch.setenv("GASTOSIA_PROCESSED_DIR", str(processed))
    pendientes = tmp_path / "Ruben" / "pendientes"
    pendientes.mkdir(parents=True)
    src = pendientes / "test.jpg"
    src.write_text("image data")

    db = AsyncMock()
    db.add = MagicMock()
    job = MagicMock(spec=ProcessingQueue)
    job.record_id = uuid.uuid4()

    record = MagicMock(spec=ExpenseRecord)
    record.id = job.record_id
    record.transaction_date = None
    record.amount = None
    record.ticket_description = None
    record.bank = None
    record.transaction_type = None
    record.confidence_json = None

    image = MagicMock(spec=ImageFile)
    image.record_id = job.record_id
    image.optimized_path = str(src)
    image.original_path = str(src)
    image.owner_folder = "Ruben"

    db.execute.side_effect = [
        MagicMock(scalar_one_or_none=MagicMock(return_value=record)),
        MagicMock(scalar_one_or_none=MagicMock(return_value=image)),
    ]

    extraction = {
        "parsed_json": {"amount": 100.0},
        "raw_response": "{}",
        "is_valid_json": True,
        "elapsed_ms": 10,
        "error_message": None,
        "engine": "gemini",
    }
    return db, job, image, src, processed, extraction


async def test_process_job_copies_to_procesados_and_removes_original(tmp_path, monkeypatch):
    db, job, image, src, processed, extraction = await _process_job_commit_failure_setup(
        tmp_path, monkeypatch
    )

    with patch("app.expenses.queue.extract_from_image", new=AsyncMock(return_value=extraction)):
        ok = await queue.process_job(db, job)

    copied = processed / "test.jpg"
    assert ok is True
    assert copied.exists()
    assert not src.exists()
    assert image.original_path == str(copied)
    assert db.commit.await_count == 1


async def test_process_job_commit_failure_keeps_original_and_cleans_copy(tmp_path, monkeypatch):
    db, job, image, src, processed, extraction = await _process_job_commit_failure_setup(
        tmp_path, monkeypatch
    )
    db.commit.side_effect = RuntimeError("commit boom")

    with (
        patch("app.expenses.queue.extract_from_image", new=AsyncMock(return_value=extraction)),
        pytest.raises(RuntimeError, match="commit boom"),
    ):
        await queue.process_job(db, job)

    assert src.exists(), "el original debe seguir disponible para el reintento"
    assert not (processed / "test.jpg").exists(), "la copia debe limpiarse si falla el commit"


async def test_process_job_passes_engine_and_adapts_on_event(tmp_path):
    db = AsyncMock()
    db.add = MagicMock()
    job = MagicMock(spec=ProcessingQueue)
    job.record_id = uuid.uuid4()

    record = MagicMock(spec=ExpenseRecord)
    record.id = job.record_id
    record.transaction_date = None
    record.amount = None
    record.ticket_description = None
    record.bank = None
    record.transaction_type = None
    record.confidence_json = None

    img_path = tmp_path / "test.jpg"
    from PIL import Image as PILImage

    img = PILImage.new("RGB", (10, 10), color="red")
    img.save(img_path)

    image = MagicMock(spec=ImageFile)
    image.record_id = job.record_id
    image.optimized_path = str(img_path)
    image.original_path = str(img_path)
    image.owner_folder = "Ruben"

    db.execute.side_effect = [
        MagicMock(scalar_one_or_none=MagicMock(return_value=record)),
        MagicMock(scalar_one_or_none=MagicMock(return_value=image)),
    ]

    fake_extraction = {
        "parsed_json": {"amount": 100.0},
        "raw_response": "{}",
        "is_valid_json": True,
        "elapsed_ms": 10,
        "error_message": None,
        "engine": "kimi",
    }

    events: list[tuple[str, str]] = []
    fake_extract = AsyncMock(return_value=fake_extraction)
    with (
        patch("app.expenses.queue.extract_from_image", new=fake_extract),
        patch("app.expenses.queue._copy_to_procesados", return_value="/procesados/test.jpg"),
    ):
        ok = await queue.process_job(
            db,
            job,
            engine="kimi",
            on_event=lambda kind, msg: events.append((kind, msg)),
        )

    assert ok is True
    kwargs = fake_extract.await_args.kwargs
    assert kwargs["preferred_engine"] == "kimi"
    added = [c.args[0] for c in db.add.call_args_list]
    assert any(isinstance(obj, ExtractionRun) for obj in added)
    kwargs["on_event"]("hola")
    assert events == [("extraccion", "hola")]
