# Ejemplo: Flujo de envío a Google Sheets (11 pasos)
# Archivo: app/sheets/sender.py

from datetime import datetime
from typing import Optional
from app.sheets.client import GoogleSheetsClient
from app.sheets.control import ControlSheetManager
from app.sheets.tabs import TabManager
from app.sheets.consecutive import ConsecutiveManager
from app.sheets.sync import CatalogSync
from app.sheets.errors import SheetsConnectionError
from app.database.models import ExpenseRecord, AuditEvent, User
from app.database.session import get_session


MONTHLY_COLUMNS = [
    "transaction_date",    # A: Fecha del gasto
    "category",            # B: Categoría
    "final_description",   # C: Descripción
    "empleado",            # D: Empleado
    "pagado_por",          # E: Pagado por
    "actividades",         # F: Actividades
    "fecha_contable",      # G: Fecha contable
    "cuenta",              # H: Cuenta
    "unit_price",          # I: Precio unitario
    "cantidad",            # J: Cantidad
    "incluir_impuestos",   # K: Incluir impuestos
    "importe_impuestos",   # L: Importe de impuestos
    "total",               # M: Total
    "estado",              # N: Estado
    "bank",                # O: Banco
    "transaction_type",    # P: Transaccion
]


class ExpenseSender:
    """Orchestrates the 11-step send flow per PRD Section 9.4."""

    def __init__(self):
        self.client = GoogleSheetsClient()
        self.control = ControlSheetManager(self.client)
        self.tabs = TabManager(self.client)
        self.consecutive = ConsecutiveManager(self.client)
        self.sync = CatalogSync(self.client)

    async def send_expense(
        self, record: ExpenseRecord, current_user: User
    ) -> dict:
        """
        Execute the full 11-step send flow.
        Returns {"success": bool, "message": str, "sheet_row": int | None}
        """
        try:
            # Step 1: Verify internet connectivity
            if not await self.client.verify_connectivity():
                await self._set_status(record, "PENDIENTE_DE_ENVIO")
                return {"success": False, "message": "Sin conexión a Internet"}

            # Step 2: Sync catalogs from Sheets
            await self.sync.sync_categories_from_sheets()
            await self.sync.sync_accounts_from_sheets()

            # Step 3: Query _Control
            await self.control.ensure_control_sheet()

            # Step 4: Re-validate duplicates
            if record.image_hash:
                existing = await self.control.find_by_hash(record.image_hash)
                if existing and existing.get("record_id") != str(record.id):
                    await self._set_status(record, "DUPLICADO_EXACTO")
                    return {"success": False, "message": "Imagen duplicada detectada"}

            # Step 5: Recalculate consecutive
            if record.group_code:
                next_num = await self.consecutive.assign_next(
                    record.group_code, record.session
                )
                record.consecutive = next_num
                record.final_description = self._build_final_description(record)

            # Step 6: Determine monthly tab
            sheet_name = self.tabs.get_month_tab_name(record.transaction_date)
            await self.tabs.ensure_month_tab(sheet_name)

            # Step 7: Find next empty row
            next_row = await self.tabs.find_next_empty_row(sheet_name)

            # Step 8: Build row data (16 columns)
            row_data = self._build_row_data(record)

            # Step 9: Insert row
            range_name = f"'{sheet_name}'!A{next_row}:P{next_row}"
            await self.client.write_range(range_name, [row_data])

            # Step 10: Update _Control
            await self.control.add_control_entry({
                "record_id": record.id,
                "image_hash": record.image_hash,
                "owner": record.owner,
                "group_code": record.group_code,
                "consecutive": record.consecutive,
                "final_description": record.final_description,
                "expense_date": str(record.transaction_date),
                "amount": float(record.amount) if record.amount else 0,
                "bank": record.bank or "",
                "transaction_type": record.transaction_type or "",
                "sheet_name": sheet_name,
                "sheet_row": next_row,
                "status": "ENVIADO",
                "source_filename": record.source_filename or "",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            })

            # Step 11: Log audit event
            await self._log_audit(record, current_user, "SENT", {
                "sheet_name": sheet_name,
                "sheet_row": next_row,
            })

            # Mark as sent
            record.status = "ENVIADO"
            record.sheet_name = sheet_name
            record.sheet_row = next_row

            return {
                "success": True,
                "message": f"Enviado a {sheet_name} fila {next_row}",
                "sheet_row": next_row,
            }

        except SheetsConnectionError:
            await self._set_status(record, "PENDIENTE_DE_ENVIO")
            return {"success": False, "message": "Sin conexión a Internet"}
        except Exception as e:
            await self._set_status(record, "ERROR_SHEETS")
            await self._log_audit(record, current_user, "SEND_ERROR", {
                "error": str(e),
            })
            return {"success": False, "message": f"Error: {str(e)}"}

    def _build_row_data(self, record: ExpenseRecord) -> list:
        """Build 16-column row matching PRD Section 13.1 order."""
        return [
            str(record.transaction_date) if record.transaction_date else "",   # A
            record.category_code or "",                                        # B
            record.final_description or "",                                    # C
            "RUBEN BENJAMIN VAZQUEZ EMBRIZ",                                   # D
            "Empresa",                                                         # E
            "",                                                                 # F
            "",                                                                 # G
            record.account_code or "",                                         # H
            float(record.unit_price) if record.unit_price else "",             # I
            1,                                                                  # J
            "",                                                                 # K
            "",                                                                 # L
            float(record.total) if record.total else "",                       # M
            "Por reportar",                                                    # N
            record.bank or "",                                                  # O
            record.transaction_type or "",                                     # P
        ]

    def _build_final_description(self, record: ExpenseRecord) -> str:
        parts = [
            record.group_code or "",
            str(record.consecutive) if record.consecutive else "",
            record.ticket_description or "",
        ]
        return "-".join(p for p in parts if p)

    async def _set_status(self, record: ExpenseRecord, status: str):
        record.status = status
        record.updated_at = datetime.utcnow()

    async def _log_audit(
        self, record: ExpenseRecord, user: User, action: str, details: dict
    ):
        async with get_session() as session:
            audit = AuditEvent(
                expense_record_id=record.id,
                user=user.username,
                action=action,
                field_changes=details,
            )
            session.add(audit)
            await session.commit()
