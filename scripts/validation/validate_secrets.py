"""validate_secrets.py — validar mecanismo de variables de entorno para Gastos IA.

Ejecutar: GASTOSIA_TEST=1 python scripts/validation/validate_secrets.py"""

import os
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_EXAMPLE = PROJECT_ROOT / ".env.example"

REQUIRED_VARS = [
    "GASTOSIA_APP_ENV",
    "GASTOSIA_DATABASE_HOST",
    "GASTOSIA_DATABASE_PORT",
    "GASTOSIA_DATABASE_NAME",
    "GASTOSIA_DATABASE_USER",
    "GASTOSIA_DATABASE_PASSWORD",
    "GASTOSIA_SESSION_SECRET",
    "GASTOSIA_SMB_USERNAME",
    "GASTOSIA_SMB_PASSWORD",
    "GASTOSIA_GOOGLE_CREDENTIALS_PATH",
    "GASTOSIA_GOOGLE_SPREADSHEET_ID",
    "GASTOSIA_RUBEN_INITIAL_PASSWORD",
    "GASTOSIA_ESME_INITIAL_PASSWORD",
    "GASTOSIA_POSTGRES_ADMIN_PASSWORD",
]

OPTIONAL_VARS: list[str] = []

def load_env_example() -> dict[str, str]:
    """Parsear .env.example y devolver diccionario clave -> valor (sin secretos)."""
    if not ENV_EXAMPLE.exists():
        return {}
    result: dict[str, str] = {}
    for line in ENV_EXAMPLE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            result[key.strip()] = value.strip()
    return result

def mask(value: str) -> str:
    """Enmascarar valor sensible para output seguro."""
    if not value:
        return "<vacío>"
    if len(value) <= 4:
        return "***"
    return value[:2] + "***" + value[-2:]

def main() -> int:
    results: list[dict] = []
    warnings: list[str] = []
    passed = 0
    failed = 0

    print("=" * 60)
    print("Validacion de mecanismo de secretos — Gastos IA")
    print("=" * 60)

    # 1. Verificar .env.example
    env_vars = load_env_example()
    if not env_vars:
        print("[FAIL] .env.example no existe o está vacío")
        results.append({"check": ".env.example existe", "status": "failed", "detail": "archivo no encontrado"})
        failed += 1
    else:
        print(f"[OK]   .env.example encontrado con {len(env_vars)} variables")
        results.append({"check": ".env.example existe", "status": "passed", "detail": f"{len(env_vars)} variables"})
        passed += 1

    # 2. Verificar variables requeridas en .env.example
    for var in REQUIRED_VARS:
        if var in env_vars:
            status = "passed"
            detail = f"presente, valor: {mask(env_vars[var])}" if env_vars[var] else "presente, sin valor (ok)"
            passed += 1
        else:
            status = "failed"
            detail = "FALTA en .env.example"
            failed += 1
        print(f"[{'OK' if status == 'passed' else 'FAIL'}] {var}: {detail}")
        results.append({"check": f"var {var} en .env.example", "status": status, "detail": detail})

    # 3. Verificar que .env.example NO tiene valores reales
    sensitive_patterns: list[str] = []
    for key, val in env_vars.items():
        if len(val) > 4 and val not in ("gastos_ia", "gastos_app", "5432", "production", ""):
            if val != "changeme" and not val.startswith("/"):
                sensitive_patterns.append(f"{key}={'***'}")
    if sensitive_patterns:
        print(f"[WARN] Posibles valores reales en .env.example ({len(sensitive_patterns)}):")
        for s in sensitive_patterns:
            print(f"       {s}")
        warnings.append(f"{len(sensitive_patterns)} variables sospechosas en .env.example")
    else:
        print("[OK]   .env.example sin valores reales sospechosos")
        results.append({"check": "sin valores reales", "status": "passed", "detail": "todas vacías o placeholder"})
        passed += 1

    # 4. Verificar os.environ.get() funciona
    os.environ["GASTOSIA_TEST_VAR"] = "test_value_12345"
    test_val = os.environ.get("GASTOSIA_TEST_VAR")
    if test_val == "test_value_12345":
        print("[OK]   os.environ.get() funciona correctamente")
        results.append({"check": "os.environ.get()", "status": "passed", "detail": "lectura correcta"})
        passed += 1
    else:
        print(f"[FAIL] os.environ.get() devolvió: {test_val}")
        results.append({"check": "os.environ.get()", "status": "failed", "detail": "error de lectura"})
        failed += 1
    del os.environ["GASTOSIA_TEST_VAR"]

    # 5. Simular validacion de longitud de GASTOSIA_SESSION_SECRET
    test_secret = os.environ.get("GASTOSIA_SESSION_SECRET", "")
    if test_secret:
        if len(test_secret) >= 32:
            print(f"[OK]   GASTOSIA_SESSION_SECRET longitud suficiente: {len(test_secret)} chars")
            results.append({"check": "SESSION_SECRET length", "status": "passed", "detail": f"{len(test_secret)} chars"})
            passed += 1
        else:
            print(f"[FAIL] GASTOSIA_SESSION_SECRET muy corto: {len(test_secret)} < 32")
            results.append({"check": "SESSION_SECRET length", "status": "failed", "detail": f"{len(test_secret)} < 32"})
            failed += 1
    else:
        print("[INFO] GASTOSIA_SESSION_SECRET no definido — validacion omitida")
        results.append({"check": "SESSION_SECRET length", "status": "skipped", "detail": "no definida en entorno"})

    # 6. Verificar fail-safe: falta variable obligatoria
    missing = [v for v in REQUIRED_VARS if v not in env_vars]
    if missing:
        print(f"[FAIL] Faltan {len(missing)} variables obligatorias en .env.example")
        results.append({"check": "variables obligatorias completas", "status": "failed", "detail": f"faltan: {', '.join(missing)}"})
        failed += 1
    else:
        print("[OK]   Todas las variables obligatorias documentadas")
        results.append({"check": "variables obligatorias completas", "status": "passed", "detail": "14/14"})
        passed += 1

    # 7. Verificar enmascaramiento en output
    sensitive_value = "super_secret_token_12345"
    masked = mask(sensitive_value)
    if "super_secret" not in masked:
        print(f"[OK]   Enmascaramiento funciona: '{masked}'")
        results.append({"check": "enmascaramiento", "status": "passed", "detail": "valores sensibles ocultos"})
        passed += 1
    else:
        print(f"[FAIL] Enmascaramiento no funciona: '{masked}'")
        results.append({"check": "enmascaramiento", "status": "failed", "detail": "secreto visible"})
        failed += 1

    # Summary
    total = passed + failed
    print("\n" + "=" * 60)
    print(f"RESUMEN: {passed}/{total} pasadas, {failed} fallidas, {len(warnings)} warnings")
    print("=" * 60)

    if warnings:
        print("\nWARNINGS:")
        for w in warnings:
            print(f"  - {w}")

    status = "passed" if failed == 0 else "partial" if passed > 0 else "failed"
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
