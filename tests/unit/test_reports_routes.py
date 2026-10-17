from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.reports.routes import report_detail, reports_page


def _request():
    return MagicMock()


async def test_reports_redirects_when_not_logged_in():
    with patch("app.reports.routes.get_user_req", new=AsyncMock(return_value=None)):
        response = await reports_page(_request(), db=AsyncMock())

    assert response.status_code == 307
    assert response.headers["location"] == "/login"


async def test_reports_forbidden_for_standard_user():
    user = SimpleNamespace(role="standard")
    with patch("app.reports.routes.get_user_req", new=AsyncMock(return_value=user)):
        response = await reports_page(_request(), db=AsyncMock())

    assert response.status_code == 403
    assert "Acceso restringido" in response.body.decode()


async def test_reports_lists_months_for_admin():
    user = SimpleNamespace(role="admin", username="admin")
    ext_db = AsyncMock()
    months = [{"month_label": "Julio-2026", "count": 3, "total": 100}]
    with (
        patch("app.reports.routes.get_user_req", new=AsyncMock(return_value=user)),
        patch("app.reports.routes.external_session") as mock_ext,
        patch("app.reports.routes.list_months", new=AsyncMock(return_value=months)),
    ):
        mock_ext.return_value.__aenter__.return_value = ext_db
        response = await reports_page(_request(), month=None, db=AsyncMock())

    body = response.body.decode()
    assert response.status_code == 200
    assert "Reportes por mes" in body
    assert "Julio-2026" in body


async def test_reports_rejects_invalid_month():
    user = SimpleNamespace(role="admin", username="admin")
    with (
        patch("app.reports.routes.get_user_req", new=AsyncMock(return_value=user)),
        pytest.raises(HTTPException) as exc,
    ):
        await reports_page(_request(), month="nope", db=AsyncMock())

    assert exc.value.status_code == 400


async def test_report_detail_without_image():
    user = SimpleNamespace(role="admin", username="admin")
    row = SimpleNamespace(
        id=1,
        record_id=None,
        month_label="Julio-2026",
        expense_date="2026-07-15",
        category="CAT",
        description="OP-1-ticket",
        employee="RUBEN",
        paid_by="Empresa",
        activities="",
        accounting_date="",
        account="ACC",
        unit_price="10",
        quantity="1",
        include_taxes="",
        tax_amount="",
        total="10",
        estado="Por reportar",
        bank="BBVA",
        transaction_type="Transferencia",
        source="sheets_migration",
        synced_at=None,
        group_code=None,
        consecutive=None,
    )
    ext_db = AsyncMock()
    with (
        patch("app.reports.routes.get_user_req", new=AsyncMock(return_value=user)),
        patch("app.reports.routes.external_session") as mock_ext,
        patch("app.reports.routes.get_record", new=AsyncMock(return_value=row)),
    ):
        mock_ext.return_value.__aenter__.return_value = ext_db
        response = await report_detail(1, _request(), db=AsyncMock())

    body = response.body.decode()
    assert response.status_code == 200
    assert "Detalle — Julio-2026" in body
    assert "Sin imagen disponible" in body
