import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.expenses.queue import (
    STALE_TIMEOUT_SECONDS,
    WORKER_ID,
    claim_next_job,
    complete_job,
    recover_stale_jobs,
)

TEST_RECORD_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
TEST_QUEUE_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


def _fake_queue_entry(status="EN_COLA", claimed_at=None, attempts=0):
    """Build a ProcessingQueue-like object for tests."""
    job = MagicMock()
    job.id = TEST_QUEUE_ID
    job.record_id = TEST_RECORD_ID
    job.status = status
    job.enqueued_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    job.claimed_at = claimed_at
    job.completed_at = None
    job.worker_id = None
    job.priority = 0
    job.attempts = attempts
    job.last_error = None
    return job


def _fake_record(status="EN_COLA"):
    record = MagicMock()
    record.id = TEST_RECORD_ID
    record.status = status
    return record


def _fake_result(scalar_result):
    """Build a fake execute result that returns scalar_result on scalar_one_or_none()."""
    result = MagicMock()
    result.scalar_one_or_none = MagicMock(return_value=scalar_result)
    return result


def _fake_result_scalars(scalars_list):
    """Build a fake execute result that returns scalars_list on scalars().all()."""
    result = MagicMock()
    scalars_mock = MagicMock()
    scalars_mock.all = MagicMock(return_value=scalars_list)
    result.scalars = MagicMock(return_value=scalars_mock)
    return result


class TestClaimNextJob:
    async def test_claim_next_job_finds_en_cola(self):
        db = AsyncMock()
        job = _fake_queue_entry(status="EN_COLA")
        record = _fake_record(status="EN_COLA")

        db.execute.side_effect = [
            _fake_result(job),
            _fake_result(record),
        ]

        result = await claim_next_job(db)

        assert result is not None
        assert result.status == "ANALIZANDO"
        assert result.claimed_at is not None
        assert result.worker_id == WORKER_ID
        assert result.attempts == 1
        db.commit.assert_awaited_once()

    async def test_claim_next_job_no_pending_jobs(self):
        db = AsyncMock()
        db.execute.return_value = _fake_result(None)

        result = await claim_next_job(db)

        assert result is None
        db.commit.assert_not_awaited()

    async def test_claim_next_job_updates_record_status(self):
        db = AsyncMock()
        job = _fake_queue_entry(status="EN_COLA")
        record = _fake_record(status="EN_COLA")

        db.execute.side_effect = [
            _fake_result(job),
            _fake_result(record),
        ]

        await claim_next_job(db)

        assert record.status == "ANALIZANDO"

    async def test_claim_next_job_record_not_found(self):
        db = AsyncMock()
        job = _fake_queue_entry(status="EN_COLA")

        db.execute.side_effect = [
            _fake_result(job),
            _fake_result(None),
        ]

        result = await claim_next_job(db)

        assert result is not None
        assert result.status == "ANALIZANDO"


class TestCompleteJob:
    async def test_complete_job_success_sets_status(self):
        db = AsyncMock()
        job = _fake_queue_entry(status="ANALIZANDO", attempts=1)
        record = _fake_record(status="ANALIZANDO")

        db.execute.return_value = _fake_result(record)

        await complete_job(db, job, success=True)

        assert job.status == "COMPLETADO"
        assert job.completed_at is not None
        assert record.status == "REQUIERE_REVISION"
        db.commit.assert_awaited_once()

    async def test_complete_job_failure_sets_error(self):
        db = AsyncMock()
        job = _fake_queue_entry(status="ANALIZANDO", attempts=1)
        record = _fake_record(status="ANALIZANDO")

        db.execute.return_value = _fake_result(record)

        await complete_job(db, job, success=False, error_msg="OCR failed")

        assert job.status == "ERROR_PERMANENTE"
        assert job.last_error == "OCR failed"
        assert record.status == "ERROR_PROCESAMIENTO"
        db.commit.assert_awaited_once()

    async def test_complete_job_without_error_msg(self):
        db = AsyncMock()
        job = _fake_queue_entry(status="ANALIZANDO", attempts=1)
        record = _fake_record(status="ANALIZANDO")

        db.execute.return_value = _fake_result(record)

        await complete_job(db, job, success=True)

        assert job.last_error is None

    async def test_complete_job_record_not_found(self):
        db = AsyncMock()
        job = _fake_queue_entry(status="ANALIZANDO", attempts=1)

        db.execute.return_value = _fake_result(None)

        await complete_job(db, job, success=True)

        assert job.status == "COMPLETADO"


class TestRecoverStaleJobs:
    async def test_recover_stale_jobs_with_stale_entries(self):
        db = AsyncMock()
        stale_time = datetime.now(timezone.utc) - timedelta(seconds=STALE_TIMEOUT_SECONDS + 60)
        job1 = _fake_queue_entry(status="ANALIZANDO", claimed_at=stale_time, attempts=2)
        job2 = _fake_queue_entry(status="ANALIZANDO", claimed_at=stale_time, attempts=1)
        record1 = _fake_record(status="ANALIZANDO")
        record2 = _fake_record(status="ANALIZANDO")

        db.execute.side_effect = [
            _fake_result_scalars([job1, job2]),
            _fake_result(record1),
            _fake_result(record2),
        ]

        count = await recover_stale_jobs(db)

        assert count == 2
        assert job1.status == "EN_COLA"
        assert job1.claimed_at is None
        assert job1.worker_id is None
        assert job2.status == "EN_COLA"
        assert record1.status == "EN_COLA"
        assert record2.status == "EN_COLA"
        db.commit.assert_awaited_once()

    async def test_recover_stale_jobs_no_stale_entries(self):
        db = AsyncMock()
        recent_time = datetime.now(timezone.utc) - timedelta(seconds=60)
        job = _fake_queue_entry(status="ANALIZANDO", claimed_at=recent_time)

        db.execute.side_effect = [
            _fake_result_scalars([]),
        ]

        count = await recover_stale_jobs(db)

        assert count == 0
        db.commit.assert_not_awaited()

    async def test_recover_stale_jobs_multiple_stale_with_mixed_records(self):
        db = AsyncMock()
        stale_time = datetime.now(timezone.utc) - timedelta(seconds=STALE_TIMEOUT_SECONDS + 3600)
        job1 = _fake_queue_entry(status="ANALIZANDO", claimed_at=stale_time)
        job2 = _fake_queue_entry(status="ANALIZANDO", claimed_at=stale_time)
        record1 = _fake_record(status="ANALIZANDO")
        record2 = _fake_record(status="ANALIZANDO")

        # Side effects: initial query, then one record lookup per stale job
        db.execute.side_effect = [
            _fake_result_scalars([job1, job2]),
            _fake_result(record1),
            _fake_result(record2),
        ]

        count = await recover_stale_jobs(db)
        assert count == 2
        assert job1.status == "EN_COLA"
        assert job2.status == "EN_COLA"
        db.commit.assert_awaited_once()
