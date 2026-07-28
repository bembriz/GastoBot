# Ejemplo: Repositorio de historial con filtros y paginación
# Archivo: app/history/repository.py

from datetime import date, datetime
from typing import Optional
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import ExpenseRecord, AuditEvent, User
from app.database.session import get_session


class HistoryRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def search_expenses(
        self,
        current_user: User,
        *,
        owner: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        bank: Optional[str] = None,
        group_code: Optional[str] = None,
        status: Optional[str] = None,
        search_text: Optional[str] = None,
        page: int = 1,
        per_page: int = 25,
    ) -> tuple[list[ExpenseRecord], int]:
        conditions = []

        # Role-based filtering
        if current_user.role != "admin":
            conditions.append(ExpenseRecord.owner == current_user.username)
        elif owner:
            conditions.append(ExpenseRecord.owner == owner)

        if date_from:
            conditions.append(ExpenseRecord.transaction_date >= date_from)
        if date_to:
            conditions.append(ExpenseRecord.transaction_date <= date_to)
        if bank:
            conditions.append(ExpenseRecord.bank.ilike(f"%{bank}%"))
        if group_code:
            conditions.append(ExpenseRecord.group_code.ilike(f"%{group_code}%"))
        if status:
            conditions.append(ExpenseRecord.status == status)

        if search_text:
            text_filter = f"%{search_text}%"
            conditions.append(or_(
                ExpenseRecord.ticket_description.ilike(text_filter),
                ExpenseRecord.final_description.ilike(text_filter),
                ExpenseRecord.source_filename.ilike(text_filter),
                ExpenseRecord.group_code.ilike(text_filter),
            ))

        # Count query
        count_q = select(func.count(ExpenseRecord.id))
        if conditions:
            count_q = count_q.where(and_(*conditions))
        total = (await self.session.execute(count_q)).scalar() or 0

        # Data query
        q = select(ExpenseRecord).order_by(
            desc(ExpenseRecord.transaction_date),
            desc(ExpenseRecord.created_at),
        )
        if conditions:
            q = q.where(and_(*conditions))
        q = q.offset((page - 1) * per_page).limit(per_page)

        result = await self.session.execute(q)
        records = result.scalars().all()

        return list(records), total

    async def get_audit_trail(self, record_id: int) -> list[AuditEvent]:
        q = (
            select(AuditEvent)
            .where(AuditEvent.expense_record_id == record_id)
            .order_by(AuditEvent.created_at.asc())
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def get_reconciliation_status(
        self, record_id: int
    ) -> dict:
        """Compare local record with _Control sheet data."""
        record_q = select(ExpenseRecord).where(ExpenseRecord.id == record_id)
        result = await self.session.execute(record_q)
        record = result.scalar_one_or_none()

        if not record:
            return {"status": "NOT_FOUND_LOCAL", "differences": []}

        if not record.sheet_name or not record.sheet_row:
            return {"status": "NOT_IN_SHEETS", "differences": []}

        # The actual Google Sheets comparison is done in the
        # google-sheets skill. Here we prepare the local data.
        return {
            "status": "PENDING_SHEETS_CHECK",
            "record_id": record_id,
            "sheet_name": record.sheet_name,
            "sheet_row": record.sheet_row,
            "local_data": {
                "transaction_date": str(record.transaction_date) if record.transaction_date else None,
                "amount": float(record.amount) if record.amount else None,
                "bank": record.bank,
                "transaction_type": record.transaction_type,
                "final_description": record.final_description,
                "category_code": record.category_code,
                "account_code": record.account_code,
                "group_code": record.group_code,
                "consecutive": record.consecutive,
                "status": record.status,
            },
        }

    async def update_record(
        self, record_id: int, data: dict, updated_by: str
    ) -> ExpenseRecord:
        """Update a record and log audit event."""
        record_q = select(ExpenseRecord).where(ExpenseRecord.id == record_id)
        result = await self.session.execute(record_q)
        record = result.scalar_one_or_none()

        if not record:
            raise ValueError(f"Record {record_id} not found")

        changes = {}
        for field, new_value in data.items():
            old_value = getattr(record, field, None)
            if old_value != new_value:
                changes[field] = {"old": str(old_value), "new": str(new_value)}
                setattr(record, field, new_value)

        if changes:
            record.updated_at = datetime.utcnow()

            # Log audit event
            audit = AuditEvent(
                expense_record_id=record_id,
                user=updated_by,
                action="UPDATED",
                field_changes=changes,
            )
            self.session.add(audit)
            await self.session.commit()

        return record

    def get_month_name_spanish(self, dt: date) -> str:
        months = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
        ]
        return months[dt.month - 1]

    def get_sheet_name(self, dt: date) -> str:
        return f"{self.get_month_name_spanish(dt)}-{dt.strftime('%y')}"

    def detect_month_change(
        self, record: ExpenseRecord, new_date: date
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """Check if editing date will change the sheet month."""
        if not record.transaction_date:
            return False, None, None

        old_sheet = self.get_sheet_name(record.transaction_date)
        new_sheet = self.get_sheet_name(new_date)

        if old_sheet != new_sheet:
            return True, old_sheet, new_sheet
        return False, None, None
