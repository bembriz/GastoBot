"""Envio de gastos a Google Sheets — flujo de 11 pasos (PRD 9.4)."""

import time
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select

from app.database.locking import get_next_consecutive
from app.database.models import AuditEvent, CatalogCache, ExpenseRecord, SheetSync
from app.database.session import async_session
from app.sheets.client import get_spreadsheet, verify_connectivity
from app.sheets.tabs import (
    build_sheet_row,
    ensure_month_tab,
    find_next_empty_row,
    get_month_tab_name,
)


async def send_expense(record_id: str, group_code: str) -> dict[str, Any]:
    async with async_session() as db:
        result = await db.execute(select(ExpenseRecord).where(ExpenseRecord.id == record_id))
        record = result.scalar_one_or_none()
        if not record:
            return {"success": False, "error": "Registro no encontrado"}

        if not record.transaction_date or not group_code or not record.amount:
            return {"success": False, "error": "Faltan campos obligatorios: fecha, grupo o monto"}

        # 1. Verificar internet
        if not verify_connectivity():
            record.status = "PENDIENTE_DE_ENVIO"
            await db.commit()
            return {"success": False, "error": "Sin conexion a Internet. Encolado para envio."}

        record.status = "ENVIANDO"
        await db.commit()

        try:
            # 2. Asignar consecutivo
            if not record.consecutive:
                consecutive = await get_next_consecutive(db, group_code)
                record.consecutive = consecutive

            # 3. Formar descripcion final
            record.group_code = group_code.upper()
            ticket = record.ticket_description or ""
            record.final_description = f"{record.group_code}-{record.consecutive}-{ticket}"

            # 4. Obtener codigos de catalogo
            cat_code = ""
            acc_code = ""
            if record.category_id:
                cat_result = await db.execute(
                    select(CatalogCache).where(CatalogCache.id == record.category_id)
                )
                cat = cat_result.scalar_one_or_none()
                if cat:
                    cat_code = f"{cat.description}"
            if record.account_id:
                acc_result = await db.execute(
                    select(CatalogCache).where(CatalogCache.id == record.account_id)
                )
                acc = acc_result.scalar_one_or_none()
                if acc:
                    acc_code = acc.description

            # 5. Determinar pestaña mensual
            tab_name = get_month_tab_name(record.transaction_date)
            ensure_month_tab(tab_name)

            # 6. Encontrar fila
            next_row = find_next_empty_row(tab_name)

            # 7. Construir y escribir fila
            row_data = build_sheet_row(record, cat_code, acc_code)

            sh = get_spreadsheet()
            ws = sh.worksheet(tab_name)
            ws.insert_row(row_data, next_row)
            time.sleep(1)

            # 8. Guardar referencia en DB
            record.status = "ENVIADO"
            record.sheet_name = tab_name
            record.sheet_row = next_row
            record.sent_at = datetime.now(UTC)

            # Registrar en sheet_sync
            sync = SheetSync(
                id=uuid.uuid4(),
                record_id=record.id,
                sheet_name=tab_name,
                sheet_row=next_row,
                sync_status="inserted",
            )
            db.add(sync)

            # Auditoria
            audit = AuditEvent(
                id=uuid.uuid4(),
                record_id=record.id,
                event_type="ENVIADO_A_SHEETS",
                new_state={
                    "tab": tab_name,
                    "row": next_row,
                    "consecutive": record.consecutive,
                },
                created_at=datetime.now(UTC),
            )
            db.add(audit)
            await db.commit()

            return {
                "success": True,
                "tab": tab_name,
                "row": next_row,
                "consecutive": record.consecutive,
                "description": record.final_description,
            }

        except Exception as e:
            record.status = "PENDIENTE_DE_ENVIO"
            await db.commit()
            return {"success": False, "error": str(e)[:200]}
