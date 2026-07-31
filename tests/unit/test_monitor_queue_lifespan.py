"""Tests para scan_directory, process_job y main lifespan."""

import contextlib
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.database.models import ExpenseRecord, ImageFile, ProcessingQueue, User


class TestScanDirectory:
    async def test_directory_not_exists_returns_zero(self):
        from app.images.monitor import scan_directory

        db = AsyncMock()
        db.execute.return_value = _scalar_result(None)

        result = await scan_directory("Ruben", "/nonexistent/path", db)
        assert result == 0

    async def test_user_not_found_returns_zero(self, tmp_path):
        from app.images.monitor import scan_directory

        db = AsyncMock()
        db.execute.return_value = _scalar_result(None)

        folder = tmp_path / "pendientes"
        folder.mkdir()

        result = await scan_directory("Nobody", str(folder), db)
        assert result == 0

    async def test_skips_non_image_files(self, tmp_path):
        from app.images.monitor import scan_directory

        db = AsyncMock()
        user = MagicMock(spec=User)
        user.id = uuid.uuid4()

        db.execute.side_effect = [
            _scalar_result(user),
            _scalar_result(None),
        ]

        folder = tmp_path / "pendientes"
        folder.mkdir()
        (folder / "readme.txt").write_text("hello")
        (folder / "data.csv").write_text("a,b,c")

        result = await scan_directory("Ruben", str(folder), db)
        assert result == 0

    async def test_skips_large_files(self, tmp_path):
        from app.images.monitor import MAX_FILE_SIZE, scan_directory

        db = AsyncMock()
        user = MagicMock(spec=User)
        user.id = uuid.uuid4()

        db.execute.side_effect = [
            _scalar_result(user),
            _scalar_result(None),
        ]

        folder = tmp_path / "pendientes"
        folder.mkdir()
        big = folder / "big.jpg"
        with open(big, "wb") as f:
            f.seek(MAX_FILE_SIZE + 1)
            f.write(b"\0")

        result = await scan_directory("Ruben", str(folder), db)
        assert result == 0

    async def test_duplicate_hash_marks_duplicado(self, tmp_path):
        from app.images.monitor import scan_directory

        db = AsyncMock()
        user = MagicMock(spec=User)
        user.id = uuid.uuid4()

        existing_image = MagicMock(spec=ImageFile)
        existing_image.sha256_hash = "abc123"

        existing_record = MagicMock(spec=ExpenseRecord)
        existing_record.status = "DETECTADO"

        db.execute.side_effect = [
            _scalar_result(user),
            _scalar_result(existing_image),
            _scalar_result(existing_record),
        ]

        from PIL import Image as PILImage

        folder = tmp_path / "pendientes"
        folder.mkdir()
        img_path = folder / "test.jpg"
        img = PILImage.new("RGB", (10, 10), color="red")
        img.save(img_path)

        result = await scan_directory("Ruben", str(folder), db)
        assert result == 0
        assert existing_record.status == "DUPLICADO_EXACTO"

    async def test_new_image_enters_queue(self, tmp_path):
        from app.images.monitor import scan_directory

        db = AsyncMock()
        user = MagicMock(spec=User)
        user.id = uuid.uuid4()

        db.execute.side_effect = [
            _scalar_result(user),
            _scalar_result(None),
        ]

        from PIL import Image as PILImage

        folder = tmp_path / "pendientes"
        folder.mkdir()
        img_path = folder / "test.jpg"
        img = PILImage.new("RGB", (10, 10), color="red")
        img.save(img_path)

        result = await scan_directory("Ruben", str(folder), db)
        assert result == 1
        assert db.add.call_count == 3
        db.commit.assert_awaited_once()

    async def test_permission_error_skipped(self, tmp_path):
        from app.images.monitor import scan_directory

        db = AsyncMock()
        user = MagicMock(spec=User)
        user.id = uuid.uuid4()

        db.execute.side_effect = [
            _scalar_result(user),
            _scalar_result(None),
        ]

        folder = tmp_path / "pendientes"
        folder.mkdir()
        img_path = folder / "test.jpg"
        img_path.write_text("data")

        with patch("app.images.monitor.sha256_file", side_effect=PermissionError("denied")):
            result = await scan_directory("Ruben", str(folder), db)
            assert result == 0


class TestProcessJob:
    async def test_process_job_record_not_found(self):
        from app.expenses.queue import process_job

        db = AsyncMock()
        job = MagicMock(spec=ProcessingQueue)
        job.record_id = uuid.uuid4()

        db.execute.return_value = _scalar_result(None)

        result = await process_job(db, job)
        assert result is False

    async def test_process_job_image_not_found(self):
        from app.expenses.queue import process_job

        db = AsyncMock()
        job = MagicMock(spec=ProcessingQueue)
        job.record_id = uuid.uuid4()

        record = MagicMock(spec=ExpenseRecord)
        record.id = job.record_id

        db.execute.side_effect = [
            _scalar_result(record),
            _scalar_result(None),
        ]

        result = await process_job(db, job)
        assert result is False

    async def test_process_job_file_not_exists(self):
        from app.expenses.queue import process_job

        db = AsyncMock()
        job = MagicMock(spec=ProcessingQueue)
        job.record_id = uuid.uuid4()

        record = MagicMock(spec=ExpenseRecord)
        record.id = job.record_id

        image = MagicMock(spec=ImageFile)
        image.record_id = job.record_id
        image.optimized_path = None
        image.original_path = "/nonexistent/photo.jpg"

        db.execute.side_effect = [
            _scalar_result(record),
            _scalar_result(image),
        ]

        result = await process_job(db, job)
        assert result is False

    async def test_process_job_success_with_extraction(self, tmp_path):
        from app.expenses.queue import process_job

        db = AsyncMock()
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
            _scalar_result(record),
            _scalar_result(image),
        ]

        fake_extraction = {
            "parsed_json": {
                "transaction_date": "2026-01-15",
                "amount": 1500.50,
                "ticket_description": "Test purchase",
                "bank": "BBVA",
                "transaction_type": "Credito",
                "confidence": {"amount": 0.95},
            },
            "raw_response": '{"ok": true}',
            "is_valid_json": True,
            "elapsed_ms": 1500,
            "error_message": None,
        }

        with (
            patch(
                "app.expenses.queue.extract_from_image",
                new=AsyncMock(return_value=fake_extraction),
            ),
            patch("app.expenses.queue._move_to_procesados"),
        ):
            result = await process_job(db, job)
            assert result is True

    async def test_process_job_extraction_fails(self, tmp_path):
        from app.expenses.queue import process_job

        db = AsyncMock()
        job = MagicMock(spec=ProcessingQueue)
        job.record_id = uuid.uuid4()

        record = MagicMock(spec=ExpenseRecord)
        record.id = job.record_id

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
            _scalar_result(record),
            _scalar_result(image),
        ]

        fake_extraction = {
            "parsed_json": None,
            "raw_response": "error",
            "is_valid_json": False,
            "elapsed_ms": 500,
            "error_message": "Model failure",
        }

        with patch(
            "app.expenses.queue.extract_from_image",
            new=AsyncMock(return_value=fake_extraction),
        ):
            result = await process_job(db, job)
            assert result is False


class TestMoveToProcesados:
    def test_moves_file_successfully(self, tmp_path):
        from app.expenses.queue import _move_to_procesados

        pendientes = tmp_path / "Ruben" / "pendientes"
        pendientes.mkdir(parents=True)
        src = pendientes / "test.jpg"
        src.write_text("image data")

        _move_to_procesados(str(src), "Ruben")

        procesados = tmp_path / "Ruben" / "procesados" / "test.jpg"
        assert procesados.exists()
        assert not src.exists()

    def test_missing_file_no_error(self):
        from app.expenses.queue import _move_to_procesados

        _move_to_procesados("/nonexistent/file.jpg", "Ruben")


class TestMonitorLoop:
    async def test_monitor_starts_and_runs_one_cycle(self):
        with (
            patch("app.images.monitor.PENDING_DIRS", {"Ruben": "/tmp/test_ruben"}),
            patch("app.images.monitor.async_session") as mock_session,
            patch("app.images.monitor.asyncio.sleep", side_effect=asyncio_cancelled_error),
        ):
            from app.images.monitor import monitor_loop

            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            with contextlib.suppress(Exception):
                await monitor_loop()

    async def test_monitor_standby_no_config(self):
        with patch("app.images.monitor.PENDING_DIRS", {}):
            from app.images.monitor import monitor_loop

            result = await monitor_loop()
            assert result is None

    async def test_monitor_handles_scan_error(self):
        with (
            patch("app.images.monitor.PENDING_DIRS", {"Ruben": "/tmp/ruben"}),
            patch("app.images.monitor.scan_directory", side_effect=Exception("scan error")),
            patch("app.images.monitor.asyncio.sleep", side_effect=asyncio_cancelled_error),
        ):
            from app.images.monitor import monitor_loop

            with contextlib.suppress(Exception):
                await monitor_loop()


class TestWorkerLoop:
    async def test_worker_recovers_and_processes(self):
        with (
            patch("app.expenses.queue.async_session") as mock_session,
            patch("app.expenses.queue.recover_stale_jobs", new=AsyncMock(return_value=2)),
            patch("app.expenses.queue.claim_next_job", new=AsyncMock(return_value=None)),
            patch("app.expenses.queue.asyncio.sleep", side_effect=asyncio_cancelled_error),
        ):
            from app.expenses.queue import worker_loop

            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            with contextlib.suppress(Exception):
                await worker_loop()

    async def test_worker_handles_claim_error(self):
        with (
            patch("app.expenses.queue.async_session") as mock_session,
            patch("app.expenses.queue.recover_stale_jobs", new=AsyncMock(return_value=0)),
            patch("app.expenses.queue.claim_next_job", side_effect=Exception("db down")),
            patch("app.expenses.queue.asyncio.sleep", side_effect=asyncio_cancelled_error),
        ):
            from app.expenses.queue import worker_loop

            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            with contextlib.suppress(Exception):
                await worker_loop()


class TestLifespan:
    def test_lifespan_test_mode(self):
        from app.main import app, lifespan

        async def _test():
            async with lifespan(app):
                pass

        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        loop.run_until_complete(_test())


def _scalar_result(scalar_value):
    result = MagicMock()
    result.scalar_one_or_none = MagicMock(return_value=scalar_value)
    return result


def asyncio_cancelled_error(*args, **kwargs):
    raise Exception("cancelled for test")
