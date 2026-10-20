"""Tests de las rutas de procesamiento manual (process/stop/activity)."""

import asyncio
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import httpx
import pytest_asyncio
from sqlalchemy import select

from app.auth.session import create_session
from app.database.models import ExpenseRecord, ProcessingQueue
from app.expenses import activity
from app.main import app

COOKIE_NAME = "gastosia_session"


def _make_client(user) -> httpx.AsyncClient:
    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")
    client.cookies.set(COOKIE_NAME, create_session(user.id, user.username, user.role))
    return client


@pytest_asyncio.fixture(loop_scope="function")
async def _clean_activity():
    activity.clear_batch()
    activity.pop_task()
    yield
    activity.clear_batch()
    activity.pop_task()


class TestProcessRoute:
    async def test_process_rejects_when_busy(self, test_admin_user, _clean_activity):
        activity.set_batch(str(uuid.uuid4()), "y.jpg", "gemini")
        async with _make_client(test_admin_user) as client:
            r = await client.post("/expenses/process", data={"engine": "gemini"})
        assert r.status_code == 409
        assert "Proceso en curso" in r.text

    async def test_process_invalid_engine(self, test_admin_user, _clean_activity):
        async with _make_client(test_admin_user) as client:
            r = await client.post("/expenses/process", data={"engine": "otro"})
        assert r.status_code == 400

    async def test_process_starts_batch_when_idle(self, test_admin_user, _clean_activity):
        mock_batch = AsyncMock(return_value=0)
        with patch("app.expenses.routes.process_batch", new=mock_batch):
            async with _make_client(test_admin_user) as client:
                r = await client.post("/expenses/process", data={"engine": "gemini"})
            # Deja correr el task fire-and-forget antes de cerrar el loop.
            await asyncio.sleep(0)
        assert r.status_code == 200
        assert "iniciado" in r.text.lower()
        mock_batch.assert_awaited_once()
        args = mock_batch.await_args.args
        assert args[0] == "gemini"
        # admin => owner_id None (procesa la cola completa)
        assert args[1] is None

    async def test_process_standard_user_scopes_owner(self, test_standard_user, _clean_activity):
        mock_batch = AsyncMock(return_value=0)
        with patch("app.expenses.routes.process_batch", new=mock_batch):
            async with _make_client(test_standard_user) as client:
                r = await client.post("/expenses/process", data={"engine": "kimi"})
            await asyncio.sleep(0)
        assert r.status_code == 200
        mock_batch.assert_awaited_once()
        args = mock_batch.await_args.args
        assert args[0] == "kimi"
        assert args[1] == test_standard_user.id

    async def test_process_concurrent_posts_start_single_batch(
        self, test_admin_user, _clean_activity
    ):
        mock_batch = AsyncMock(return_value=0)
        with patch("app.expenses.routes.process_batch", new=mock_batch):
            async with _make_client(test_admin_user) as client:
                r1, r2 = await asyncio.gather(
                    client.post("/expenses/process", data={"engine": "gemini"}),
                    client.post("/expenses/process", data={"engine": "gemini"}),
                )
            await asyncio.sleep(0)
        assert sorted([r1.status_code, r2.status_code]) == [200, 409]
        assert "Proceso en curso" in (r1.text + r2.text)
        assert mock_batch.await_count == 1

    async def test_process_waits_on_shared_claim_lock(self, test_admin_user, _clean_activity):
        # F1: POST /process decide+reclama bajo el MISMO lock que el worker;
        # mientras el lock esta tomado, el route no decide nada (ni busy).
        from app.expenses import activity

        lock = activity.get_claim_lock()
        await lock.acquire()
        mock_batch = AsyncMock(return_value=0)
        try:
            with patch("app.expenses.routes.process_batch", new=mock_batch):
                async with _make_client(test_admin_user) as client:
                    post = asyncio.create_task(
                        client.post("/expenses/process", data={"engine": "gemini"})
                    )
                    await asyncio.sleep(0.05)
                    assert not post.done(), "el POST debe esperar el lock compartido"
                    assert not activity.is_busy()
                    assert mock_batch.await_count == 0
                    lock.release()
                    r = await post
            assert r.status_code == 200
            assert activity.is_busy()
        finally:
            if lock.locked():
                lock.release()
            activity.clear_batch()
            activity.pop_task()
            await asyncio.sleep(0)

    async def test_process_conflicts_with_analizando_job_in_db(
        self, db_session, test_admin_user, _clean_activity
    ):
        # Worker auto sostiene un job en ANALIZANDO pero NO marco busy
        # (ventana claim -> set_batch): el route debe bloquear igual (I3).
        record = ExpenseRecord(
            owner_id=test_admin_user.id,
            image_hash=f"sha_gate_{uuid.uuid4().hex[:16]}",
            status="ANALIZANDO",
            source_filename=f"gate_{uuid.uuid4().hex[:8]}.jpg",
        )
        db_session.add(record)
        await db_session.flush()
        job = ProcessingQueue(
            record_id=record.id,
            status="ANALIZANDO",
            claimed_at=datetime.now(UTC),
            worker_id="w-auto",
        )
        db_session.add(job)
        await db_session.commit()

        try:
            assert not activity.is_busy()
            mock_batch = AsyncMock(return_value=0)
            with patch("app.expenses.routes.process_batch", new=mock_batch):
                async with _make_client(test_admin_user) as client:
                    r = await client.post("/expenses/process", data={"engine": "gemini"})
            assert r.status_code == 409
            assert "ANALIZANDO" in r.text
            mock_batch.assert_not_awaited()
        finally:
            await db_session.delete(job)
            await db_session.delete(record)
            await db_session.commit()


class TestStopRoute:
    async def test_stop_without_batch_shows_notice(self, test_admin_user, _clean_activity):
        async with _make_client(test_admin_user) as client:
            r = await client.post("/expenses/stop")
        assert r.status_code == 200
        assert "No hay proceso en curso" in r.text

    async def test_stop_waits_on_shared_claim_lock(self, test_admin_user, _clean_activity):
        # F1: stop decide+barre bajo el MISMO lock que POST /process y el
        # worker; con el lock tomado no debe responder ni tocar el state.
        lock = activity.get_claim_lock()
        await lock.acquire()
        activity.set_batch(str(uuid.uuid4()), "lock.jpg", "gemini")
        try:
            async with _make_client(test_admin_user) as client:
                post = asyncio.create_task(client.post("/expenses/stop"))
                # Margen amplio: sin el lock la ruta responde en ~60 ms (primer
                # uso del pool); asi el rojo es determinista, no una carrera.
                await asyncio.sleep(0.3)
                assert not post.done(), "el POST debe esperar el lock compartido"
                assert activity.is_busy(), "stop no debe decidir con el lock tomado"
                lock.release()
                r = await post
            assert r.status_code == 200
            assert "Lote detenido" in r.text
            assert not activity.is_busy()
        finally:
            if lock.locked():
                lock.release()
            activity.clear_batch()
            activity.pop_task()
            await asyncio.sleep(0)

    async def test_stop_resets_in_flight_job(self, db_session, test_admin_user, _clean_activity):
        record = ExpenseRecord(
            owner_id=test_admin_user.id,
            image_hash=f"sha_stop_{uuid.uuid4().hex[:16]}",
            status="ANALIZANDO",
            source_filename=f"stop_{uuid.uuid4().hex[:8]}.jpg",
        )
        db_session.add(record)
        await db_session.flush()
        job = ProcessingQueue(record_id=record.id, status="ANALIZANDO")
        db_session.add(job)
        await db_session.commit()

        activity.set_batch(str(record.id), record.source_filename, "gemini")

        async def _noop() -> None:
            return None

        task = asyncio.create_task(_noop())
        activity.attach_task(task)

        try:
            async with _make_client(test_admin_user) as client:
                r = await client.post("/expenses/stop")
            assert r.status_code == 200
            assert "Lote detenido" in r.text
            assert not activity.is_busy()
            assert activity.get_task() is None

            from app.database.session import async_session

            async with async_session() as fresh:
                q = (
                    await fresh.execute(
                        select(ProcessingQueue).where(ProcessingQueue.record_id == record.id)
                    )
                ).scalar_one()
                rec = (
                    await fresh.execute(select(ExpenseRecord).where(ExpenseRecord.id == record.id))
                ).scalar_one()
            assert q.status == "EN_COLA"
            assert q.claimed_at is None
            assert q.worker_id is None
            assert rec.status == "EN_COLA"
        finally:
            await db_session.delete(job)
            await db_session.delete(record)
            await db_session.commit()

    async def test_stop_resets_analizando_job_not_in_state(
        self, db_session, test_admin_user, _clean_activity
    ):
        record = ExpenseRecord(
            owner_id=test_admin_user.id,
            image_hash=f"sha_sweep_{uuid.uuid4().hex[:16]}",
            status="ANALIZANDO",
            source_filename=f"sweep_{uuid.uuid4().hex[:8]}.jpg",
        )
        db_session.add(record)
        await db_session.flush()
        job = ProcessingQueue(
            record_id=record.id,
            status="ANALIZANDO",
            claimed_at=datetime.now(UTC),
            worker_id="w-test",
        )
        db_session.add(job)
        await db_session.commit()

        # El state apunta a OTRO record: simula la ventana claim->set_batch
        # en la que stop lee el record_id anterior al job recien reclamado.
        activity.set_batch(str(uuid.uuid4()), "otro.jpg", "gemini")

        async def _noop() -> None:
            return None

        task = asyncio.create_task(_noop())
        activity.attach_task(task)

        try:
            async with _make_client(test_admin_user) as client:
                r = await client.post("/expenses/stop")
            assert r.status_code == 200
            assert "Lote detenido" in r.text

            from app.database.session import async_session

            async with async_session() as fresh:
                q = (
                    await fresh.execute(
                        select(ProcessingQueue).where(ProcessingQueue.record_id == record.id)
                    )
                ).scalar_one()
                rec = (
                    await fresh.execute(select(ExpenseRecord).where(ExpenseRecord.id == record.id))
                ).scalar_one()
            assert q.status == "EN_COLA"
            assert q.claimed_at is None
            assert q.worker_id is None
            assert rec.status == "EN_COLA"
            assert not activity.is_busy()
        finally:
            await db_session.delete(job)
            await db_session.delete(record)
            await db_session.commit()

    async def test_stop_sweeps_orphan_analizando_without_busy(
        self, db_session, test_admin_user, _clean_activity
    ):
        # F2: job ANALIZANDO huérfano (worker auto murio sin marcar busy) ->
        # stop debe barrerlo aunque is_busy() sea False; si no, /process
        # queda en 409 permanente.
        record = ExpenseRecord(
            owner_id=test_admin_user.id,
            image_hash=f"sha_orphan_{uuid.uuid4().hex[:16]}",
            status="ANALIZANDO",
            source_filename=f"orphan_{uuid.uuid4().hex[:8]}.jpg",
        )
        db_session.add(record)
        await db_session.flush()
        job = ProcessingQueue(
            record_id=record.id,
            status="ANALIZANDO",
            claimed_at=datetime.now(UTC),
            worker_id="w-dead",
        )
        db_session.add(job)
        await db_session.commit()

        try:
            assert not activity.is_busy()
            async with _make_client(test_admin_user) as client:
                r = await client.post("/expenses/stop")
            assert r.status_code == 200
            assert "Lote detenido" in r.text
            assert not activity.is_busy()

            from app.database.session import async_session

            async with async_session() as fresh:
                q = (
                    await fresh.execute(
                        select(ProcessingQueue).where(ProcessingQueue.record_id == record.id)
                    )
                ).scalar_one()
                rec = (
                    await fresh.execute(select(ExpenseRecord).where(ExpenseRecord.id == record.id))
                ).scalar_one()
            assert q.status == "EN_COLA"
            assert q.claimed_at is None
            assert q.worker_id is None
            assert rec.status == "EN_COLA"
        finally:
            await db_session.delete(job)
            await db_session.delete(record)
            await db_session.commit()


class TestActivityPanel:
    async def test_activity_panel_renders(self, test_admin_user, _clean_activity):
        async with _make_client(test_admin_user) as client:
            r = await client.get("/dashboard/activity")
        assert r.status_code == 200
        assert "En cola" in r.text
        assert "Actividad" in r.text

    async def test_activity_panel_requires_auth(self, _clean_activity):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            r = await client.get("/dashboard/activity", follow_redirects=False)
        assert r.status_code in (302, 307)
        assert r.headers["location"] == "/login"

    async def test_activity_panel_counts_queued_for_standard_user(
        self, db_session, test_standard_user, _clean_activity
    ):
        record = ExpenseRecord(
            owner_id=test_standard_user.id,
            image_hash=f"sha_act_{uuid.uuid4().hex[:16]}",
            status="EN_COLA",
            source_filename=f"act_{uuid.uuid4().hex[:8]}.jpg",
            created_at=datetime.now(UTC),
        )
        db_session.add(record)
        await db_session.commit()
        try:
            from sqlalchemy import func

            expected = (
                await db_session.execute(
                    select(func.count())
                    .select_from(ExpenseRecord)
                    .where(
                        ExpenseRecord.status == "EN_COLA",
                        ExpenseRecord.owner_id == test_standard_user.id,
                    )
                )
            ).scalar_one()
            async with _make_client(test_standard_user) as client:
                r = await client.get("/dashboard/activity")
            assert r.status_code == 200
            assert f"<strong>En cola:</strong> {expected}" in r.text
        finally:
            await db_session.delete(record)
            await db_session.commit()
