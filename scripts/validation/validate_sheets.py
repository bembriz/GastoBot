"""validate_sheets.py — validar acceso y operaciones con Google Sheets API.

Ejecutar: python scripts/validation/validate_sheets.py

Requiere variables de entorno:
  - GASTOSIA_GOOGLE_CREDENTIALS_PATH
  - GASTOSIA_GOOGLE_SPREADSHEET_ID
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

COLUMNAS_MENSUALES = [
    "Fecha del gasto", "Categoría", "Descripción", "Empleado",
    "Pagado por", "Actividades", "Fecha contable", "Cuenta",
    "Precio unitario", "Cantidad", "Incluir impuestos",
    "Importe de impuestos", "Total", "Estado", "Banco", "Transaccion",
]

CONTROL_MINIMO = [
    "record_id", "image_hash", "owner", "group_code", "consecutive",
    "final_description", "expense_date", "amount", "bank",
    "transaction_type", "sheet_name", "sheet_row", "status",
    "source_filename", "created_at", "updated_at",
]


def check_prerequisites() -> list[dict]:
    """Verificar que las variables y archivos necesarios existen."""
    results = []
    creds_path = os.environ.get("GASTOSIA_GOOGLE_CREDENTIALS_PATH", "")
    sheet_id = os.environ.get("GASTOSIA_GOOGLE_SPREADSHEET_ID", "")

    if not creds_path:
        results.append({"check": "GASTOSIA_GOOGLE_CREDENTIALS_PATH", "status": "failed",
                        "detail": "variable no definida"})
    elif not Path(creds_path).exists():
        results.append({"check": "credencial JSON", "status": "failed",
                        "detail": f"archivo no encontrado: {creds_path}"})
    else:
        results.append({"check": "credencial JSON", "status": "passed",
                        "detail": f"encontrado: {creds_path}"})

    if not sheet_id:
        results.append({"check": "GASTOSIA_GOOGLE_SPREADSHEET_ID", "status": "failed",
                        "detail": "variable no definida"})
    else:
        results.append({"check": "spreadsheet ID", "status": "passed",
                        "detail": f"ID: ***{sheet_id[-4:]}" if len(sheet_id) > 4 else "definido"})

    return results


def validate_with_api(creds_path: str, sheet_id: str) -> list[dict]:
    """Ejecutar validaciones reales contra la API de Google Sheets."""
    results: list[dict] = []

    try:
        import gspread
    except ImportError:
        results.append({"check": "gspread instalado", "status": "failed",
                        "detail": "pip install gspread"})
        return results

    results.append({"check": "gspread instalado", "status": "passed",
                    "detail": "disponible"})

    try:
        gc = gspread.service_account(filename=creds_path)
        sh = gc.open_by_key(sheet_id)
        results.append({"check": "autenticacion", "status": "passed",
                        "detail": "cuenta de servicio autenticada"})

        # Listar pestañas
        worksheets = sh.worksheets()
        sheet_names = [ws.title for ws in worksheets]
        print(f"[OK]   Spreadsheet abierto: {sh.title}")
        print(f"[OK]   Pestañas: {', '.join(sheet_names)}")
        results.append({"check": "apertura spreadsheet", "status": "passed",
                        "detail": f"titulo={sh.title}, pestañas={len(sheet_names)}"})

        # Verificar/crear _Control
        has_control = "_Control" in sheet_names
        if has_control:
            ws_control = sh.worksheet("_Control")
            control_headers = ws_control.row_values(1)
            has_all = all(h in control_headers for h in CONTROL_MINIMO[:3])
            results.append({"check": "_Control", "status": "passed" if has_all else "partial",
                            "detail": f"existe, {len(control_headers)} encabezados"})
        else:
            ws_control = sh.add_worksheet(title="_Control", rows=100, cols=len(CONTROL_MINIMO))
            ws_control.append_row(CONTROL_MINIMO)
            results.append({"check": "_Control", "status": "passed",
                            "detail": "creada con encabezados minimos"})

        # Crear pestaña de prueba
        test_name = "_Test_Fase0"
        if test_name in sheet_names:
            sh.del_worksheet(sh.worksheet(test_name))
        ws_test = sh.add_worksheet(title=test_name, rows=10, cols=16)
        ws_test.append_row(COLUMNAS_MENSUALES)
        ws_test.append_row([
            "2026-07-28", "Test", "Fase 0 validacion", "RUBEN BENJAMIN VAZQUEZ EMBRIZ",
            "Empresa", "", "", "Test Account",
            "100.00", "1", "", "", "100.00", "Por reportar", "NU", "Transferencia",
        ])

        # Leer de vuelta
        row = ws_test.row_values(2)
        if len(row) == 16 and row[8] == "100.00":
            results.append({"check": "escritura/lectura", "status": "passed",
                            "detail": "datos integros"})
        else:
            results.append({"check": "escritura/lectura", "status": "failed",
                            "detail": f"datos inconsistentes: {row}"})

        # Limpiar
        sh.del_worksheet(ws_test)
        results.append({"check": "limpieza", "status": "passed",
                        "detail": f"pestaña '{test_name}' eliminada"})

    except Exception as e:
        results.append({"check": "API error", "status": "failed",
                        "detail": f"{type(e).__name__}: {str(e)[:200]}"})

    return results


def main() -> int:
    print("=" * 60)
    print("Validacion Google Sheets — Gastos IA")
    print("=" * 60)

    all_results = []

    # Pre-checks
    print("\n[Pre-checks]")
    pre_results = check_prerequisites()
    all_results.extend(pre_results)
    for r in pre_results:
        status = "OK" if r["status"] == "passed" else "FAIL"
        print(f"[{status}] {r['check']}: {r['detail']}")

    # API validation (solo si pre-checks pasan)
    creds_path = os.environ.get("GASTOSIA_GOOGLE_CREDENTIALS_PATH", "")
    sheet_id = os.environ.get("GASTOSIA_GOOGLE_SPREADSHEET_ID", "")

    if creds_path and sheet_id and Path(creds_path).exists():
        print("\n[API validation]")
        api_results = validate_with_api(creds_path, sheet_id)
        all_results.extend(api_results)
        for r in api_results:
            status = "OK" if r["status"] == "passed" else "WARN" if r["status"] == "partial" else "FAIL"
            print(f"[{status}] {r['check']}: {r['detail']}")
    else:
        print("\n[INFO] Credenciales no disponibles, omitiendo validacion API")
        print("[INFO] Defina GASTOSIA_GOOGLE_CREDENTIALS_PATH y GASTOSIA_GOOGLE_SPREADSHEET_ID")

    # Summary
    passed = sum(1 for r in all_results if r["status"] == "passed")
    failed = sum(1 for r in all_results if r["status"] == "failed")
    total = passed + failed
    print("\n" + "=" * 60)
    print(f"RESUMEN Sheets: {passed}/{total} pasadas, {failed} fallidas")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
