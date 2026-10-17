"""Tabla espejo gastobot.expense_records en la instancia PostgreSQL destino."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Index, Integer, MetaData, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class ExternalBase(DeclarativeBase):
    metadata = MetaData(schema="gastobot")


def utcnow() -> datetime:
    return datetime.now(UTC)


class ExternalExpense(ExternalBase):
    __tablename__ = "expense_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    record_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="app")
    month_label: Mapped[str] = mapped_column(String(20), nullable=False)

    expense_date: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    category: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    employee: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    paid_by: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    activities: Mapped[str] = mapped_column(Text, nullable=False, default="")
    accounting_date: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    account: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    unit_price: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    quantity: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    include_taxes: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    tax_amount: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    total: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    estado: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    bank: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False, default="")

    group_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    consecutive: Mapped[int | None] = mapped_column(Integer, nullable=True)
    final_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    __table_args__ = (
        Index("ix_gastobot_expense_records_month", "month_label"),
        Index(
            "uq_gastobot_expense_records_record_id",
            "record_id",
            unique=True,
            postgresql_where=text("record_id IS NOT NULL"),
        ),
        Index(
            "uq_gastobot_expense_records_group_consecutive",
            "group_code",
            "consecutive",
            unique=True,
            postgresql_where=text("consecutive IS NOT NULL"),
        ),
    )


def external_row_dict(row: ExternalExpense) -> dict[str, Any]:
    """Serializar una fila externa para templates/rutas."""
    return {
        "id": row.id,
        "record_id": str(row.record_id) if row.record_id else None,
        "source": row.source,
        "month_label": row.month_label,
        "expense_date": row.expense_date,
        "category": row.category,
        "description": row.description,
        "employee": row.employee,
        "paid_by": row.paid_by,
        "activities": row.activities,
        "accounting_date": row.accounting_date,
        "account": row.account,
        "unit_price": row.unit_price,
        "quantity": row.quantity,
        "include_taxes": row.include_taxes,
        "tax_amount": row.tax_amount,
        "total": row.total,
        "estado": row.estado,
        "bank": row.bank,
        "transaction_type": row.transaction_type,
        "group_code": row.group_code,
        "consecutive": row.consecutive,
        "final_description": row.final_description,
        "synced_at": row.synced_at,
    }
