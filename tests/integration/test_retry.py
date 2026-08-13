"""Tests del endpoint de reenvio (retry) de imagenes con error de extraccion."""

import uuid

import httpx
import pytest_asyncio
from sqlalchemy import select

from app.auth.session import create_session
from app.database.models import ExpenseRecord, ExtractionRun, ProcessingQueue
from app.main import app

COOKIE_NAME = "gastosia_session"


def _cookie(user) -> str:
    return create_session(user.id, user.username, user.role)


def _make_client(user) -> httpx.AsyncClient:
    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")
    client.cookies.set(COOKIE_NAME, _cookie(user))
    return client


async def _make_error_record(db_session, owner_id, status="ERROR_PROCESAMIENTO") -> ExpenseRecord:
    record = ExpenseRecord(
        owner_id=owner_id,
        image_hash=f"sha_retry_{uuid.uuid4().hex[:16]}",
        status=status,
        source_filename=f"retry_{uuid.uuid4().hex[:8]}.jpg",
        amount=10.0,
        bank="BBVA",
        transaction_type="Credito",
    )
    db_session.add(record)
    await db_session.flush()

    if status == "ERROR_PROCESAMIENTO":
        db_session.add(
            ProcessingQueue(record_id=record.id, status="ERROR_PERMANENTE", last_error="boom")
        )
        db_session.add(
            ExtractionRun(record_id=record.id, model_name="kimi", error_message="Kimi 429")
        )
    await db_session.commit()
    await db_session.refresh(record)
    return record


async def _cleanup_record(db_session, record_id) -> None:
    for model, col in (
        (ExtractionRun, ExtractionRun.record_id),
        (ProcessingQueue, ProcessingQueue.record_id),
    ):
        result = await db_session.execute(select(model).where(col == record_id))
        for obj in result.scalars().all():
            await db_session.delete(obj)
    rec = (
        await db_session.execute(select(ExpenseRecord).where(ExpenseRecord.id == record_id))
    ).scalar_one_or_none()
    if rec:
        await db_session.delete(rec)
    await db_session.commit()


@pytest_asyncio.fixture(loop_scope="function")
async def error_record(db_session, test_admin_user):
    record = await _make_error_record(db_session, test_admin_user.id)
    yield record
    await _cleanup_record(db_session, record.id)


class TestRetryExpense:
    async def test_retry_resets_record_and_queue(self, db_session, test_admin_user, error_record):
        record_id = error_record.id
        async with _make_client(test_admin_user) as client:
            r = await client.post(f"/expenses/{record_id}/retry")
        assert r.status_code == 200
        assert "Reenviado" in r.text

        from app.database.session import async_session

        async with async_session() as fresh:
            rec = (
                await fresh.execute(select(ExpenseRecord).where(ExpenseRecord.id == record_id))
            ).scalar_one()
            q = (
                await fresh.execute(
                    select(ProcessingQueue).where(ProcessingQueue.record_id == record_id)
                )
            ).scalar_one()

        assert rec.status == "EN_COLA"
        assert rec.amount is None
        assert rec.bank is None
        assert rec.transaction_type is None
        assert q.status == "EN_COLA"
        assert q.attempts == 0
        assert q.last_error is None
        assert q.claimed_at is None
        assert q.completed_at is None

    async def test_retry_not_owner_forbidden(self, db_session, test_admin_user, test_standard_user):
        record = await _make_error_record(db_session, test_admin_user.id)
        try:
            async with _make_client(test_standard_user) as client:
                r = await client.post(f"/expenses/{record.id}/retry")
            assert r.status_code == 403
        finally:
            await _cleanup_record(db_session, record.id)

    async def test_retry_conflict_when_not_error(self, db_session, test_admin_user):
        record = await _make_error_record(
            db_session, test_admin_user.id, status="REQUIERE_REVISION"
        )
        try:
            async with _make_client(test_admin_user) as client:
                r = await client.post(f"/expenses/{record.id}/retry")
            assert r.status_code == 409
        finally:
            await _cleanup_record(db_session, record.id)

    async def test_retry_404(self, test_admin_user):
        async with _make_client(test_admin_user) as client:
            r = await client.post(f"/expenses/{uuid.uuid4()}/retry")
        assert r.status_code == 404

    async def test_dashboard_errors_standard_sees_only_own(
        self, db_session, test_admin_user, test_standard_user
    ):
        admin_record = await _make_error_record(db_session, test_admin_user.id)
        std_record = await _make_error_record(db_session, test_standard_user.id)
        try:
            async with _make_client(test_standard_user) as client:
                r = await client.get("/dashboard/errors")
            assert r.status_code == 200
            assert std_record.source_filename in r.text
            assert admin_record.source_filename not in r.text
        finally:
            await _cleanup_record(db_session, admin_record.id)
            await _cleanup_record(db_session, std_record.id)
