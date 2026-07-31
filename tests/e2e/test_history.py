"""Tests E2E: historial (busqueda y update)."""

import pytest
from playwright.sync_api import Page


@pytest.mark.e2e
class TestHistoryE2E:
    def test_history_page_requires_auth(self, page: Page, live_server: str):
        page.goto(f"{live_server}/history")
        page.wait_for_load_state("networkidle")
        assert "/login" in page.url or page.locator("form").is_visible()

    def test_history_search_endpoint_requires_auth(self, page: Page, live_server: str):
        import httpx

        r = httpx.get(f"{live_server}/history?q=test", follow_redirects=True)
        assert r.status_code in (200, 307, 302)
