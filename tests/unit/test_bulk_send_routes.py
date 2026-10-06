from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.expenses.routes import (
    _is_stuck_sheets_send,
    bulk_delete_expenses,
    bulk_send_expenses,
)


def test_enviando_without_sheet_reference_is_stuck_after_grace_period():
    record = MagicMock()
    record.status = "ENVIANDO"
    record.sheet_name = None
    record.sheet_row = None
    record.sent_at = None
    record.updated_at = datetime(2026, 10, 6, 10, 0, tzinfo=UTC)

    now = datetime(2026, 10, 6, 10, 20, tzinfo=UTC)

    assert _is_stuck_sheets_send(record, now=now) is True


def test_enviando_with_complete_sheet_reference_is_not_stuck():
    record = MagicMock()
    record.status = "ENVIANDO"
    record.sheet_name = "Octubre-26"
    record.sheet_row = 12
    record.sent_at = datetime(2026, 10, 6, 10, 0, tzinfo=UTC)
    record.updated_at = datetime(2026, 10, 6, 10, 0, tzinfo=UTC)

    now = datetime(2026, 10, 6, 10, 30, tzinfo=UTC)

    assert _is_stuck_sheets_send(record, now=now) is False


def test_recent_enviando_without_reference_is_not_stuck_yet():
    record = MagicMock()
    record.status = "ENVIANDO"
    record.sheet_name = None
    record.sheet_row = None
    record.sent_at = None
    record.updated_at = datetime(2026, 10, 6, 10, 0, tzinfo=UTC)

    now = datetime(2026, 10, 6, 10, 5, tzinfo=UTC)

    assert _is_stuck_sheets_send(record, now=now) is False


async def test_bulk_send_without_selection_returns_visible_error():
    response = await bulk_send_expenses(record_ids=None, user=MagicMock(), db=AsyncMock())

    assert response.status_code == 400
    assert "Selecciona al menos un comprobante" in response.body.decode()


async def test_bulk_send_rejects_record_owned_by_another_user():
    record = MagicMock()
    record.id = "record-1"
    record.owner_id = "other-user"
    record.source_filename = "ticket.jpg"
    record.status = "PENDIENTE_DE_ENVIO"

    db = AsyncMock()
    db.execute.return_value = _scalar_result(record)

    user = MagicMock()
    user.role = "standard"
    user.id = "current-user"

    response = await bulk_send_expenses(record_ids=["record-1"], user=user, db=db)

    body = response.body.decode()
    assert "ticket.jpg: no autorizado" in body


async def test_bulk_send_recovers_stuck_enviando_before_retry(monkeypatch):
    record = MagicMock()
    record.id = "record-1"
    record.owner_id = "current-user"
    record.source_filename = "ticket.jpg"
    record.status = "ENVIANDO"
    record.sheet_name = None
    record.sheet_row = None
    record.sent_at = None
    record.updated_at = datetime.now(UTC) - timedelta(minutes=20)
    record.created_at = record.updated_at
    record.transaction_date = datetime(2026, 10, 6, tzinfo=UTC)
    record.amount = 100
    record.bank = "BBVA"
    record.group_code = "OP"
    record.category_id = "category-1"
    record.account_id = "account-1"

    db = AsyncMock()
    db.execute.return_value = _scalar_result(record)

    user = MagicMock()
    user.role = "standard"
    user.id = "current-user"

    send_mock = AsyncMock(return_value={"success": True, "row": 7, "tab": "Octubre-26"})
    monkeypatch.setattr("app.expenses.routes.send_expense_to_sheets", send_mock)

    response = await bulk_send_expenses(record_ids=["record-1"], user=user, db=db)

    assert response.status_code == 200
    assert record.status == "PENDIENTE_DE_ENVIO"
    db.commit.assert_awaited_once()
    send_mock.assert_awaited_once_with("record-1", "OP")
    assert "fila 7" in response.body.decode()


async def test_bulk_delete_without_selection_returns_visible_error():
    response = await bulk_delete_expenses(record_ids=None, user=MagicMock(), db=AsyncMock())

    assert response.status_code == 400
    assert "Selecciona al menos un comprobante" in response.body.decode()


async def test_bulk_delete_rejects_record_owned_by_another_user():
    record = MagicMock()
    record.id = "record-1"
    record.owner_id = "other-user"
    record.source_filename = "ticket.jpg"

    db = AsyncMock()
    db.execute.return_value = _scalar_result(record)

    user = MagicMock()
    user.role = "standard"
    user.id = "current-user"

    response = await bulk_delete_expenses(record_ids=["record-1"], user=user, db=db)

    body = response.body.decode()
    assert "ticket.jpg: no autorizado" in body
    db.delete.assert_not_called()
    db.commit.assert_not_called()


async def test_bulk_delete_deletes_authorized_record():
    record = MagicMock()
    record.id = "record-1"
    record.owner_id = "current-user"
    record.source_filename = "ticket.jpg"

    db = AsyncMock()
    db.execute.return_value = _scalar_result(record)

    user = MagicMock()
    user.role = "standard"
    user.id = "current-user"

    response = await bulk_delete_expenses(record_ids=["record-1"], user=user, db=db)

    body = response.body.decode()
    assert "ticket.jpg: eliminado" in body
    assert db.execute.await_count == 6
    db.delete.assert_awaited_once_with(record)
    db.commit.assert_awaited_once()


def _scalar_result(scalar_value):
    result = MagicMock()
    result.scalar_one_or_none = MagicMock(return_value=scalar_value)
    return result
