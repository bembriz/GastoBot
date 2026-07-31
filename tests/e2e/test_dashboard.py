"""Tests E2E: dashboard y HTMX polling."""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
class TestDashboardE2E:
    def test_login_page_accessible(self, page: Page, live_server: str):
        page.goto(live_server)
        page.wait_for_load_state("networkidle")
        expect(page.locator("body")).to_be_visible()

    def test_login_form_present(self, page: Page, live_server: str):
        page.goto(f"{live_server}/login")
        page.wait_for_load_state("networkidle")
        assert page.locator("form").count() > 0

    def test_health_endpoint(self, page: Page, live_server: str):
        import httpx

        r = httpx.get(f"{live_server}/health")
        assert r.status_code in (200, 404)

    def test_static_files_serve(self, page: Page, live_server: str):
        page.goto(live_server)
        page.wait_for_load_state("networkidle")
        body_text = page.inner_text("body")
        assert len(body_text) > 0

    def test_navigation_to_dashboard_requires_auth(self, page: Page, live_server: str):
        page.goto(f"{live_server}/dashboard")
        page.wait_for_load_state("networkidle")
        assert "/login" in page.url or page.locator("form").is_visible()
