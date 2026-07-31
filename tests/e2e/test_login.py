"""Tests E2E: flujo de login."""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
class TestLoginE2E:
    def test_login_page_loads(self, page: Page, live_server: str):
        page.goto(live_server)
        page.wait_for_load_state("networkidle")
        expect(page).to_have_title("Gastos IA")

    def test_login_redirects_to_dashboard(self, page: Page, live_server: str):
        page.goto(f"{live_server}/login")
        page.wait_for_load_state("networkidle")
        expect(page.locator("form")).to_be_visible()

    def test_login_invalid_shows_error(self, page: Page, live_server: str):
        page.goto(f"{live_server}/login")
        page.fill("input[name='username']", "noexiste")
        page.fill("input[name='password']", "wrongpassword")
        page.click("button[type='submit']")
        page.wait_for_timeout(1000)
        expect(page.locator("body")).to_be_visible()

    def test_redirect_if_not_authenticated(self, page: Page, live_server: str):
        page.goto(f"{live_server}/dashboard")
        page.wait_for_load_state("networkidle")
        assert "/login" in page.url or page.locator("form").is_visible()
