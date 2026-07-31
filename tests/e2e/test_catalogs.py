"""Tests E2E: catalogos (admin)."""

import pytest
from playwright.sync_api import Page


@pytest.mark.e2e
class TestCatalogsE2E:
    def test_catalogs_page_requires_auth(self, page: Page, live_server: str):
        page.goto(f"{live_server}/catalogs")
        page.wait_for_load_state("networkidle")
        assert "/login" in page.url or page.locator("form").is_visible()

    def test_catalogs_not_accessible_for_anonymous(self, page: Page, live_server: str):
        page.goto(f"{live_server}/catalogs")
        page.wait_for_load_state("networkidle")
        assert page.locator("form").count() > 0 or "/login" in page.url
