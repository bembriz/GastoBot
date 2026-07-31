from unittest.mock import AsyncMock, MagicMock

from app.database.models import ExpenseRecord, ProcessingQueue
from app.expenses.queue import claim_next_job, complete_job, recover_stale_jobs


class TestRecoverStaleJobsExtra:
    async def test_recover_stale_with_no_records(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = []
        db.execute.return_value = mock_result

        count = await recover_stale_jobs(db)
        assert count == 0

    async def test_recover_stale_resets_en_cola(self):
        job = ProcessingQueue()
        job.status = "ANALIZANDO"
        job.record_id = "fake-id"

        record = ExpenseRecord()
        record.id = "fake-id"
        record.status = "EN_COLA"

        db = AsyncMock()

        mock_job_result = MagicMock()
        mock_job_result.scalars().all.return_value = [job]
        mock_record_result = MagicMock()
        mock_record_result.scalar_one_or_none.return_value = record

        db.execute.side_effect = [mock_job_result, mock_record_result]

        count = await recover_stale_jobs(db)
        assert count == 1
        assert job.status == "EN_COLA"


class TestCompleteJobEdgeCases:
    async def test_complete_job_sets_requiere_revision(self):
        job = ProcessingQueue()
        job.id = 1
        job.record_id = "rid"
        job.status = "EN_COLA"

        record = ExpenseRecord()
        record.id = "rid"
        record.status = "ANALIZANDO"

        db = AsyncMock()
        mock_record_result = MagicMock()
        mock_record_result.scalar_one_or_none.return_value = record
        db.execute.return_value = mock_record_result

        await complete_job(db, job, success=True)

        assert record.status == "REQUIERE_REVISION"
        assert job.status == "COMPLETADO"

    async def test_complete_job_failure_sets_error(self):
        job = ProcessingQueue()
        job.id = 1
        job.record_id = "rid"
        job.status = "EN_COLA"

        record = ExpenseRecord()
        record.id = "rid"
        record.status = "ANALIZANDO"

        db = AsyncMock()
        mock_record_result = MagicMock()
        mock_record_result.scalar_one_or_none.return_value = record
        db.execute.return_value = mock_record_result

        await complete_job(db, job, success=False, error_msg="OCR failed")

        assert job.status == "ERROR_PERMANENTE"
        assert job.last_error == "OCR failed"


class TestClaimNextJobEdgeCases:
    async def test_claim_empty_queue(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        record = await claim_next_job(db)
        assert record is None
