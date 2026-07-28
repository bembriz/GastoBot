"""import_historicos.py — importar datos historicos a _Control de Google Sheets.

Ejecutar: python scripts/validation/import_historicos.py [--file datos.csv] [--dry-run]

Requiere:
  - GASTOSIA_GOOGLE_CREDENTIALS_PATH
  - GASTOSIA_GOOGLE_SPREADSHEET_ID
"""

import os
import sys
import json
import hashlib
import argparse
import csv
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

CONTROL_HEADERS = [
    "record_id", "image_hash", "owner", "group_code", "consecutive",
    "final_description", "expense_date", "amount", "bank",
    "transaction_type", "sheet_name", "sheet_row", "status",
    "source_filename", "created_at", "updated_at",
]


def csv_reader(filepath: Path) -> list[dict]:
    """Leer archivo CSV de historicos con encoding flexible."""
    rows = []
    for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
        try:
            with open(filepath, newline="", encoding=encoding) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                if rows:
                    break
        except (UnicodeDecodeError, UnicodeError):
            continue
    return rows


def generate_record_id(row: dict, index: int) -> str:
    """Generar un record_id unico basado en los datos."""
    key = json.dumps(row, sort_keys=True, default=str)
    return f"historic-{hashlib.md5(key.encode()).hexdigest()[:12]}"


def normalize_row(row: dict, index: int, owner: str = "Ruben") -> dict | None:
    """Normalizar una fila de historicos al formato _Control."""
    expense_date = row.get("expense_date") or row.get("fecha") or row.get("date") or ""
    amount = row.get("amount") or row.get("total") or row.get("monto") or "0"
    description = row.get("final_description") or row.get("descripcion") or row.get("concepto") or ""
    group = row.get("group_code") or row.get("grupo") or "HIST"
    consecutive = row.get("consecutive") or row.get("consecutivo") or str(index + 1)

    if not expense_date:
        return None

    try:
        amount_f = float(str(amount).replace("$", "").replace(",", ""))
    except (ValueError, TypeError):
        amount_f = 0.0

    record_id = generate_record_id(row, index)

    return {
        "record_id": record_id,
        "image_hash": f"historic-{hashlib.md5(record_id.encode()).hexdigest()[:8]}",
        "owner": owner,
        "group_code": str(group).strip().upper(),
        "consecutive": int(consecutive) if str(consecutive).isdigit() else index + 1,
        "final_description": str(description).strip(),
        "expense_date": str(expense_date).strip(),
        "amount": amount_f,
        "bank": str(row.get("bank") or row.get("banco") or "").strip().upper(),
        "transaction_type": str(row.get("transaction_type") or row.get("tipo") or "Transferencia").strip(),
        "sheet_name": str(row.get("sheet_name") or row.get("pestaña") or "Historico").strip(),
        "sheet_row": str(row.get("sheet_row") or row.get("fila") or "").strip(),
        "status": "IMPORTADO",
        "source_filename": str(row.get("source_filename") or row.get("archivo") or "historico.csv").strip(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def detect_duplicates(records: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    """Detectar duplicados por image_hash y por group_code+consecutive."""
    seen_hashes: set[str] = set()
    seen_groups: dict[str, set[int]] = defaultdict(set)
    clean: list[dict] = []
    dup_hash: list[dict] = []
    dup_group: list[dict] = []

    for rec in records:
        h = rec["image_hash"]
        gk = (rec["group_code"], rec["consecutive"])

        if h in seen_hashes:
            dup_hash.append(rec)
            continue
        if rec["consecutive"] in seen_groups[rec["group_code"]]:
            dup_group.append(rec)
            continue

        seen_hashes.add(h)
        seen_groups[rec["group_code"]].add(rec["consecutive"])
        clean.append(rec)

    return clean, dup_hash, dup_group


def compute_max_consecutives(records: list[dict]) -> dict[str, int]:
    """Calcular el consecutivo maximo por grupo."""
    max_cons: dict[str, int] = defaultdict(int)
    for rec in records:
        g = rec["group_code"]
        c = rec["consecutive"]
        if c > max_cons[g]:
            max_cons[g] = c + 1
    return dict(max_cons)


def main() -> int:
    parser = argparse.ArgumentParser(description="Importar historicos a _Control")
    parser.add_argument("--file", type=str, help="Archivo CSV con historicos")
    parser.add_argument("--dry-run", action="store_true", help="Solo validar, no escribir")
    parser.add_argument("--owner", type=str, default="Ruben", help="Propietario por defecto")
    parser.add_argument("--output", type=str, help="Archivo JSON de salida")
    args = parser.parse_args()

    print("=" * 60)
    print("Importacion de historicos — Gastos IA")
    print("=" * 60)

    if not args.file:
        print("[INFO] No se especifico archivo de historicos (--file)")
        print("[INFO] Para importar: python scripts/validation/import_historicos.py --file datos.csv")
        print("[INFO] Continuando sin importacion — se parte de cero")

        # Generar evidencia de "sin historicos"
        output_path = Path(args.output) if args.output else PROJECT_ROOT / "harness" / "evidence" / "fase0" / "importacion-historicos.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "sin_historicos",
            "message": "No se proporciono archivo de historicos. Los consecutivos iniciaran en 1.",
            "records_imported": 0,
            "duplicates": 0,
            "max_consecutives": {},
        }
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[OK] Evidencia generada en {output_path}")
        return 0

    filepath = Path(args.file)
    if not filepath.exists():
        print(f"[FAIL] Archivo no encontrado: {filepath}")
        return 1

    print(f"\n[1/5] Leyendo {filepath}...")
    raw_rows = csv_reader(filepath)
    if not raw_rows:
        print("[FAIL] Archivo CSV vacio o ilegible")
        return 1
    print(f"[OK]   {len(raw_rows)} registros leidos")

    print(f"\n[2/5] Normalizando registros...")
    records = []
    skipped = 0
    for i, row in enumerate(raw_rows):
        norm = normalize_row(row, i, args.owner)
        if norm:
            records.append(norm)
        else:
            skipped += 1
    print(f"[OK]   {len(records)} normalizados, {skipped} omitidos (sin fecha)")

    print(f"\n[3/5] Detectando duplicados...")
    clean, dup_hash, dup_group = detect_duplicates(records)
    print(f"[OK]   {len(clean)} limpios, {len(dup_hash)} dup. por hash, {len(dup_group)} dup. por grupo+consecutivo")

    print(f"\n[4/5] Calculando consecutivos...")
    max_cons = compute_max_consecutives(clean)
    for group, next_val in sorted(max_cons.items()):
        print(f"  {group}: proximo consecutivo = {next_val}")

    if args.dry_run:
        print("\n[DRY-RUN] No se escribira en Google Sheets")
    else:
        print("\n[5/5] Escribiendo en Google Sheets...")
        creds_path = os.environ.get("GASTOSIA_GOOGLE_CREDENTIALS_PATH", "")
        sheet_id = os.environ.get("GASTOSIA_GOOGLE_SPREADSHEET_ID", "")
        if not creds_path or not sheet_id:
            print("[WARN] Credenciales no disponibles. Use --dry-run o defina variables de entorno")
        else:
            try:
                import gspread
                gc = gspread.service_account(filename=creds_path)
                sh = gc.open_by_key(sheet_id)
                ws_control = sh.worksheet("_Control")

                for rec in clean:
                    row = [rec.get(h, "") for h in CONTROL_HEADERS]
                    ws_control.append_row(row)

                print(f"[OK]   {len(clean)} registros escritos en _Control")
            except Exception as e:
                print(f"[FAIL] Error escribiendo en Sheets: {e}")
                return 1

    # Guardar resultados
    output_path = Path(args.output) if args.output else PROJECT_ROOT / "harness" / "evidence" / "fase0" / "importacion-historicos.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "completado",
        "file": str(filepath),
        "raw_rows": len(raw_rows),
        "records_imported": len(clean),
        "skipped_no_date": skipped,
        "duplicates_hash": len(dup_hash),
        "duplicates_group": len(dup_group),
        "max_consecutives": max_cons,
        "sample_records": clean[:5],
    }
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Resultados guardados en {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
