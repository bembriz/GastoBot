"""Acceso a la tabla espejo gastobot.expense_records."""

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.external.layout import CAMPOS, build_layout_row, get_month_label, month_label_to_key
from app.external.models import ExternalExpense


def _as_decimal(value: str) -> Decimal | None:
    cleaned = (value or "").strip().replace(",", "").replace("$", "")
    if not cleaned:
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def build_external_values(
    record: Any,
    category_code: str,
    account_code: str,
    month_label: str,
) -> dict[str, Any]:
    """Construir el dict de columnas para la fila externa."""
    row = build_layout_row(record, category_code, account_code)
    values: dict[str, Any] = dict(zip(CAMPOS, row, strict=True))
    values.update(
        {
            "record_id": record.id,
            "source": "app",
            "month_label": month_label,
            "group_code": record.group_code,
            "consecutive": record.consecutive,
            "final_description": record.final_description,
            "synced_at": datetime.now(UTC),
        }
    )
    return values


async def upsert_expense(db: AsyncSession, values: dict[str, Any]) -> None:
    """Insertar o actualizar por record_id (idempotente)."""
    stmt = insert(ExternalExpense).values(**values)
    update_values = {key: stmt.excluded[key] for key in values if key != "record_id"}
    stmt = stmt.on_conflict_do_update(
        index_elements=[ExternalExpense.record_id],
        index_where=ExternalExpense.record_id.isnot(None),
        set_=update_values,
    )
    await db.execute(stmt)


async def list_months(db: AsyncSession) -> list[dict[str, Any]]:
    """Agrupar por month_label con conteo e importe total."""
    result = await db.execute(
        select(ExternalExpense.month_label, ExternalExpense.total).order_by(
            ExternalExpense.month_label
        )
    )
    grouped: dict[str, dict[str, Any]] = {}
    for month_label, total in result.all():
        entry = grouped.setdefault(
            month_label,
            {"month_label": month_label, "count": 0, "total": Decimal("0")},
        )
        entry["count"] += 1
        amount = _as_decimal(total or "")
        if amount is not None:
            entry["total"] += amount

    months = list(grouped.values())
    months.sort(
        key=lambda item: month_label_to_key(str(item["month_label"])) or "",
        reverse=True,
    )
    return months


async def records_for_month(
    db: AsyncSession, month_label: str, limit: int = 1000
) -> list[ExternalExpense]:
    result = await db.execute(
        select(ExternalExpense)
        .where(ExternalExpense.month_label == month_label)
        .order_by(ExternalExpense.expense_date, ExternalExpense.id)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_record(db: AsyncSession, report_id: int) -> ExternalExpense | None:
    result = await db.execute(select(ExternalExpense).where(ExternalExpense.id == report_id))
    return result.scalar_one_or_none()


async def existing_natural_keys(db: AsyncSession) -> set[tuple[str, str, str]]:
    """Claves fecha+descripcion+total para deduplicar la migracion."""
    result = await db.execute(
        select(
            ExternalExpense.expense_date,
            ExternalExpense.description,
            ExternalExpense.total,
        )
    )
    return {(fecha or "", desc or "", total or "") for fecha, desc, total in result.all()}


async def insert_migrated_rows(db: AsyncSession, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    await db.execute(insert(ExternalExpense), rows)


def month_label_for(record: Any) -> str:
    return get_month_label(record.transaction_date)
