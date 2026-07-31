"""Tests de rutas con sesion autenticada para ejercitar todos los paths."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.auth.session import create_session
from tests.conftest import (
    TEST_USER_ADMIN_PASSWORD,
)

COOKIE_NAME = "gastosia_session"


@pytest.fixture
def client():
    from app.main import app

    return TestClient(app)


def _make_cookie(user_id, username, role):
    return create_session(uuid.UUID(str(user_id)), username, role)


class TestAuthRoutes:
    def test_login_page(self, client, _test_users_setup):
        r = client.get("/login")
        assert r.status_code == 200

    def test_login_invalid_password(self, client, _test_users_setup, test_admin_user):
        r = client.post(
            "/login",
            data={"username": test_admin_user.username, "password": "wrong-password!!"},
        )
        assert r.status_code in (200, 401)

    def test_logout(self, client, _test_users_setup):
        r = client.post("/logout")
        assert r.status_code == 200

    def test_change_password_wrong_current(self, client, _test_users_setup, test_admin_user):
        cookie = _make_cookie(test_admin_user.id, test_admin_user.username, test_admin_user.role)
        client.cookies.set(COOKIE_NAME, cookie)
        r = client.post(
            "/change-password",
            data={"current_password": "wrong", "new_password": "newsecret123"},
        )
        assert r.status_code in (200, 401, 403)

    def test_change_password_too_short(self, client, _test_users_setup, test_admin_user):
        cookie = _make_cookie(test_admin_user.id, test_admin_user.username, test_admin_user.role)
        client.cookies.set(COOKIE_NAME, cookie)
        r = client.post(
            "/change-password",
            data={"current_password": TEST_USER_ADMIN_PASSWORD, "new_password": "123"},
        )
        assert r.status_code in (200, 401)


class TestExpensesRoutes:
    def test_dashboard_redirects(self, client, _test_users_setup):
        r = client.get("/dashboard", follow_redirects=False)
        assert r.status_code in (200, 302, 307)

    def test_dashboard_with_session(self, client, _test_users_setup, test_admin_user):
        cookie = _make_cookie(test_admin_user.id, test_admin_user.username, test_admin_user.role)
        client.cookies.set(COOKIE_NAME, cookie)
        r = client.get("/dashboard")
        assert r.status_code == 200

    def test_dashboard_status_with_session(self, client, _test_users_setup, test_admin_user):
        cookie = _make_cookie(test_admin_user.id, test_admin_user.username, test_admin_user.role)
        client.cookies.set(COOKIE_NAME, cookie)
        r = client.get("/dashboard/status")
        assert r.status_code == 200

    def test_expense_detail_404(self, client, _test_users_setup, test_admin_user):
        cookie = _make_cookie(test_admin_user.id, test_admin_user.username, test_admin_user.role)
        client.cookies.set(COOKIE_NAME, cookie)
        r = client.get(f"/expenses/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_update_expense_404(self, client, _test_users_setup, test_admin_user):
        cookie = _make_cookie(test_admin_user.id, test_admin_user.username, test_admin_user.role)
        client.cookies.set(COOKIE_NAME, cookie)
        r = client.put(
            f"/expenses/{uuid.uuid4()}",
            data={"transaction_date": "2026-01-15", "group_code": "VAL"},
        )
        assert r.status_code == 404

    def test_send_expense(self, client, _test_users_setup, test_admin_user):
        cookie = _make_cookie(test_admin_user.id, test_admin_user.username, test_admin_user.role)
        client.cookies.set(COOKIE_NAME, cookie)
        with patch(
            "app.expenses.routes.send_expense_to_sheets",
            new=AsyncMock(return_value={"success": False, "error": "no encontrado"}),
        ):
            r = client.post(
                f"/expenses/{uuid.uuid4()}/send",
                data={"group_code": "VAL"},
            )
            assert r.status_code == 200

    def test_categories_by_account(self, client, _test_users_setup, test_admin_user):
        cookie = _make_cookie(test_admin_user.id, test_admin_user.username, test_admin_user.role)
        client.cookies.set(COOKIE_NAME, cookie)
        r = client.get("/categories/by-account?account_id=0")
        assert r.status_code == 200


class TestCatalogsRoutes:
    def test_catalogs_page_as_admin(self, client, _test_users_setup, test_admin_user):
        cookie = _make_cookie(test_admin_user.id, test_admin_user.username, test_admin_user.role)
        client.cookies.set(COOKIE_NAME, cookie)
        r = client.get("/catalogs")
        assert r.status_code == 200

    def test_catalogs_page_as_standard(self, client, _test_users_setup, test_standard_user):
        cookie = _make_cookie(
            test_standard_user.id, test_standard_user.username, test_standard_user.role
        )
        client.cookies.set(COOKIE_NAME, cookie)
        r = client.get("/catalogs")
        assert r.status_code == 403

    def test_create_category(self, client, _test_users_setup, test_admin_user):
        cookie = _make_cookie(test_admin_user.id, test_admin_user.username, test_admin_user.role)
        client.cookies.set(COOKIE_NAME, cookie)
        r = client.post(
            "/catalogs/categoria",
            data={"code": f"CAT{uuid.uuid4().hex[:4]}", "description": "Test category"},
        )
        assert r.status_code == 200

    def test_create_account(self, client, _test_users_setup, test_admin_user):
        cookie = _make_cookie(test_admin_user.id, test_admin_user.username, test_admin_user.role)
        client.cookies.set(COOKIE_NAME, cookie)
        r = client.post(
            "/catalogs/cuenta",
            data={"code": f"ACC{uuid.uuid4().hex[:4]}", "description": "Test account"},
        )
        assert r.status_code == 200


class TestHistoryRoutes:
    def test_history_page(self, client, _test_users_setup, test_admin_user):
        cookie = _make_cookie(test_admin_user.id, test_admin_user.username, test_admin_user.role)
        client.cookies.set(COOKIE_NAME, cookie)
        r = client.get("/history")
        assert r.status_code == 200

    def test_history_search(self, client, _test_users_setup, test_admin_user):
        cookie = _make_cookie(test_admin_user.id, test_admin_user.username, test_admin_user.role)
        client.cookies.set(COOKIE_NAME, cookie)
        r = client.get("/history?q=BBVA")
        assert r.status_code == 200

    def test_update_history_404(self, client, _test_users_setup, test_admin_user):
        cookie = _make_cookie(test_admin_user.id, test_admin_user.username, test_admin_user.role)
        client.cookies.set(COOKIE_NAME, cookie)
        r = client.put(
            f"/history/{uuid.uuid4()}",
            data={"transaction_date": "2026-01-15", "amount": "100.50", "bank": "BBVA"},
        )
        assert r.status_code == 200
        assert "No encontrado" in r.text


class TestAuthLoginSuccess:
    def test_login_valid_admin(self, client, _test_users_setup, test_admin_user):
        from app.auth.session import verify_session

        r = client.post(
            "/login",
            data={
                "username": test_admin_user.username,
                "password": TEST_USER_ADMIN_PASSWORD,
            },
        )
        assert r.status_code == 200
        cookie = r.cookies.get(COOKIE_NAME)
        if cookie:
            session_data = verify_session(cookie)
            assert session_data is not None

    def test_api_me_with_session(self, client, _test_users_setup, test_admin_user):
        cookie = _make_cookie(test_admin_user.id, test_admin_user.username, test_admin_user.role)
        client.cookies.set(COOKIE_NAME, cookie)
        r = client.get("/api/me")
        assert r.status_code == 200
        data = r.json()
        assert data["username"] == test_admin_user.username

    def test_change_password_success(self, client, _test_users_setup, test_admin_user, db_session):
        cookie = _make_cookie(test_admin_user.id, test_admin_user.username, test_admin_user.role)
        client.cookies.set(COOKIE_NAME, cookie)
        r = client.post(
            "/change-password",
            data={
                "current_password": TEST_USER_ADMIN_PASSWORD,
                "new_password": "newpassword12345",
            },
        )
        assert r.status_code == 200


class TestExpensesWithRecord:
    def test_expense_detail_with_real_record(
        self, client, _test_users_setup, test_admin_user, db_session
    ):
        from app.database.models import ExpenseRecord, ImageFile

        hash_val = f"sha_det_{uuid.uuid4().hex[:16]}"
        import tempfile

        img_path = tempfile.mktemp(suffix=".jpg")
        from PIL import Image as PILImage

        img = PILImage.new("RGB", (10, 10))
        img.save(img_path)

        async def _create():
            record = ExpenseRecord(
                owner_id=test_admin_user.id,
                image_hash=hash_val,
                status="REQUIERE_REVISION",
                source_filename="detail_test.jpg",
            )
            db_session.add(record)
            await db_session.flush()

            img_file = ImageFile(
                record_id=record.id,
                original_path=img_path,
                sha256_hash=hash_val,
                file_size=100,
                mime_type="image/jpeg",
                owner_folder="Ruben",
            )
            db_session.add(img_file)
            await db_session.commit()
            await db_session.refresh(record)
            return record.id

        import asyncio

        loop = asyncio.get_event_loop()
        rid = loop.run_until_complete(_create())

        cookie = _make_cookie(test_admin_user.id, test_admin_user.username, test_admin_user.role)
        client.cookies.set(COOKIE_NAME, cookie)

        r = client.get(f"/expenses/{rid}")
        assert r.status_code == 200

    def test_view_image_with_session(self, client, _test_users_setup, test_admin_user, db_session):
        from app.database.models import ExpenseRecord, ImageFile

        hash_val = f"sha_view_{uuid.uuid4().hex[:16]}"
        import tempfile

        img_path = tempfile.mktemp(suffix=".jpg")
        from PIL import Image as PILImage

        img = PILImage.new("RGB", (10, 10))
        img.save(img_path)

        async def _create():
            record = ExpenseRecord(
                owner_id=test_admin_user.id,
                image_hash=hash_val,
                status="REQUIERE_REVISION",
                source_filename="view_test.jpg",
            )
            db_session.add(record)
            await db_session.flush()

            img_file = ImageFile(
                record_id=record.id,
                original_path=img_path,
                sha256_hash=hash_val,
                file_size=100,
                mime_type="image/jpeg",
                owner_folder="Ruben",
            )
            db_session.add(img_file)
            await db_session.commit()
            await db_session.refresh(record)
            return record.id

        import asyncio

        loop = asyncio.get_event_loop()
        rid = loop.run_until_complete(_create())

        cookie = _make_cookie(test_admin_user.id, test_admin_user.username, test_admin_user.role)
        client.cookies.set(COOKIE_NAME, cookie)

        r = client.get(f"/images/{rid}/view")
        assert r.status_code == 200

    def test_history_page_as_standard(self, client, _test_users_setup, test_standard_user):
        cookie = _make_cookie(
            test_standard_user.id, test_standard_user.username, test_standard_user.role
        )
        client.cookies.set(COOKIE_NAME, cookie)
        r = client.get("/history")
        assert r.status_code == 200

    def test_update_expense_success(self, client, _test_users_setup, test_admin_user, db_session):
        from app.database.models import ExpenseRecord

        hash_val = f"sha_up_{uuid.uuid4().hex[:16]}"

        async def _create():
            record = ExpenseRecord(
                owner_id=test_admin_user.id,
                image_hash=hash_val,
                status="REQUIERE_REVISION",
                source_filename=f"test_{uuid.uuid4().hex[:8]}.jpg",
            )
            db_session.add(record)
            await db_session.commit()
            await db_session.refresh(record)
            return record.id

        import asyncio

        loop = asyncio.get_event_loop()
        rid = loop.run_until_complete(_create())

        cookie = _make_cookie(test_admin_user.id, test_admin_user.username, test_admin_user.role)
        client.cookies.set(COOKIE_NAME, cookie)

        r = client.put(
            f"/expenses/{rid}",
            data={
                "transaction_date": "2026-01-15",
                "group_code": "VAL",
                "ticket_description": "Test desc",
                "amount": "500.00",
                "bank": "BBVA",
                "transaction_type": "Credito",
            },
        )
        assert r.status_code == 200

    def test_update_with_category_account(
        self, client, _test_users_setup, test_admin_user, db_session
    ):
        from app.database.models import CatalogCache, ExpenseRecord

        hash_val = f"sha_ca_{uuid.uuid4().hex[:16]}"

        async def _setup():
            cat = CatalogCache(
                catalog_type="categoria", code=f"TCAT{uuid.uuid4().hex[:4]}", description="Test Cat"
            )
            acc = CatalogCache(
                catalog_type="cuenta", code=f"TACC{uuid.uuid4().hex[:4]}", description="Test Acc"
            )
            db_session.add_all([cat, acc])
            await db_session.flush()

            record = ExpenseRecord(
                owner_id=test_admin_user.id,
                image_hash=hash_val,
                status="REQUIERE_REVISION",
                source_filename=f"test2_{uuid.uuid4().hex[:8]}.jpg",
            )
            db_session.add(record)
            await db_session.commit()
            await db_session.refresh(record)
            return record.id, cat.id, acc.id

        import asyncio

        loop = asyncio.get_event_loop()
        rid, cid, aid = loop.run_until_complete(_setup())

        cookie = _make_cookie(test_admin_user.id, test_admin_user.username, test_admin_user.role)
        client.cookies.set(COOKIE_NAME, cookie)

        r = client.put(
            f"/expenses/{rid}",
            data={
                "transaction_date": "2026-02-20",
                "group_code": "OP",
                "ticket_description": "with cat",
                "amount": "250.50",
                "bank": "SANTANDER",
                "transaction_type": "Transferencia",
                "category_id": str(cid),
                "account_id": str(aid),
            },
        )
        assert r.status_code == 200

    def test_bulk_send_empty(self, client, _test_users_setup, test_admin_user):
        cookie = _make_cookie(test_admin_user.id, test_admin_user.username, test_admin_user.role)
        client.cookies.set(COOKIE_NAME, cookie)

        r = client.post("/expenses/bulk-send", data={"record_ids": []})
        assert r.status_code in (200, 422)

    def test_bulk_send_with_invalid_id(self, client, _test_users_setup, test_admin_user):
        from unittest.mock import AsyncMock, patch

        cookie = _make_cookie(test_admin_user.id, test_admin_user.username, test_admin_user.role)
        client.cookies.set(COOKIE_NAME, cookie)

        with patch(
            "app.expenses.routes.send_expense_to_sheets",
            new=AsyncMock(return_value={"success": True, "row": 5, "tab": "Jul-26"}),
        ):
            r = client.post(
                "/expenses/bulk-send",
                data={"record_ids": [str(uuid.uuid4())]},
            )
            assert r.status_code == 200


class TestCatalogsToggle:
    def test_toggle_category(self, client, _test_users_setup, test_admin_user, db_session):
        from app.database.models import CatalogCache

        code = f"TTOG{uuid.uuid4().hex[:4]}"

        async def _setup():
            cat = CatalogCache(catalog_type="categoria", code=code, description="Toggle Cat")
            db_session.add(cat)
            await db_session.commit()
            await db_session.refresh(cat)
            return cat.id

        import asyncio

        loop = asyncio.get_event_loop()
        cid = loop.run_until_complete(_setup())

        cookie = _make_cookie(test_admin_user.id, test_admin_user.username, test_admin_user.role)
        client.cookies.set(COOKIE_NAME, cookie)

        r = client.put(f"/catalogs/categoria/{cid}/toggle")
        assert r.status_code == 200

    def test_toggle_account(self, client, _test_users_setup, test_admin_user, db_session):
        from app.database.models import CatalogCache

        code = f"ATOG{uuid.uuid4().hex[:4]}"

        async def _setup():
            acc = CatalogCache(catalog_type="cuenta", code=code, description="Toggle Acc")
            db_session.add(acc)
            await db_session.commit()
            await db_session.refresh(acc)
            return acc.id

        import asyncio

        loop = asyncio.get_event_loop()
        aid = loop.run_until_complete(_setup())

        cookie = _make_cookie(test_admin_user.id, test_admin_user.username, test_admin_user.role)
        client.cookies.set(COOKIE_NAME, cookie)

        r = client.put(f"/catalogs/cuenta/{aid}/toggle")
        assert r.status_code == 200

    def test_toggle_not_found(self, client, _test_users_setup, test_admin_user):
        cookie = _make_cookie(test_admin_user.id, test_admin_user.username, test_admin_user.role)
        client.cookies.set(COOKIE_NAME, cookie)

        r = client.put(f"/catalogs/categoria/{uuid.uuid4()}/toggle")
        assert r.status_code == 200


class TestHistoryUpdate:
    def test_update_history_with_record(
        self, client, _test_users_setup, test_admin_user, db_session
    ):
        from datetime import date

        from app.database.models import ExpenseRecord

        hash_val = f"sha_h_{uuid.uuid4().hex[:16]}"

        async def _setup():
            record = ExpenseRecord(
                owner_id=test_admin_user.id,
                image_hash=hash_val,
                status="ENVIADO",
                source_filename=f"hist_{uuid.uuid4().hex[:8]}.jpg",
                transaction_date=date(2026, 3, 1),
                amount=300.00,
                bank="BBVA",
            )
            db_session.add(record)
            await db_session.commit()
            await db_session.refresh(record)
            return record.id

        import asyncio

        loop = asyncio.get_event_loop()
        rid = loop.run_until_complete(_setup())

        cookie = _make_cookie(test_admin_user.id, test_admin_user.username, test_admin_user.role)
        client.cookies.set(COOKIE_NAME, cookie)

        r = client.put(
            f"/history/{rid}",
            data={"transaction_date": "2026-03-15", "amount": "450.00", "bank": "SANTANDER"},
        )
        assert r.status_code == 200
        assert "Actualizado" in r.text

    def test_update_history_field_unchanged(
        self, client, _test_users_setup, test_admin_user, db_session
    ):
        from app.database.models import ExpenseRecord

        hash_val = f"sha_h2_{uuid.uuid4().hex[:16]}"

        async def _setup():
            record = ExpenseRecord(
                owner_id=test_admin_user.id,
                image_hash=hash_val,
                status="ENVIADO",
                source_filename=f"hist2_{uuid.uuid4().hex[:8]}.jpg",
            )
            db_session.add(record)
            await db_session.commit()
            await db_session.refresh(record)
            return record.id

        import asyncio

        loop = asyncio.get_event_loop()
        rid = loop.run_until_complete(_setup())

        cookie = _make_cookie(test_admin_user.id, test_admin_user.username, test_admin_user.role)
        client.cookies.set(COOKIE_NAME, cookie)

        r = client.put(
            f"/history/{rid}",
            data={},
        )
        assert r.status_code == 200


class TestRootRoutes:
    def test_root_redirects(self, client, _test_users_setup):
        r = client.get("/", follow_redirects=False)
        assert r.status_code in (200, 302, 307)

    def test_root_with_session(self, client, _test_users_setup, test_admin_user):
        cookie = _make_cookie(test_admin_user.id, test_admin_user.username, test_admin_user.role)
        client.cookies.set(COOKIE_NAME, cookie)
        r = client.get("/", follow_redirects=False)
        assert r.status_code in (200, 302, 307)

    def test_login_page(self, client, _test_users_setup):
        r = client.get("/login")
        assert r.status_code == 200

    def test_dashboard_status_as_standard(self, client, _test_users_setup, test_standard_user):
        cookie = _make_cookie(
            test_standard_user.id, test_standard_user.username, test_standard_user.role
        )
        client.cookies.set(COOKIE_NAME, cookie)
        r = client.get("/dashboard/status")
        assert r.status_code == 200

    def test_categories_by_account_filter(self, client, _test_users_setup, test_admin_user):
        cookie = _make_cookie(test_admin_user.id, test_admin_user.username, test_admin_user.role)
        client.cookies.set(COOKIE_NAME, cookie)
        r = client.get(f"/categories/by-account?account_id={uuid.uuid4()}")
        assert r.status_code == 200

    def test_view_image_not_found(self, client, _test_users_setup, test_admin_user):
        cookie = _make_cookie(test_admin_user.id, test_admin_user.username, test_admin_user.role)
        client.cookies.set(COOKIE_NAME, cookie)
        r = client.get(f"/images/{uuid.uuid4()}/view")
        assert r.status_code == 404

    @pytest.mark.skip(reason="event loop conflict with async fixtures")
    def test_view_image_no_path(self, client, _test_users_setup, test_admin_user, db_session):
        from app.database.models import ExpenseRecord, ImageFile

        hash_val = f"sha_np_{uuid.uuid4().hex[:16]}"

        async def _create():
            record = ExpenseRecord(
                owner_id=test_admin_user.id,
                image_hash=hash_val,
                status="REQUIERE_REVISION",
                source_filename="no_path.jpg",
            )
            db_session.add(record)
            await db_session.flush()

            img_file = ImageFile(
                record_id=record.id,
                original_path="/nonexistent/file.jpg",
                sha256_hash=hash_val,
                file_size=100,
                mime_type="image/jpeg",
                owner_folder="Ruben",
            )
            db_session.add(img_file)
            await db_session.commit()
            return record.id

        import asyncio

        loop = asyncio.get_event_loop()
        rid = loop.run_until_complete(_create())

        cookie = _make_cookie(test_admin_user.id, test_admin_user.username, test_admin_user.role)
        client.cookies.set(COOKIE_NAME, cookie)
        r = client.get(f"/images/{rid}/view")
        assert r.status_code == 404

    def test_update_with_consecutive(self, client, _test_users_setup, test_admin_user, db_session):
        from app.database.models import ExpenseRecord

        hash_val = f"sha_con_{uuid.uuid4().hex[:16]}"

        async def _create():
            record = ExpenseRecord(
                owner_id=test_admin_user.id,
                image_hash=hash_val,
                status="REQUIERE_REVISION",
                source_filename="consec.jpg",
                group_code=f"V{uuid.uuid4().hex[:4]}",
                consecutive=int(uuid.uuid4().int % 9000) + 1000,
                ticket_description="GASOLINA",
            )
            db_session.add(record)
            await db_session.commit()
            await db_session.refresh(record)
            return record.id

        import asyncio

        loop = asyncio.get_event_loop()
        rid = loop.run_until_complete(_create())

        cookie = _make_cookie(test_admin_user.id, test_admin_user.username, test_admin_user.role)
        client.cookies.set(COOKIE_NAME, cookie)

        r = client.put(
            f"/expenses/{rid}",
            data={"transaction_date": "2026-01-20"},
        )
        assert r.status_code == 200

    @pytest.mark.skip(reason="event loop conflict with async fixtures")
    def test_bulk_send_with_records(self, client, _test_users_setup, test_admin_user, db_session):
        from datetime import date
        from unittest.mock import AsyncMock, patch

        from app.database.models import CatalogCache, ExpenseRecord

        hash_vals = [f"sha_bs{i}_{uuid.uuid4().hex[:12]}" for i in range(2)]

        async def _create():
            cat = CatalogCache(
                catalog_type="categoria",
                code=f"BSC{uuid.uuid4().hex[:4]}",
                description="Bulk Cat",
            )
            acc = CatalogCache(
                catalog_type="cuenta",
                code=f"BSA{uuid.uuid4().hex[:4]}",
                description="Bulk Acc",
            )
            db_session.add_all([cat, acc])
            await db_session.flush()

            rids = []
            for i, h in enumerate(hash_vals):
                record = ExpenseRecord(
                    owner_id=test_admin_user.id,
                    image_hash=h,
                    status="PENDIENTE_DE_ENVIO",
                    source_filename=f"bulk{i}.jpg",
                    transaction_date=date(2026, 1, 15),
                    amount=100.0 + i,
                    bank="BBVA",
                    group_code="VAL",
                    category_id=cat.id,
                    account_id=acc.id,
                )
                db_session.add(record)
                await db_session.flush()
                rids.append(str(record.id))
            await db_session.commit()
            return rids

        import asyncio

        loop = asyncio.get_event_loop()
        rids = loop.run_until_complete(_create())

        cookie = _make_cookie(test_admin_user.id, test_admin_user.username, test_admin_user.role)
        client.cookies.set(COOKIE_NAME, cookie)

        with patch(
            "app.expenses.routes.send_expense_to_sheets",
            new=AsyncMock(return_value={"success": True, "row": 10, "tab": "Ene-26"}),
        ):
            r = client.post(
                "/expenses/bulk-send",
                data={"record_ids": rids},
            )
            assert r.status_code == 200
