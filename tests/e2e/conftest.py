"""Fixtures compartidos para tests E2E con Playwright."""

import os
import socket
import threading
import time
import uuid

import pytest

os.environ["GASTOSIA_TEST"] = "1"
os.environ.setdefault("GASTOSIA_SESSION_SECRET", "test-session-secret-e2e-64chars-key-ok!!")


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _run_server(port: int) -> None:
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=port,
        log_level="warning",
        access_log=False,
    )


@pytest.fixture(scope="session")
def live_server() -> str:
    port = _find_free_port()
    t = threading.Thread(target=_run_server, args=(port,), daemon=True)
    t.start()
    time.sleep(2)
    return f"http://127.0.0.1:{port}"


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args, live_server):
    return {
        **browser_context_args,
        "ignore_https_errors": True,
    }


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    return {
        **browser_type_launch_args,
        "args": [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
        ],
    }


def _run_async_in_thread(coro):
    """Run an async coroutine in a separate thread with its own event loop."""
    import asyncio

    result_holder = {}
    exception_holder = {}

    def runner():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result_holder["result"] = loop.run_until_complete(coro)
        except Exception as e:
            exception_holder["error"] = e
        finally:
            loop.close()

    t = threading.Thread(target=runner)
    t.start()
    t.join()

    if "error" in exception_holder:
        raise exception_holder["error"]
    return result_holder["result"]


async def _create_e2e_user_async():
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.auth.password import hash_password
    from app.database.engine import engine
    from app.database.models import User

    username = f"e2e_test_{uuid.uuid4().hex[:8]}"
    password = "e2e-test-password-12345"

    async with AsyncSession(engine) as sess:
        result = await sess.execute(select(User).where(User.username == username))
        existing = result.scalar_one_or_none()

        if existing is None:
            user = User(
                username=username,
                password_hash=hash_password(password),
                role="admin",
                is_active=True,
                password_change_required=False,
            )
            sess.add(user)
            await sess.commit()
            await sess.refresh(user)
            user_id = str(user.id)
        else:
            user_id = str(existing.id)

    await engine.dispose()
    return {
        "user_id": user_id,
        "username": username,
        "password": password,
    }


@pytest.fixture(scope="session")
def e2e_user():
    return _run_async_in_thread(_create_e2e_user_async())


@pytest.fixture(scope="session")
def auth_cookie(e2e_user: dict) -> str:
    from app.auth.session import create_session

    return create_session(
        uuid.UUID(e2e_user["user_id"]),
        e2e_user["username"],
        "admin",
    )


@pytest.fixture
def authenticated_page(page, live_server: str, auth_cookie: str):
    page.goto(live_server)
    page.context.add_cookies(
        [
            {
                "name": "gastosia_session",
                "value": auth_cookie,
                "domain": "127.0.0.1",
                "path": "/",
            }
        ]
    )
    return page
