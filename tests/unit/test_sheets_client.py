from unittest.mock import MagicMock, patch

import pytest

from app.sheets.client import _get_client, get_spreadsheet, verify_connectivity


class TestGetClient:
    def test_creates_client_once(self):
        with (
            patch("app.sheets.client.Path.exists", return_value=True),
            patch("app.sheets.client.gspread.service_account") as mock_sa,
        ):
            mock_sa.return_value = "client-1"
            from app.sheets import client as mod

            mod._client = None
            c1 = _get_client()
            c2 = _get_client()
            assert c1 == c2
            assert mock_sa.call_count == 1

    def test_missing_credentials_raises(self):
        with patch("app.sheets.client.Path.exists", return_value=False):
            from app.sheets import client as mod

            mod._client = None
            with pytest.raises(FileNotFoundError):
                _get_client()


class TestGetSpreadsheet:
    def test_creates_spreadsheet_once(self):
        with patch("app.sheets.client._get_client") as mock_get_client:
            mock_gc = MagicMock()
            mock_gc.open_by_key.return_value = "sheet-1"
            mock_get_client.return_value = mock_gc

            from app.sheets import client as mod

            mod._spreadsheet = None
            s1 = get_spreadsheet()
            s2 = get_spreadsheet()
            assert s1 == s2
            assert mock_gc.open_by_key.call_count == 1


class TestVerifyConnectivity:
    def test_online_returns_true(self):
        with patch("app.sheets.client.get_spreadsheet") as mock_gs:
            mock_sheet = MagicMock()
            mock_sheet.title = "Reporte de gastos"
            mock_gs.return_value = mock_sheet
            from app.sheets import client as mod

            mod._last_connectivity_check = 0
            assert verify_connectivity() is True

    def test_offline_returns_false(self):
        with patch("app.sheets.client.get_spreadsheet") as mock_gs:
            mock_gs.side_effect = Exception("offline")
            from app.sheets import client as mod

            mod._last_connectivity_check = 0
            assert verify_connectivity() is False

    def test_cached_result_within_30s(self):
        from app.sheets import client as mod

        mod._last_connectivity_check = 1e9
        mod._is_online = False
        assert verify_connectivity() is False
