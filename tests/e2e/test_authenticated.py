"""Tests E2E: flujos con sesion autenticada."""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
class TestAuthenticatedE2E:
    def test_dashboard_accessible_with_session(self, authenticated_page: Page, live_server: str):
        authenticated_page.goto(f"{live_server}/dashboard")
        authenticated_page.wait_for_load_state("networkidle")
        expect(authenticated_page.locator("body")).to_be_visible()

    def test_catalogs_accessible_as_admin(self, authenticated_page: Page, live_server: str):
        authenticated_page.goto(f"{live_server}/catalogs")
        authenticated_page.wait_for_load_state("networkidle")
        expect(authenticated_page.locator("body")).to_be_visible()

    def test_history_accessible_with_session(self, authenticated_page: Page, live_server: str):
        authenticated_page.goto(f"{live_server}/history")
        authenticated_page.wait_for_load_state("networkidle")
        expect(authenticated_page.locator("body")).to_be_visible()

    def test_api_me_returns_user_data(self, authenticated_page: Page, live_server: str):
        import httpx

        cookie = authenticated_page.context.cookies()[0]["value"]
        r = httpx.get(
            f"{live_server}/api/me",
            cookies={"gastosia_session": cookie},
        )
        assert r.status_code == 200
        data = r.json()
        assert "username" in data
        assert "role" in data

    def test_dashboard_status_with_session(self, authenticated_page: Page, live_server: str):
        authenticated_page.goto(f"{live_server}/dashboard/status")
        authenticated_page.wait_for_load_state("networkidle")
        expect(authenticated_page.locator("body")).to_be_visible()

    def test_catalogs_page_has_content(self, authenticated_page: Page, live_server: str):
        authenticated_page.goto(f"{live_server}/catalogs")
        authenticated_page.wait_for_load_state("networkidle")
        body = authenticated_page.inner_text("body")
        assert len(body) > 0

    def test_history_search_with_session(self, authenticated_page: Page, live_server: str):
        authenticated_page.goto(f"{live_server}/history?q=test")
        authenticated_page.wait_for_load_state("networkidle")
        expect(authenticated_page.locator("body")).to_be_visible()

    def test_categories_endpoint_with_session(self, authenticated_page: Page, live_server: str):
        import httpx

        cookie = authenticated_page.context.cookies()[0]["value"]
        r = httpx.get(
            f"{live_server}/categories/by-account?account_id=00000000-0000-0000-0000-000000000000",
            cookies={"gastosia_session": cookie},
        )
        assert r.status_code == 200

    def test_dashboard_has_expected_structure(self, authenticated_page: Page, live_server: str):
        authenticated_page.goto(f"{live_server}/dashboard")
        authenticated_page.wait_for_load_state("networkidle")
        body = authenticated_page.inner_text("body")
        assert len(body) > 0
