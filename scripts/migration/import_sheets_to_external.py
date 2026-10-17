"""Migrar las pestanas mensuales de Google Sheets a gastobot.expense_records.

Lee el spreadsheet configurado (GASTOSIA_GOOGLE_*) y carga las filas de las
pestanas mensuales (Mes-AA) en la tabla externa. No modifica el spreadsheet.

Idempotente: deduplica por clave natural fecha + descripcion + total contra
las filas ya existentes en la BD externa (tanto de la app como migradas).

Uso:
  # Dry-run (por defecto): cuenta filas y reporta problemas, sin escribir.
  uv run python scripts/migration/import_sheets_to_external.py

  # Escritura real:
  uv run python scripts/migration/import_sheets_to_external.py --apply
"""

import argparse
import asyncio
import re
import sys
import unicodedata
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.external.engine import external_session
from app.external.layout import COLUMNAS, CAMPOS, MESES
from app.external.repository import existing_natural_keys, insert_migrated_rows
from app.sheets.client import get_spreadsheet

CONTROL_TAB = "_Control"
MONTH_TAB_RE = re.compile(r"^([A-Za-zÁÉÍÓÚÜáéíóúü]+)-(\d{2,4})$")
DATE_PREFIX_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")
DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y", "%m/%d/%Y", "%m/%d/%y")


def normalize_header(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_value = "".join(c for c in normalized if not unicodedata.combining(c))
    return " ".join(ascii_value.lower().split())


def normalize_amount(value: str) -> str:
    cleaned = (value or "").strip().replace(",", "").replace("$", "")
    if not cleaned:
        return ""
    try:
        return format(Decimal(cleaned).normalize(), "f")
    except InvalidOperation:
        return cleaned


def parse_date(value: str) -> date | None:
    text = (value or "").strip()
    if not text:
        return None
    match = DATE_PREFIX_RE.match(text)
    if match:
        try:
            return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def short_tab_to_label(title: str) -> str | None:
    match = MONTH_TAB_RE.match(title.strip())
    if not match:
        return None
    month_name, year_text = match.group(1), match.group(2)
    try:
        month_index = [m.lower() for m in MESES].index(month_name.lower())
    except ValueError:
        return None
    year = int(year_text)
    if year < 100:
        year += 2000
    return f"{MESES[month_index]}-{year}"


def natural_key(expense_date: str, description: str, total: str) -> tuple[str, str, str]:
    parsed = parse_date(expense_date)
    date_key = parsed.isoformat() if parsed else (expense_date or "").strip()
    return (date_key, (description or "").strip(), normalize_amount(total))


def validate_header(header: list[str]) -> bool:
    if len(header) < 16:
        return False
    expected = [normalize_header(c) for c in COLUMNAS]
    actual = [normalize_header(c) for c in header[:16]]
    return actual == expected


def build_control_layout(row: list[str], index: dict[str, int]) -> list[str] | None:
    """Convertir una fila de _Control al layout de 16 columnas."""

    def get(name: str) -> str:
        position = index.get(name)
        if position is None or position >= len(row):
            return ""
        return (row[position] or "").strip()

    expense_date = get("expense_date")
    description = get("final_description")
    amount = get("amount")
    if not description and not amount:
        return None

    return [
        expense_date,
        "",
        description,
        "RUBEN BENJAMIN VAZQUEZ EMBRIZ",
        "Empresa",
        "",
        "",
        "",
        amount,
        "1",
        "",
        "",
        amount,
        "Por reportar",
        get("bank"),
        get("transaction_type") or "Transferencia",
    ]


def build_migrated_row(values: list[str], month_label: str) -> dict[str, Any]:
    padded = list(values[:16]) + [""] * max(0, 16 - len(values))
    fields = {field: (padded[index] or "").strip() for index, field in enumerate(CAMPOS)}
    return {
        **fields,
        "record_id": None,
        "source": "sheets_migration",
        "month_label": month_label,
        "group_code": None,
        "consecutive": None,
        "final_description": fields["description"] or None,
        "synced_at": datetime.now(UTC),
    }


async def main(apply: bool) -> int:
    spreadsheet = get_spreadsheet()
    async with external_session() as db:
        existing = {
            natural_key(*key) for key in await existing_natural_keys(db)
        }

    seen: set[tuple[str, str, str]] = set()
    pending: list[dict[str, Any]] = []
    totals = {
        "tabs": 0,
        "tabs_skipped": 0,
        "rows": 0,
        "rows_valid": 0,
        "rows_duplicate": 0,
        "rows_invalid": 0,
    }

    print(f"[migracion] Modo: {'APPLY' if apply else 'DRY-RUN'}")
    worksheets = spreadsheet.worksheets()

    control = next((ws for ws in worksheets if ws.title == CONTROL_TAB), None)
    if control is not None:
        rows = control.get_all_values()
        index = {normalize_header(value): i for i, value in enumerate(rows[0] if rows else [])}
        required = {"expense_date", "final_description", "amount"}
        if not rows or not required.issubset(index):
            print(f"[{CONTROL_TAB}] OMITIDA: faltan columnas requeridas {sorted(required)}")
            totals["tabs_skipped"] += 1
        else:
            control_valid = control_duplicate = control_invalid = 0
            for row_number, row in enumerate(rows[1:], start=2):
                totals["rows"] += 1
                if not any((cell or "").strip() for cell in row):
                    continue
                layout = build_control_layout(row, index)
                if layout is None:
                    control_invalid += 1
                    totals["rows_invalid"] += 1
                    print(f"[{CONTROL_TAB}:{row_number}] omitida: sin descripcion ni monto")
                    continue

                expense_date, description, total = layout[0], layout[2], layout[12]
                parsed = parse_date(expense_date)
                sheet_name = (
                    (row[index["sheet_name"]] or "").strip()
                    if "sheet_name" in index and index["sheet_name"] < len(row)
                    else ""
                )
                month_label = (
                    f"{MESES[parsed.month - 1]}-{parsed.year}"
                    if parsed
                    else short_tab_to_label(sheet_name)
                )
                if not month_label:
                    control_invalid += 1
                    totals["rows_invalid"] += 1
                    print(f"[{CONTROL_TAB}:{row_number}] omitida: sin fecha ni pestana mensual")
                    continue

                key = natural_key(expense_date, description, total)
                if key in existing or key in seen:
                    control_duplicate += 1
                    totals["rows_duplicate"] += 1
                    continue

                seen.add(key)
                control_valid += 1
                totals["rows_valid"] += 1
                pending.append(build_migrated_row(layout, month_label))

            print(
                f"[{CONTROL_TAB}] validas={control_valid} duplicadas={control_duplicate} "
                f"invalidas={control_invalid}"
            )

    for worksheet in worksheets:
        label = short_tab_to_label(worksheet.title)
        if not label:
            continue

        totals["tabs"] += 1
        rows = worksheet.get_all_values()
        if not rows or not validate_header(rows[0]):
            totals["tabs_skipped"] += 1
            print(f"[{worksheet.title}] OMITIDA: encabezado distinto al layout de 16 columnas")
            if rows:
                print(f"    header: {rows[0][:16]}")
            continue

        tab_valid = tab_duplicate = tab_invalid = 0
        for row_number, row in enumerate(rows[1:], start=2):
            totals["rows"] += 1
            if not any((cell or "").strip() for cell in row):
                continue

            padded = list(row[:16]) + [""] * max(0, 16 - len(row))
            expense_date = (padded[0] or "").strip()
            description = (padded[2] or "").strip()
            total = (padded[12] or "").strip()

            if not description and not total:
                tab_invalid += 1
                totals["rows_invalid"] += 1
                print(f"[{worksheet.title}:{row_number}] omitida: sin descripcion ni total")
                continue

            parsed = parse_date(expense_date)
            month_label = (
                f"{MESES[parsed.month - 1]}-{parsed.year}" if parsed else label
            )
            key = natural_key(expense_date, description, total)
            if key in existing or key in seen:
                tab_duplicate += 1
                totals["rows_duplicate"] += 1
                continue

            seen.add(key)
            tab_valid += 1
            totals["rows_valid"] += 1
            pending.append(build_migrated_row(padded, month_label))

        print(
            f"[{worksheet.title}] validas={tab_valid} duplicadas={tab_duplicate} "
            f"invalidas={tab_invalid} -> {label}"
        )

    print(
        f"[migracion] pestanas={totals['tabs']} omitidas={totals['tabs_skipped']} "
        f"filas={totals['rows']} validas={totals['rows_valid']} "
        f"duplicadas={totals['rows_duplicate']} invalidas={totals['rows_invalid']}"
    )

    if not apply:
        print("[dry-run] Sin escrituras en la BD externa ni en Sheets")
        return 0

    async with external_session() as db:
        try:
            await insert_migrated_rows(db, pending)
            await db.commit()
            print(f"[migracion] {len(pending)} filas insertadas en gastobot.expense_records")
        except Exception:
            await db.rollback()
            raise

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Escribe en la BD externa. Sin esta bandera solo hace dry-run.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fuerza dry-run (comportamiento por defecto).",
    )
    args = parser.parse_args()
    if args.dry_run and args.apply:
        print("Usa --apply o --dry-run, no ambos.")
        sys.exit(2)
    sys.exit(asyncio.run(main(apply=args.apply and not args.dry_run)))
