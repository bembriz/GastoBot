"""Envio de gastos a PostgreSQL externo (reemplazo del envio a Sheets)."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.locking import get_next_consecutive
from app.database.models import AuditEvent, CatalogCache, ExpenseRecord, ImageFile, SheetSync
from app.database.session import async_session
from app.external.engine import external_session, verify_connectivity
from app.external.layout import get_month_label
from app.external.repository import build_external_values, upsert_expense
from app.images.files import move_image_to_sent

# SheetSync.sheet_row es NOT NULL y no admite NULL en el esquema local.
# En envios a PostgreSQL no existe una fila fisica de hoja: se usa 0 como
# centinela documentado (D5, sin migracion de esquema).
EXTERNAL_SYNC_SHEET_ROW = 0


async def _move_image(db: AsyncSession, record_id: uuid.UUID, month_label: str) -> str | None:
    """Trasladar la imagen y registrar el resultado. Nunca invalida el envio."""
    result = await db.execute(select(ImageFile).where(ImageFile.record_id == record_id))
    image = result.scalar_one_or_none()
    if not image:
        return None

    moved = move_image_to_sent(image, month_label)
    if moved:
        await db.commit()
        return moved

    db.add(
        AuditEvent(
            id=uuid.uuid4(),
            record_id=record_id,
            event_type="IMAGEN_NO_MOVIDA",
            new_state={
                "month": month_label,
                "path": image.original_path,
                "reason": "No se pudo mover a GASTOSIA_SENT_IMAGES_DIR",
            },
            created_at=datetime.now(UTC),
        )
    )
    await db.commit()
    return None


async def send_expense(record_id: str, group_code: str) -> dict[str, Any]:
    """Escribir el gasto en gastobot.expense_records y marcarlo ENVIADO.

    Misma firma/contrato que el sender de Sheets. La imagen se mueve despues
    del commit exitoso; un fallo del move no invalida el envio.
    """
    async with async_session() as db:
        result = await db.execute(select(ExpenseRecord).where(ExpenseRecord.id == record_id))
        record = result.scalar_one_or_none()
        if not record:
            return {"success": False, "error": "Registro no encontrado"}

        if not record.transaction_date or not group_code or not record.amount:
            return {"success": False, "error": "Faltan campos obligatorios: fecha, grupo o monto"}

        if not await verify_connectivity():
            record.status = "PENDIENTE_DE_ENVIO"
            await db.commit()
            return {
                "success": False,
                "error": "Sin conexion a la base de datos. Encolado para envio.",
            }

        record.status = "ENVIANDO"
        await db.commit()

        month_label = ""

        try:
            if not record.consecutive:
                record.consecutive = await get_next_consecutive(db, group_code)

            record.group_code = group_code.upper()
            ticket = record.ticket_description or ""
            record.final_description = f"{record.group_code}-{record.consecutive}-{ticket}"

            cat_code = ""
            acc_code = ""
            if record.category_id:
                cat_result = await db.execute(
                    select(CatalogCache).where(CatalogCache.id == record.category_id)
                )
                cat = cat_result.scalar_one_or_none()
                if cat:
                    cat_code = cat.description
            if record.account_id:
                acc_result = await db.execute(
                    select(CatalogCache).where(CatalogCache.id == record.account_id)
                )
                acc = acc_result.scalar_one_or_none()
                if acc:
                    acc_code = acc.description

            month_label = get_month_label(record.transaction_date)
            values = build_external_values(record, cat_code, acc_code, month_label)

            async with external_session() as ext_db:
                await upsert_expense(ext_db, values)
                await ext_db.commit()

            record.status = "ENVIADO"
            record.sheet_name = month_label
            record.sheet_row = None
            record.sent_at = datetime.now(UTC)

            sync_result = await db.execute(
                select(SheetSync).where(SheetSync.record_id == record.id)
            )
            sync = sync_result.scalar_one_or_none()
            if sync:
                sync.sheet_name = month_label
                sync.sheet_row = EXTERNAL_SYNC_SHEET_ROW
                sync.sync_status = "inserted"
                sync.synced_at = datetime.now(UTC)
            else:
                db.add(
                    SheetSync(
                        id=uuid.uuid4(),
                        record_id=record.id,
                        sheet_name=month_label,
                        sheet_row=EXTERNAL_SYNC_SHEET_ROW,
                        sync_status="inserted",
                    )
                )
            db.add(
                AuditEvent(
                    id=uuid.uuid4(),
                    record_id=record.id,
                    event_type="ENVIADO_A_BD",
                    new_state={
                        "month": month_label,
                        "consecutive": record.consecutive,
                        "source": "postgres",
                    },
                    created_at=datetime.now(UTC),
                )
            )
            await db.commit()
        except Exception as e:
            record.status = "ERROR_SHEETS"
            await db.commit()
            return {"success": False, "error": str(e)[:200]}

        try:
            await _move_image(db, record.id, month_label)
        except Exception as e:
            print(f"[Envio] Advertencia al mover imagen: {e}", flush=True)

        return {
            "success": True,
            "tab": month_label,
            "row": None,
            "consecutive": record.consecutive,
            "description": record.final_description,
        }
