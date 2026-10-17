import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from fastapi.responses import FileResponse

from app.expenses.routes import expense_image


def _db_returning(record):
    result = MagicMock()
    result.unique.return_value.scalar_one_or_none.return_value = record
    db = AsyncMock()
    db.execute.return_value = result
    return db


async def test_image_served_to_owner(tmp_path):
    owner_id = uuid.uuid4()
    path = tmp_path / "ticket.jpeg"
    path.write_bytes(b"image")
    record = SimpleNamespace(
        owner_id=owner_id,
        image_file=SimpleNamespace(
            original_path=str(path),
            optimized_path=None,
            mime_type="image/jpeg",
        ),
    )
    user = SimpleNamespace(id=owner_id, role="standard")

    response = await expense_image("record-1", user=user, db=_db_returning(record))

    assert isinstance(response, FileResponse)
    assert response.path == str(path)
    assert response.media_type == "image/jpeg"


async def test_image_served_to_admin_for_other_owner(tmp_path):
    path = tmp_path / "ticket.jpeg"
    path.write_bytes(b"image")
    record = SimpleNamespace(
        owner_id=uuid.uuid4(),
        image_file=SimpleNamespace(
            original_path=str(path),
            optimized_path=None,
            mime_type="image/jpeg",
        ),
    )
    user = SimpleNamespace(id=uuid.uuid4(), role="admin")

    response = await expense_image("record-1", user=user, db=_db_returning(record))
    assert isinstance(response, FileResponse)


async def test_image_forbidden_for_other_standard_user(tmp_path):
    path = tmp_path / "ticket.jpeg"
    path.write_bytes(b"image")
    record = SimpleNamespace(
        owner_id=uuid.uuid4(),
        image_file=SimpleNamespace(
            original_path=str(path),
            optimized_path=None,
            mime_type="image/jpeg",
        ),
    )
    user = SimpleNamespace(id=uuid.uuid4(), role="standard")

    with pytest.raises(HTTPException) as exc:
        await expense_image("record-1", user=user, db=_db_returning(record))
    assert exc.value.status_code == 403


async def test_image_404_when_record_missing():
    user = SimpleNamespace(id=uuid.uuid4(), role="admin")
    with pytest.raises(HTTPException) as exc:
        await expense_image("record-1", user=user, db=_db_returning(None))
    assert exc.value.status_code == 404


async def test_image_404_when_file_missing(tmp_path):
    record = SimpleNamespace(
        owner_id=uuid.uuid4(),
        image_file=SimpleNamespace(
            original_path=str(tmp_path / "missing.jpeg"),
            optimized_path=None,
            mime_type="image/jpeg",
        ),
    )
    user = SimpleNamespace(id=record.owner_id, role="standard")

    with pytest.raises(HTTPException) as exc:
        await expense_image("record-1", user=user, db=_db_returning(record))
    assert exc.value.status_code == 404


async def test_image_404_when_record_has_no_image():
    record = SimpleNamespace(owner_id=uuid.uuid4(), image_file=None)
    user = SimpleNamespace(id=record.owner_id, role="standard")

    with pytest.raises(HTTPException) as exc:
        await expense_image("record-1", user=user, db=_db_returning(record))
    assert exc.value.status_code == 404
