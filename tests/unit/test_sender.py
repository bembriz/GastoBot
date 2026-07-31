import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

from app.sheets.sender import send_expense

RECORD_ID = str(uuid.UUID("11111111-1111-1111-1111-111111111111"))


def _fake_record(status="REQUIERE_REVISION", amount=1500.50):
    record = MagicMock()
    record.id = RECORD_ID
    record.status = status
    record.transaction_date = date(2026, 1, 15)
    record.amount = amount
    record.bank = "BBVA"
    record.transaction_type = "Credito"
    record.ticket_description = "Compra super"
    record.final_description = None
    record.group_code = "BORAMAR"
    record.consecutive = None
    record.category_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
    record.account_id = uuid.UUID("33333333-3333-3333-3333-333333333333")
    record.sheet_name = None
    record.sheet_row = None
    record.sent_at = None
    return record


class TestSendExpense:
    async def test_record_not_found(self):
        with patch("app.sheets.sender.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_db.execute.return_value = _scalar_result(None)
            mock_session.return_value.__aenter__.return_value = mock_db

            result = await send_expense(RECORD_ID, "BORAMAR")
            assert result["success"] is False
            assert "no encontrado" in result["error"]

    async def test_missing_required_fields(self):
        record = _fake_record(amount=None)

        with patch("app.sheets.sender.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_db.execute.return_value = _scalar_result(record)
            mock_session.return_value.__aenter__.return_value = mock_db

            result = await send_expense(RECORD_ID, "BORAMAR")
            assert result["success"] is False
            assert "Faltan" in result["error"]

    async def test_no_connectivity_sets_pendiente(self):
        record = _fake_record()

        with (
            patch("app.sheets.sender.async_session") as mock_session,
            patch("app.sheets.sender.verify_connectivity", return_value=False),
        ):
            mock_db = AsyncMock()
            mock_db.execute.return_value = _scalar_result(record)
            mock_session.return_value.__aenter__.return_value = mock_db

            result = await send_expense(RECORD_ID, "BORAMAR")
            assert result["success"] is False
            assert record.status == "PENDIENTE_DE_ENVIO"
            assert mock_db.commit.call_count >= 1

    async def test_successful_send_full_flow(self):
        record = _fake_record()
        cat_mock = MagicMock()
        cat_mock.description = "CAT001"
        acc_mock = MagicMock()
        acc_mock.description = "ACC001"

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        mock_db.execute.side_effect = [
            _scalar_result(record),
            _scalar_result(cat_mock),
            _scalar_result(acc_mock),
        ]

        with (
            patch("app.sheets.sender.async_session") as mock_session,
            patch("app.sheets.sender.verify_connectivity", return_value=True),
            patch(
                "app.sheets.sender.get_next_consecutive",
                new=AsyncMock(return_value="BORAMAR-42"),
            ),
            patch("app.sheets.sender.get_month_tab_name", return_value="Enero-26"),
            patch("app.sheets.sender.ensure_month_tab") as mock_ensure,
            patch("app.sheets.sender.find_next_empty_row", return_value=5),
            patch("app.sheets.sender.build_sheet_row", return_value=["col"] * 16),
            patch("app.sheets.sender.get_spreadsheet") as mock_gs,
            patch("app.sheets.sender.time.sleep"),
        ):
            mock_session.return_value.__aenter__.return_value = mock_db

            mock_ws = MagicMock()
            mock_sh = MagicMock()
            mock_sh.worksheet.return_value = mock_ws
            mock_gs.return_value = mock_sh

            result = await send_expense(RECORD_ID, "BORAMAR")

            assert result["success"] is True
            assert result["tab"] == "Enero-26"
            assert result["row"] == 5
            assert result["consecutive"] == "BORAMAR-42"
            assert record.status == "ENVIADO"
            assert record.consecutive == "BORAMAR-42"
            mock_ws.insert_row.assert_called_once()
            mock_ensure.assert_called_once_with("Enero-26")

    async def test_send_exception_reverts_to_pendiente(self):
        record = _fake_record()
        cat_mock = MagicMock()
        cat_mock.description = "CAT001"
        acc_mock = MagicMock()
        acc_mock.description = "ACC001"

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        mock_db.execute.side_effect = [
            _scalar_result(record),
            _scalar_result(cat_mock),
            _scalar_result(acc_mock),
        ]

        with (
            patch("app.sheets.sender.async_session") as mock_session,
            patch("app.sheets.sender.verify_connectivity", return_value=True),
            patch(
                "app.sheets.sender.get_next_consecutive",
                new=AsyncMock(return_value="BORAMAR-42"),
            ),
            patch("app.sheets.sender.get_month_tab_name", return_value="Enero-26"),
            patch("app.sheets.sender.ensure_month_tab"),
            patch("app.sheets.sender.find_next_empty_row", return_value=5),
            patch("app.sheets.sender.build_sheet_row", return_value=["col"] * 16),
            patch("app.sheets.sender.get_spreadsheet") as mock_gs,
        ):
            mock_session.return_value.__aenter__.return_value = mock_db
            mock_gs.side_effect = Exception("API error")

            result = await send_expense(RECORD_ID, "BORAMAR")

            assert result["success"] is False
            assert record.status == "PENDIENTE_DE_ENVIO"

    async def test_catalog_not_found_uses_empty_strings(self):
        record = _fake_record()

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        mock_db.execute.side_effect = [
            _scalar_result(record),
            _scalar_result(None),
            _scalar_result(None),
        ]

        with (
            patch("app.sheets.sender.async_session") as mock_session,
            patch("app.sheets.sender.verify_connectivity", return_value=True),
            patch(
                "app.sheets.sender.get_next_consecutive",
                new=AsyncMock(return_value="BORAMAR-42"),
            ),
            patch("app.sheets.sender.get_month_tab_name", return_value="Enero-26"),
            patch("app.sheets.sender.ensure_month_tab"),
            patch("app.sheets.sender.find_next_empty_row", return_value=5),
            patch("app.sheets.sender.build_sheet_row") as mock_build,
            patch("app.sheets.sender.get_spreadsheet") as mock_gs,
            patch("app.sheets.sender.time.sleep"),
        ):
            mock_session.return_value.__aenter__.return_value = mock_db
            mock_ws = MagicMock()
            mock_sh = MagicMock()
            mock_sh.worksheet.return_value = mock_ws
            mock_gs.return_value = mock_sh

            await send_expense(RECORD_ID, "BORAMAR")
            mock_build.assert_called_once()
            args, _ = mock_build.call_args
            assert args[2] == ""


def _scalar_result(scalar_value):
    result = MagicMock()
    result.scalar_one_or_none = MagicMock(return_value=scalar_value)
    return result
