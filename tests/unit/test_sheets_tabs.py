from datetime import date
from unittest.mock import MagicMock, patch

from app.sheets.tabs import (
    COLUMNAS,
    MESES,
    build_sheet_row,
    ensure_month_tab,
    find_next_empty_row,
    get_month_tab_name,
)


class TestMonthTabName:
    def test_enero_2026(self):
        assert get_month_tab_name(date(2026, 1, 15)) == "Enero-26"

    def test_diciembre_2025(self):
        assert get_month_tab_name(date(2025, 12, 31)) == "Diciembre-25"

    def test_julio_2026(self):
        assert get_month_tab_name(date(2026, 7, 1)) == "Julio-26"

    def test_all_months(self):
        for m in range(1, 13):
            d = date(2026, m, 15)
            expected = f"{MESES[m - 1]}-26"
            assert get_month_tab_name(d) == expected


class TestEnsureMonthTab:
    def test_existing_worksheet(self):
        with patch("app.sheets.tabs.get_spreadsheet") as mock_gs:
            mock_sh = MagicMock()
            mock_ws = MagicMock()
            mock_ws.id = 12345
            mock_sh.worksheet.return_value = mock_ws
            mock_gs.return_value = mock_sh

            ws_id = ensure_month_tab("Enero-26")
            assert ws_id == 12345

    def test_new_worksheet_created(self):
        with patch("app.sheets.tabs.get_spreadsheet") as mock_gs:
            mock_sh = MagicMock()
            mock_sh.worksheet.side_effect = Exception("not found")
            mock_ws = MagicMock()
            mock_ws.id = 67890
            mock_sh.add_worksheet.return_value = mock_ws
            mock_gs.return_value = mock_sh

            with patch("app.sheets.tabs.time.sleep"):
                ws_id = ensure_month_tab("Febrero-26")
            assert ws_id == 67890
            mock_sh.add_worksheet.assert_called_once()
            mock_ws.append_row.assert_called_once_with(COLUMNAS)


class TestFindNextEmptyRow:
    def test_empty_sheet(self):
        with patch("app.sheets.tabs.get_spreadsheet") as mock_gs:
            mock_sh = MagicMock()
            mock_ws = MagicMock()
            mock_ws.get_all_values.return_value = [COLUMNAS]
            mock_sh.worksheet.return_value = mock_ws
            mock_gs.return_value = mock_sh

            row = find_next_empty_row("Enero-26")
            assert row == 2

    def test_with_data(self):
        with patch("app.sheets.tabs.get_spreadsheet") as mock_gs:
            mock_sh = MagicMock()
            mock_ws = MagicMock()
            mock_ws.get_all_values.return_value = [COLUMNAS, ["row1"], ["row2"]]
            mock_sh.worksheet.return_value = mock_ws
            mock_gs.return_value = mock_sh

            row = find_next_empty_row("Marzo-26")
            assert row == 4


class TestBuildSheetRow:
    def test_full_record(self):
        class FakeRecord:
            transaction_date = date(2026, 1, 15)
            amount = 1500.50
            bank = "BBVA"
            transaction_type = "Credito"
            final_description = "BORAMAR-42-Compra super"
            ticket_description = "Compra super"

        record = FakeRecord()
        row = build_sheet_row(record, "CAT001", "ACC001")
        assert len(row) == 16
        assert row[0] == "2026-01-15"
        assert row[1] == "CAT001"
        assert row[12] == "1500.5"
        assert row[7] == "ACC001"
        assert row[14] == "BBVA"
        assert row[15] == "Credito"

    def test_minimal_record(self):
        class FakeRecord:
            transaction_date = None
            amount = None
            bank = None
            transaction_type = None
            final_description = None
            ticket_description = None

        record = FakeRecord()
        row = build_sheet_row(record)
        assert len(row) == 16
        assert row[0] == ""
        assert row[12] == ""
        assert row[14] == ""
        assert row[15] == "Transferencia"
