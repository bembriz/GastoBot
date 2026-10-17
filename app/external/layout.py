"""Layout de 16 columnas compartido entre Sheets, PostgreSQL externo y Excel."""

from datetime import date
from typing import Any

MESES = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]

COLUMNAS = [
    "Fecha del gasto",
    "Categoria",
    "Descripcion",
    "Empleado",
    "Pagado por",
    "Actividades",
    "Fecha contable",
    "Cuenta",
    "Precio unitario",
    "Cantidad",
    "Incluir impuestos",
    "Importe de impuestos",
    "Total",
    "Estado",
    "Banco",
    "Transaccion",
]

CAMPOS = [
    "expense_date",
    "category",
    "description",
    "employee",
    "paid_by",
    "activities",
    "accounting_date",
    "account",
    "unit_price",
    "quantity",
    "include_taxes",
    "tax_amount",
    "total",
    "estado",
    "bank",
    "transaction_type",
]


def get_month_label(expense_date: date) -> str:
    """Etiqueta larga usada en Excel, carpetas de imagenes y BD externa."""
    return f"{MESES[expense_date.month - 1]}-{expense_date.year}"


def month_label_to_key(label: str) -> str | None:
    """Convertir 'Julio-2026' en '2026-07'. Devuelve None si no es valido."""
    parts = label.strip().split("-")
    if len(parts) != 2:
        return None
    month_name, year = parts
    if not year.isdigit():
        return None
    month_names = [m.lower() for m in MESES]
    try:
        month = month_names.index(month_name.lower()) + 1
    except ValueError:
        return None
    return f"{int(year):04d}-{month:02d}"


def month_key_to_label(key: str) -> str | None:
    """Convertir '2026-07' en 'Julio-2026'. Devuelve None si no es valido."""
    parts = key.strip().split("-")
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        return None
    month = int(parts[1])
    if month < 1 or month > 12:
        return None
    return f"{MESES[month - 1]}-{int(parts[0]):04d}"


def normalize_month(value: str) -> str | None:
    """Aceptar 'Julio-2026' o '2026-07' y devolver la etiqueta larga."""
    label = month_key_to_label(value)
    if label:
        return label
    if month_label_to_key(value):
        return value.strip()
    return None


def build_layout_row(record: Any, category_code: str = "", account_code: str = "") -> list[str]:
    """Construir las 16 columnas del layout a partir de un ExpenseRecord."""
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
