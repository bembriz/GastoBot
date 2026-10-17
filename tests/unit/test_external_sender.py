import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

from app.external.sender import send_expense

RECORD_ID = str(uuid.UUID("11111111-1111-1111-1111-111111111111"))


def _fake_record(status="PENDIENTE_DE_ENVIO", amount=1500.50):
    record = MagicMock()
    record.id = uuid.UUID(RECORD_ID)
    record.status = status
    record.transaction_date = date(2026, 7, 15)
    record.amount = amount
    record.bank = "BBVA"
    record.transaction_type = "Credito"
    record.ticket_description = "Compra super"
    record.final_description = None
    record.group_code = "OP"
    record.consecutive = None
    record.category_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
    record.account_id = uuid.UUID("33333333-3333-3333-3333-333333333333")
    record.sheet_name = None
    record.sheet_row = 5
    record.sent_at = None
    return record


def _scalar_result(scalar_value):
    result = MagicMock()
    result.scalar_one_or_none = MagicMock(return_value=scalar_value)
    return result


def _local_db(record, cat=None, acc=None):
    db = AsyncMock()
    db.add = MagicMock()
    db.execute = AsyncMock(
        side_effect=[
            _scalar_result(record),
            _scalar_result(cat),
            _scalar_result(acc),
            _scalar_result(None),
        ]
    )
    return db


class TestExternalSender:
    async def test_record_not_found(self):
        db = AsyncMock()
        db.execute.return_value = _scalar_result(None)
        with patch("app.external.sender.async_session") as mock_session:
            mock_session.return_value.__aenter__.return_value = db
            result = await send_expense(RECORD_ID, "OP")

        assert result["success"] is False
        assert "no encontrado" in str(result["error"])

    async def test_missing_required_fields(self):
        record = _fake_record(amount=None)
        db = _local_db(record)
        with patch("app.external.sender.async_session") as mock_session:
            mock_session.return_value.__aenter__.return_value = db
            result = await send_expense(RECORD_ID, "OP")

        assert result["success"] is False
        assert "Faltan" in str(result["error"])

    async def test_no_connectivity_leaves_pending(self):
        record = _fake_record()
        db = _local_db(record)
        with (
            patch("app.external.sender.async_session") as mock_session,
            patch(
                "app.external.sender.verify_connectivity",
                new=AsyncMock(return_value=False),
            ),
        ):
            mock_session.return_value.__aenter__.return_value = db
            result = await send_expense(RECORD_ID, "OP")

        assert result["success"] is False
        assert "Sin conexion" in str(result["error"])
        assert record.status == "PENDIENTE_DE_ENVIO"

    async def test_successful_send_writes_external_and_marks_enviado(self):
        record = _fake_record()
        cat = MagicMock(description="CAT001")
        acc = MagicMock(description="ACC001")
        db = _local_db(record, cat, acc)
        ext_db = AsyncMock()
        upsert = AsyncMock()
        move = AsyncMock(return_value=None)

        with (
            patch("app.external.sender.async_session") as mock_session,
            patch("app.external.sender.external_session") as mock_ext_session,
            patch(
                "app.external.sender.verify_connectivity",
                new=AsyncMock(return_value=True),
            ),
            patch(
                "app.external.sender.get_next_consecutive",
                new=AsyncMock(return_value=42),
            ),
            patch("app.external.sender.upsert_expense", new=upsert),
            patch("app.external.sender._move_image", new=move),
        ):
            mock_session.return_value.__aenter__.return_value = db
            mock_ext_session.return_value.__aenter__.return_value = ext_db

            result = await send_expense(RECORD_ID, "op")

        assert result["success"] is True
        assert result["tab"] == "Julio-2026"
        assert result["row"] is None
        assert result["consecutive"] == 42
        assert record.status == "ENVIADO"
        assert record.sheet_name == "Julio-2026"
        assert record.sheet_row is None
        assert record.group_code == "OP"
        assert record.final_description == "OP-42-Compra super"
        upsert.assert_awaited_once()
        values = upsert.await_args.args[1]
        assert values["record_id"] == record.id
        assert values["month_label"] == "Julio-2026"
        assert values["description"] == "OP-42-Compra super"
        assert values["category"] == "CAT001"
        assert values["account"] == "ACC001"
        ext_db.commit.assert_awaited_once()
        move.assert_awaited_once_with(db, record.id, "Julio-2026")

    async def test_external_error_marks_error_sheets(self):
        record = _fake_record()
        db = _local_db(record, None, None)
        ext_db = AsyncMock()
        upsert = AsyncMock(side_effect=RuntimeError("db caida"))

        with (
            patch("app.external.sender.async_session") as mock_session,
            patch("app.external.sender.external_session") as mock_ext_session,
            patch(
                "app.external.sender.verify_connectivity",
                new=AsyncMock(return_value=True),
            ),
            patch(
                "app.external.sender.get_next_consecutive",
                new=AsyncMock(return_value=7),
            ),
            patch("app.external.sender.upsert_expense", new=upsert),
        ):
            mock_session.return_value.__aenter__.return_value = db
            mock_ext_session.return_value.__aenter__.return_value = ext_db

            result = await send_expense(RECORD_ID, "OP")

        assert result["success"] is False
        assert "db caida" in str(result["error"])
        assert record.status == "ERROR_SHEETS"
