"""Gestion de pestañas mensuales (Mes-AA)."""

import time
from datetime import date
from typing import Any

from app.external.layout import COLUMNAS, MESES, build_layout_row
from app.sheets.client import get_spreadsheet


def get_month_tab_name(expense_date: date) -> str:
    return f"{MESES[expense_date.month - 1]}-{str(expense_date.year)[-2:]}"


def ensure_month_tab(sheet_name: str) -> int:
    sh = get_spreadsheet()
    try:
        ws = sh.worksheet(sheet_name)
    except Exception:
        try:
            ws = sh.add_worksheet(title=sheet_name, rows=100, cols=16)
            ws.append_row(COLUMNAS)
            time.sleep(1)
        except Exception as exc:
            if "already exists" not in str(exc):
                raise
            for existing_ws in sh.worksheets():
                if existing_ws.title == sheet_name:
                    ws = existing_ws
                    break
            else:
                raise
    return ws.id


def find_next_empty_row(sheet_name: str) -> int:
    sh = get_spreadsheet()
    ws = sh.worksheet(sheet_name)
    all_values = ws.get_all_values()
    return len(all_values) + 1


def build_sheet_row(record: Any, category_code: str = "", account_code: str = "") -> list[str]:
    return build_layout_row(record, category_code, account_code)
