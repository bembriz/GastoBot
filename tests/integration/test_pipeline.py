import uuid
import pytest
import pytest_asyncio
from datetime import datetime, timezone
from sqlalchemy import select

from app.database.models import ExpenseRecord
from app.database.session import async_session


def _unique_hash() -> str:
    return f"sha256_integration_{uuid.uuid4().hex}"


class TestCreateExpenseRecord:
    @pytest_asyncio.fixture(loop_scope="function")
    async def test_admin_id(self, db_session, test_admin_user):
        return test_admin_user.id

    async def test_create_expense_record(self, db_session, test_admin_id):
        record = ExpenseRecord(
            owner_id=test_admin_id,
            image_hash=_unique_hash(),
            status="DETECTADO",
            source_filename="integration_test_001.jpg",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(record)
        await db_session.commit()
        await db_session.refresh(record)

        assert record.id is not None
        assert record.status == "DETECTADO"
        assert record.owner_id == test_admin_id
        assert record.amount is None

        await db_session.delete(record)
        await db_session.commit()

    async def test_create_expense_record_with_all_fields(self, db_session, test_admin_id):
        record = ExpenseRecord(
            owner_id=test_admin_id,
            image_hash=_unique_hash(),
            status="DETECTADO",
            source_filename="integration_full.jpg",
            transaction_date=datetime(2026, 7, 15).date(),
            amount=1234.56,
            ticket_description="Compra en oficina",
            bank="BBVA",
            transaction_type="Transferencia",
            confidence_json={"amount": 0.95},
            final_description="Material oficina",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(record)
        await db_session.commit()
        await db_session.refresh(record)

        from decimal import Decimal

        assert record.amount == Decimal("1234.56")
        assert record.ticket_description == "Compra en oficina"
        assert record.bank == "BBVA"
        assert record.transaction_type == "Transferencia"
        assert record.confidence_json == {"amount": 0.95}
        assert record.final_description == "Material oficina"

        await db_session.delete(record)
        await db_session.commit()

    async def test_create_expense_record_amount_precision(self, db_session, test_admin_id):
        """Verify that Numeric(12,2) stores cents correctly (C19)."""
        record = ExpenseRecord(
            owner_id=test_admin_id,
            image_hash=_unique_hash(),
            status="DETECTADO",
            source_filename="precision_test.jpg",
            amount=9999999999.99,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(record)
        await db_session.commit()
        await db_session.refresh(record)

        assert float(record.amount) == 9999999999.99

        await db_session.delete(record)
        await db_session.commit()

    async def test_image_hash_unique_constraint(self, db_session, test_admin_id):
        same_hash = _unique_hash()
        record1 = ExpenseRecord(
            owner_id=test_admin_id,
            image_hash=same_hash,
            status="DETECTADO",
            source_filename="dup_1.jpg",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(record1)
        await db_session.commit()

        record2 = ExpenseRecord(
            owner_id=test_admin_id,
            image_hash=same_hash,
            status="DETECTADO",
            source_filename="dup_2.jpg",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(record2)

        with pytest.raises(Exception):
            await db_session.commit()

        await db_session.rollback()
        await db_session.delete(record1)
        await db_session.commit()


class TestUpdateExpenseStatus:
    @pytest_asyncio.fixture(loop_scope="function")
    async def fresh_record(self, db_session, test_admin_user):
        record = ExpenseRecord(
            owner_id=test_admin_user.id,
            image_hash=_unique_hash(),
            status="DETECTADO",
            source_filename=f"status_test_{uuid.uuid4().hex[:8]}.jpg",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(record)
        await db_session.commit()
        await db_session.refresh(record)

        yield record

        try:
            await db_session.delete(record)
            await db_session.commit()
        except Exception:
            await db_session.rollback()

    async def test_update_status_to_en_cola(self, db_session, fresh_record):
        fresh_record.status = "EN_COLA"
        await db_session.commit()
        await db_session.refresh(fresh_record)

        assert fresh_record.status == "EN_COLA"

    async def test_update_status_to_analizando(self, db_session, fresh_record):
        fresh_record.status = "ANALIZANDO"
        await db_session.commit()
        await db_session.refresh(fresh_record)

        assert fresh_record.status == "ANALIZANDO"

    async def test_update_status_to_enviado(self, db_session, fresh_record):
        fresh_record.status = "ENVIADO"
        await db_session.commit()
        await db_session.refresh(fresh_record)

        assert fresh_record.status == "ENVIADO"

    async def test_update_status_invalid_raises_error(self, db_session, fresh_record):
        fresh_record.status = "ESTADO_INEXISTENTE"
        db_session.add(fresh_record)

        with pytest.raises(Exception):
            await db_session.commit()

        await db_session.rollback()

    async def test_updated_at_changes_on_update(self, db_session, fresh_record):
        original_updated_at = fresh_record.updated_at

        fresh_record.status = "EN_COLA"
        await db_session.commit()
        await db_session.refresh(fresh_record)

        assert fresh_record.updated_at > original_updated_at


class TestPriceSyncC19:
    """C19: Verify amount and ticket_description remain synchronized
    during the review-update cycle.
    """

    @pytest_asyncio.fixture(loop_scope="function")
    async def review_record(self, db_session, test_admin_user):
        record = ExpenseRecord(
            owner_id=test_admin_user.id,
            image_hash=_unique_hash(),
            status="REQUIERE_REVISION",
            source_filename=f"c19_test_{uuid.uuid4().hex[:8]}.jpg",
            transaction_date=datetime(2026, 7, 20).date(),
            amount=150.75,
            ticket_description="Gasolina Magna",
            bank="NU",
            transaction_type="Transferencia",
            confidence_json={
                "amount": 0.85,
                "ticket_description": 0.90,
                "bank": 0.95,
                "transaction_type": 0.80,
                "transaction_date": 0.88,
            },
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(record)
        await db_session.commit()
        await db_session.refresh(record)

        yield record

        try:
            await db_session.delete(record)
            await db_session.commit()
        except Exception:
            await db_session.rollback()

    async def test_update_amount_and_description_together(self, db_session, review_record):
        review_record.amount = 200.00
        review_record.final_description = "Gasolina Magna - corregido"
        await db_session.commit()
        await db_session.refresh(review_record)

        assert review_record.amount == 200.00
        assert review_record.final_description == "Gasolina Magna - corregido"

    async def test_update_only_amount_preserves_description(self, db_session, review_record):
        original_desc = review_record.ticket_description
        original_final = review_record.final_description

        review_record.amount = 175.25
        await db_session.commit()
        await db_session.refresh(review_record)

        assert review_record.amount == 175.25
        assert review_record.ticket_description == original_desc
        assert review_record.final_description == original_final

    async def test_update_only_description_preserves_amount(self, db_session, review_record):
        original_amount = review_record.amount

        review_record.final_description = "Solo cambio descripcion"
        await db_session.commit()
        await db_session.refresh(review_record)

        assert review_record.amount == original_amount
        assert review_record.final_description == "Solo cambio descripcion"

    async def test_amount_stored_as_numeric_with_cents(self, db_session, review_record):
        from decimal import Decimal

        review_record.amount = 99.99
        await db_session.commit()
        await db_session.refresh(review_record)

        assert review_record.amount == Decimal("99.99")
        assert isinstance(float(review_record.amount), float)
