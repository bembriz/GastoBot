from datetime import date

from app.external.layout import (
    COLUMNAS,
    build_layout_row,
    get_month_label,
    month_key_to_label,
    month_label_to_key,
    normalize_month,
)


class TestMonthLabels:
    def test_long_label(self):
        assert get_month_label(date(2026, 7, 15)) == "Julio-2026"

    def test_label_to_key(self):
        assert month_label_to_key("Julio-2026") == "2026-07"

    def test_key_to_label(self):
        assert month_key_to_label("2026-07") == "Julio-2026"

    def test_invalid_label(self):
        assert month_label_to_key("Julio") is None
        assert month_label_to_key("Mes-2026") is None
        assert month_key_to_label("2026-13") is None

    def test_normalize_accepts_both_formats(self):
        assert normalize_month("Julio-2026") == "Julio-2026"
        assert normalize_month("2026-07") == "Julio-2026"
        assert normalize_month("otro") is None


class TestBuildLayoutRow:
    def test_full_record(self):
        class FakeRecord:
            transaction_date = date(2026, 1, 15)
            amount = 1500.50
            bank = "BBVA"
            transaction_type = "Credito"
            final_description = "BORAMAR-42-Compra super"
            ticket_description = "Compra super"

        row = build_layout_row(FakeRecord(), "CAT001", "ACC001")
        assert len(COLUMNAS) == len(row) == 16
        assert row[0] == "2026-01-15"
        assert row[1] == "CAT001"
        assert row[2] == "BORAMAR-42-Compra super"
        assert row[7] == "ACC001"
        assert row[8] == row[12] == "1500.5"
        assert row[13] == "Por reportar"
        assert row[14] == "BBVA"
        assert row[15] == "Credito"

    def test_minimal_record_defaults(self):
        class FakeRecord:
            transaction_date = None
            amount = None
            bank = None
            transaction_type = None
            final_description = None
            ticket_description = None

        row = build_layout_row(FakeRecord())
        assert len(row) == 16
        assert row[0] == ""
        assert row[8] == ""
        assert row[15] == "Transferencia"
