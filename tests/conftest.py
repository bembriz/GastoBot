import os
import uuid
from datetime import UTC, datetime

import pytest_asyncio

# ---------------------------------------------------------------------------
# Set required env vars BEFORE any app imports that read os.environ at module level
# ---------------------------------------------------------------------------
if "GASTOSIA_DATABASE_HOST" not in os.environ:
    os.environ["GASTOSIA_DATABASE_HOST"] = os.environ.get(
        "GASTOSIA_DATABASE_HOST", "192.168.100.45"
    )
if "GASTOSIA_DATABASE_PORT" not in os.environ:
    os.environ["GASTOSIA_DATABASE_PORT"] = os.environ.get("GASTOSIA_DATABASE_PORT", "5432")
if "GASTOSIA_DATABASE_NAME" not in os.environ:
    os.environ["GASTOSIA_DATABASE_NAME"] = os.environ.get("GASTOSIA_DATABASE_NAME", "gastos_ia")
if "GASTOSIA_DATABASE_USER" not in os.environ:
    os.environ["GASTOSIA_DATABASE_USER"] = os.environ.get("GASTOSIA_DATABASE_USER", "gastos_app")
if "GASTOSIA_DATABASE_PASSWORD" not in os.environ:
    os.environ["GASTOSIA_DATABASE_PASSWORD"] = os.environ.get("GASTOSIA_DATABASE_PASSWORD", "")

if os.environ.get("GASTOSIA_USE_ADMIN_DB") and "GASTOSIA_POSTGRES_ADMIN_PASSWORD" not in os.environ:
    os.environ["GASTOSIA_POSTGRES_ADMIN_PASSWORD"] = os.environ.get(
        "GASTOSIA_POSTGRES_ADMIN_PASSWORD", ""
    )

if "GASTOSIA_SESSION_SECRET" not in os.environ:
    os.environ["GASTOSIA_SESSION_SECRET"] = "test-session-secret-64chars-long-key-for-tests!!"

if "GASTOSIA_GEMINI_API_KEY" not in os.environ:
    os.environ["GASTOSIA_GEMINI_API_KEY"] = "test-gemini-api-key"

os.environ["GASTOSIA_TEST"] = "1"

# ---------------------------------------------------------------------------
# Now safe to import app modules
# ---------------------------------------------------------------------------
from app.auth.password import hash_password  # noqa: E402
from app.database.engine import engine  # noqa: E402
from app.database.models import ExpenseRecord, User  # noqa: E402

TEST_USER_ADMIN_NAME = f"test_admin_{uuid.uuid4().hex[:8]}"
TEST_USER_STANDARD_NAME = f"test_standard_{uuid.uuid4().hex[:8]}"
TEST_USER_ADMIN_PASSWORD = "admin-test-password-12345"
TEST_USER_STANDARD_PASSWORD = "standard-test-password-67890"
TEST_USER_ADMIN_HASH = hash_password(TEST_USER_ADMIN_PASSWORD)
TEST_USER_STANDARD_HASH = hash_password(TEST_USER_STANDARD_PASSWORD)
TEST_USER_ADMIN_ID: uuid.UUID | None = None
TEST_USER_STANDARD_ID: uuid.UUID | None = None


def _make_session():
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return maker()


@pytest_asyncio.fixture(loop_scope="function")
async def db_session():
    """Provide a clean async database session per test function."""
    session = _make_session()
    try:
        yield session
    finally:
        await session.close()
        # Dispose pool connections so the next test (on a new event loop)
        # doesn't reuse stale connections from this loop.
        await engine.dispose()


@pytest_asyncio.fixture(loop_scope="function")
async def _test_users_setup(db_session):
    """Create test users once (lazily, per first test that needs them).

    Uses the module-level globals so users are created just once across
    all tests in a run. The db_session fixture is still function-scoped
    but we check if users already exist before creating.
    """
    global TEST_USER_ADMIN_ID, TEST_USER_STANDARD_ID

    if TEST_USER_ADMIN_ID is not None:
        # Already created by a previous test
        return

    admin_user = User(
        username=TEST_USER_ADMIN_NAME,
        password_hash=TEST_USER_ADMIN_HASH,
        role="admin",
        is_active=True,
        password_change_required=False,
    )
    standard_user = User(
        username=TEST_USER_STANDARD_NAME,
        password_hash=TEST_USER_STANDARD_HASH,
        role="standard",
        is_active=True,
        password_change_required=False,
    )
    db_session.add_all([admin_user, standard_user])
    await db_session.flush()

    TEST_USER_ADMIN_ID = admin_user.id
    TEST_USER_STANDARD_ID = standard_user.id

    await db_session.commit()


@pytest_asyncio.fixture(loop_scope="function")
async def test_admin_user(db_session, _test_users_setup):
    """Return the pre-created admin user."""
    from sqlalchemy import select as sa_select

    result = await db_session.execute(sa_select(User).where(User.username == TEST_USER_ADMIN_NAME))
    row = result.scalar_one()
    row.id = row.id  # ensure loaded
    return row


@pytest_asyncio.fixture(loop_scope="function")
async def test_standard_user(db_session, _test_users_setup):
    """Return the pre-created standard user."""
    from sqlalchemy import select as sa_select

    result = await db_session.execute(
        sa_select(User).where(User.username == TEST_USER_STANDARD_NAME)
    )
    row = result.scalar_one()
    return row


def _unique_hash() -> str:
    return f"sha256_test_{uuid.uuid4().hex}"


@pytest_asyncio.fixture(loop_scope="function")
async def test_record(db_session, _test_users_setup, test_admin_user):
    """Create a test expense record and clean it up after the test."""
    record = ExpenseRecord(
        owner_id=test_admin_user.id,
        image_hash=_unique_hash(),
        status="DETECTADO",
        source_filename=f"test_{uuid.uuid4().hex[:8]}.jpg",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(record)
    await db_session.commit()
    await db_session.refresh(record)

    yield record

    await db_session.delete(record)
    await db_session.commit()
