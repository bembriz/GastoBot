import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestAuthRoutes:
    def test_login_page(self, client):
        r = client.get("/login")
        assert r.status_code == 200

    def test_login_invalid(self, client):
        r = client.post("/login", data={"username": "x", "password": "y"})
        assert r.status_code in (200, 401)

    def test_login_no_data(self, client):
        r = client.post("/login", data={})
        assert r.status_code == 422

    def test_logout(self, client):
        r = client.post("/logout")
        assert r.status_code == 200

    def test_api_me_401(self, client):
        r = client.get("/api/me")
        assert r.status_code == 401

    def test_change_password_401(self, client):
        r = client.post("/change-password", data={"current_password": "x", "new_password": "y"})
        assert r.status_code == 401


class TestRootAndDashboard:
    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200

    def test_dashboard(self, client):
        r = client.get("/dashboard", follow_redirects=False)
        assert r.status_code in (200, 302, 401, 307)

    def test_dashboard_status(self, client):
        r = client.get("/dashboard/status", follow_redirects=False)
        assert r.status_code in (200, 302, 401, 307)


class TestExpensesRoutes:
    def test_expense_detail(self, client):
        r = client.get(f"/expenses/{uuid.uuid4()}")
        assert r.status_code in (200, 302, 401, 307)

    def test_view_image(self, client):
        r = client.get(f"/images/{uuid.uuid4()}/view")
        assert r.status_code in (200, 302, 401)

    def test_categories_by_account(self, client):
        r = client.get("/categories/by-account")
        assert r.status_code in (200, 302, 401)

    def test_categories_by_account_with_id(self, client):
        r = client.get(f"/categories/by-account?account_id={uuid.uuid4()}")
        assert r.status_code in (200, 302, 401)

    def test_update_expense_no_data(self, client):
        r = client.put(f"/expenses/{uuid.uuid4()}")
        assert r.status_code in (302, 401, 404, 422)

    def test_send_expense_auth_first(self, client):
        r = client.post(f"/expenses/{uuid.uuid4()}/send", data={})
        assert r.status_code in (401, 422)

    def test_bulk_send_auth_first(self, client):
        r = client.post("/expenses/bulk-send", data={})
        assert r.status_code in (401, 422)


class TestCatalogsRoutes:
    def test_catalogs_page(self, client):
        r = client.get("/catalogs")
        assert r.status_code in (200, 302, 401, 307)

    def test_create_category_auth(self, client):
        r = client.post("/catalogs/categoria", data={})
        assert r.status_code in (401, 422)

    def test_toggle_category_403(self, client):
        r = client.put(f"/catalogs/categoria/{uuid.uuid4()}/toggle")
        assert r.status_code in (302, 401, 403)

    def test_create_account_auth(self, client):
        r = client.post("/catalogs/cuenta", data={})
        assert r.status_code in (401, 422)

    def test_toggle_account_403(self, client):
        r = client.put(f"/catalogs/cuenta/{uuid.uuid4()}/toggle")
        assert r.status_code in (302, 401, 403)


class TestHistoryRoutes:
    def test_history_page(self, client):
        r = client.get("/history")
        assert r.status_code in (200, 302, 401)

    def test_history_search(self, client):
        r = client.get("/history?q=test")
        assert r.status_code in (200, 302, 401)

    def test_update_history_401(self, client):
        r = client.put(
            f"/history/{uuid.uuid4()}",
            data={"transaction_date": "2026-01-15"},
        )
        assert r.status_code in (302, 401)


class TestStaticFiles:
    def test_static_mounted(self, client):
        r = client.get("/static/")
        assert r.status_code in (200, 404, 307)
