"""Gestion de pestañas mensuales (Mes-AA)."""

import time
from datetime import date

from app.sheets.client import get_spreadsheet

MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]

COLUMNAS = [
    "Fecha del gasto", "Categoria", "Descripcion", "Empleado",
    "Pagado por", "Actividades", "Fecha contable", "Cuenta",
    "Precio unitario", "Cantidad", "Incluir impuestos",
    "Importe de impuestos", "Total", "Estado", "Banco", "Transaccion",
]


def get_month_tab_name(expense_date: date) -> str:
    return f"{MESES[expense_date.month - 1]}-{str(expense_date.year)[-2:]}"


def ensure_month_tab(sheet_name: str) -> int:
    sh = get_spreadsheet()
    try:
        ws = sh.worksheet(sheet_name)
    except Exception:
        ws = sh.add_worksheet(title=sheet_name, rows=100, cols=16)
        ws.append_row(COLUMNAS)
        time.sleep(1)
    return ws.id


def find_next_empty_row(sheet_name: str) -> int:
    sh = get_spreadsheet()
    ws = sh.worksheet(sheet_name)
    all_values = ws.get_all_values()
    return len(all_values) + 1


def build_sheet_row(record, category_code: str = "", account_code: str = "") -> list[str]:
    fecha = str(record.transaction_date) if record.transaction_date else ""
    cat = category_code or ""
    acc = account_code or ""
    desc = record.final_description or record.ticket_description or ""
    amount = str(record.amount) if record.amount is not None else ""
    bank = record.bank or ""
    ttype = record.transaction_type or "Transferencia"

    return [
        fecha,
        cat,
        desc,
        "RUBEN BENJAMIN VAZQUEZ EMBRIZ",
        "Empresa",
        "",
        "",
        acc,
        amount,
        "1",
        "",
        "",
        amount,
        "Por reportar",
        bank,
        ttype,
    ]
