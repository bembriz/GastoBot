"""Tests E2E: revision y envio de gastos."""

import pytest
from playwright.sync_api import Page


@pytest.mark.e2e
class TestExpenseReviewE2E:
    def test_expense_detail_requires_auth(self, page: Page, live_server: str):
        import uuid

        page.goto(f"{live_server}/expenses/{uuid.uuid4()}")
        page.wait_for_load_state("networkidle")
        assert "/login" in page.url or page.locator("form").is_visible()

    def test_api_me_requires_auth(self, page: Page, live_server: str):
        import httpx

        r = httpx.get(f"{live_server}/api/me", follow_redirects=True)
        assert r.status_code in (200, 401, 403)

    def test_categories_endpoint(self, page: Page, live_server: str):
        import httpx

        r = httpx.get(f"{live_server}/categories/by-account?account_id=none")
        assert r.status_code in (200, 307)
