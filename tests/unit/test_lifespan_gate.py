"""Gate del worker automatico: GASTOSIA_AUTO_PROCESS + recuperacion al arranque.

Cierra I3: el worker FIFO solo arranca si GASTOSIA_AUTO_PROCESS esta activo
(procesamiento SOLO manual por defecto). recover_stale_jobs corre SIEMPRE al
arranque, con o sin worker.
"""

import asyncio
import contextlib
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app import main
from app.database.models import ProcessingQueue
from app.main import _auto_process_enabled


class TestAutoProcessEnabled:
    @pytest.mark.parametrize("value", ["1", "true", "yes", "TRUE", "Yes", " 1 "])
    def test_truthy_values(self, monkeypatch, value):
        monkeypatch.setenv("GASTOSIA_AUTO_PROCESS", value)
        assert _auto_process_enabled() is True

    @pytest.mark.parametrize("value", ["", "0", "false", "no", "maybe", " "])
    def test_falsy_values(self, monkeypatch, value):
        monkeypatch.setenv("GASTOSIA_AUTO_PROCESS", value)
        assert _auto_process_enabled() is False

    def test_unset_is_false(self, monkeypatch):
        monkeypatch.delenv("GASTOSIA_AUTO_PROCESS", raising=False)
        assert _auto_process_enabled() is False


class _LifespanHarness:
    """Corre el lifespan real (sin GASTOSIA_TEST) con tareas y DB mockeadas."""

    def __init__(self, monkeypatch):
        self.mock_monitor = AsyncMock()
        self.mock_worker = AsyncMock()
        self.mock_recover = AsyncMock(return_value=0)
        monkeypatch.setattr(main, "_start_monitor", self.mock_monitor)
        monkeypatch.setattr(main, "_start_worker", self.mock_worker)
        monkeypatch.setattr("app.expenses.queue.recover_stale_jobs", self.mock_recover)
        mock_session = MagicMock()
        mock_session.return_value.__aenter__.return_value = AsyncMock()
        monkeypatch.setattr("app.database.session.async_session", mock_session)
        monkeypatch.delenv("GASTOSIA_TEST", raising=False)
        monkeypatch.setattr(main, "_monitor_task", None)
        monkeypatch.setattr(main, "_worker_task", None)

    async def run(self):
        async with main.lifespan(main.app):
            # deja correr las tareas recien creadas antes de inspeccionarlas
            await asyncio.sleep(0)
            return main._worker_task


class TestLifespanGate:
    async def test_worker_not_started_without_env(self, monkeypatch):
        monkeypatch.delenv("GASTOSIA_AUTO_PROCESS", raising=False)
        h = _LifespanHarness(monkeypatch)
        worker_task = await h.run()
        assert worker_task is None
        assert h.mock_monitor.await_count == 1
        assert h.mock_worker.await_count == 0

    async def test_worker_started_with_env(self, monkeypatch):
        monkeypatch.setenv("GASTOSIA_AUTO_PROCESS", "1")
        h = _LifespanHarness(monkeypatch)
        worker_task = await h.run()
        assert worker_task is not None
        assert h.mock_worker.await_count == 1

    async def test_recover_always_runs(self, monkeypatch):
        monkeypatch.delenv("GASTOSIA_AUTO_PROCESS", raising=False)
        h = _LifespanHarness(monkeypatch)
        await h.run()
        assert h.mock_recover.await_count == 1


class TestWorkerBusyGuard:
    async def test_worker_waits_when_manual_batch_busy(self):
        from app.expenses import activity

        activity.set_batch(str(uuid.uuid4()), "lote.jpg", "gemini")
        try:
            with (
                patch("app.expenses.queue.async_session") as mock_session,
                patch("app.expenses.queue.recover_stale_jobs", new=AsyncMock(return_value=0)),
                patch("app.expenses.queue.claim_next_job", new=AsyncMock()) as mock_claim,
                patch("app.expenses.queue.asyncio.sleep", side_effect=Exception("stop-test")),
            ):
                from app.expenses.queue import worker_loop

                mock_db = AsyncMock()
                mock_session.return_value.__aenter__.return_value = mock_db

                with contextlib.suppress(Exception):
                    await worker_loop()

                mock_claim.assert_not_awaited()
        finally:
            activity.clear_batch()

    async def test_worker_claims_when_idle(self):
        mock_claim = AsyncMock(return_value=None)
        with (
            patch("app.expenses.queue.async_session") as mock_session,
            patch("app.expenses.queue.recover_stale_jobs", new=AsyncMock(return_value=0)),
            patch("app.expenses.queue.claim_next_job", new=mock_claim),
            patch("app.expenses.queue.asyncio.sleep", side_effect=Exception("stop-test")),
        ):
            from app.expenses.queue import worker_loop

            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            with contextlib.suppress(Exception):
                await worker_loop()

            assert mock_claim.await_count >= 1


class TestSharedClaimLock:
    """F1: un unico asyncio.Lock decide+reclama en route y worker."""

    async def test_get_claim_lock_is_shared_async_lock(self):
        import asyncio as aio

        from app.expenses import activity

        lock = activity.get_claim_lock()
        assert isinstance(lock, aio.Lock)
        assert activity.get_claim_lock() is lock

    async def test_worker_defers_claim_while_lock_held(self):
        from app.expenses import activity

        lock = activity.get_claim_lock()
        await lock.acquire()
        mock_claim = AsyncMock(return_value=None)
        try:
            with (
                patch("app.expenses.queue.async_session") as mock_session,
                patch("app.expenses.queue.recover_stale_jobs", new=AsyncMock(return_value=0)),
                patch("app.expenses.queue.claim_next_job", new=mock_claim),
            ):
                from app.expenses.queue import worker_loop

                mock_session.return_value.__aenter__.return_value = AsyncMock()
                task = asyncio.create_task(worker_loop())
                await asyncio.sleep(0.05)
                # El worker espera el lock compartido: no reclama ni decide.
                assert not task.done()
                assert mock_claim.await_count == 0

                lock.release()
                # El patch de sleep va DESPUES de soltar el lock: patchear
                # asyncio.sleep afecta al modulo entero (tambien el del test).
                with (
                    patch("app.expenses.queue.asyncio.sleep", side_effect=Exception("stop-test")),
                    contextlib.suppress(Exception),
                ):
                    await task
                assert mock_claim.await_count == 1
        finally:
            if lock.locked():
                lock.release()
            activity.clear_batch()


class TestWorkerResetOnError:
    """F3: si procesar falla, el job vuelve a EN_COLA (no queda huérfano)."""

    async def test_worker_resets_job_on_processing_error(self):
        job = MagicMock(spec=ProcessingQueue)
        job.record_id = uuid.uuid4()
        job.attempts = 1

        with (
            patch("app.expenses.queue.async_session") as mock_session,
            patch("app.expenses.queue.recover_stale_jobs", new=AsyncMock(return_value=0)),
            patch("app.expenses.queue.claim_next_job", new=AsyncMock(return_value=job)),
            patch(
                "app.expenses.queue.process_job",
                new=AsyncMock(side_effect=Exception("boom")),
            ),
            patch("app.expenses.queue.complete_job", new=AsyncMock()) as mock_complete,
            patch("app.expenses.queue.reset_job_to_en_cola", new=AsyncMock()) as mock_reset,
            patch("app.expenses.activity.push_event") as mock_push,
            patch("app.expenses.queue.asyncio.sleep", side_effect=Exception("stop-test")),
        ):
            from app.expenses.queue import worker_loop

            mock_session.return_value.__aenter__.return_value = AsyncMock()

            with contextlib.suppress(Exception):
                await worker_loop()

            mock_reset.assert_awaited_once()
            assert mock_reset.await_args.args[1] is job
            mock_complete.assert_not_awaited()
            error_calls = [c for c in mock_push.call_args_list if c.args[0] == "error"]
            assert error_calls, "el worker debe emitir evento de error en activity"


class TestProdHostGuard:
    """F4: los tests solo contra hosts loopback salvo GASTOSIA_ALLOW_PROD_TESTS."""

    def test_loopback_hosts_ok(self):
        from tests.conftest import validate_test_db_host

        validate_test_db_host("127.0.0.1")
        validate_test_db_host("localhost")
        validate_test_db_host("::1")

    def test_non_loopback_host_raises(self):
        from tests.conftest import validate_test_db_host

        with pytest.raises(RuntimeError, match="no-loopback"):
            validate_test_db_host("192.168.100.24")

    def test_allow_env_escape(self, monkeypatch):
        from tests.conftest import validate_test_db_host

        monkeypatch.setenv("GASTOSIA_ALLOW_PROD_TESTS", "1")
        validate_test_db_host("192.168.100.24")

    def test_allow_flag_escape(self):
        from tests.conftest import validate_test_db_host

        validate_test_db_host("192.168.100.24", allow_prod=True)
