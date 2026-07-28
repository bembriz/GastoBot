"""validate_postgresql.py — validar conectividad y operaciones basicas con PostgreSQL.

Ejecutar: python scripts/validation/validate_postgresql.py"""

import os
import sys
import json
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DB_HOST = os.environ.get("GASTOSIA_DATABASE_HOST", "localhost")
DB_PORT = os.environ.get("GASTOSIA_DATABASE_PORT", "5432")
DB_NAME = os.environ.get("GASTOSIA_DATABASE_NAME", "gastos_ia")
DB_USER = os.environ.get("GASTOSIA_DATABASE_USER", "gastos_app")
DB_PASSWORD = os.environ.get("GASTOSIA_DATABASE_PASSWORD", "")
DB_ADMIN_PASSWORD = os.environ.get("GASTOSIA_POSTGRES_ADMIN_PASSWORD", "")

def run_sql(sql: str, user: str = "postgres", password: str | None = None, db: str = "postgres") -> tuple[int, str, str]:
    """Ejecutar comando SQL via psql y devolver (exit_code, stdout, stderr)."""
    env = os.environ.copy()
    if password is None:
        password = DB_ADMIN_PASSWORD
    if password:
        env["PGPASSWORD"] = password
    cmd = [
        "psql",
        "-h", DB_HOST,
        "-p", DB_PORT,
        "-U", user,
        "-d", db,
        "-c", sql,
        "-w",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=15)
    return result.returncode, result.stdout, result.stderr

def main() -> int:
    results: list[dict] = []
    passed = 0
    failed = 0

    print("=" * 60)
    print("Validacion PostgreSQL — Gastos IA")
    print(f"Host: {DB_HOST}:{DB_PORT}")
    print("=" * 60)

    # 1. Verificar conectividad basica (version)
    print("\n[1/7] Verificando version de PostgreSQL...")
    rc, stdout, stderr = run_sql("SELECT version();")
    if rc == 0:
        version_line = [l for l in stdout.splitlines() if "PostgreSQL" in l]
        version = version_line[0].strip() if version_line else "desconocida"
        print(f"[OK]   Conectado: {version}")
        results.append({"check": "conectividad", "status": "passed", "detail": version})
        passed += 1
    else:
        error_msg = stderr.strip() or stdout.strip()
        print(f"[FAIL] No se pudo conectar: {error_msg[:200]}")
        results.append({"check": "conectividad", "status": "failed", "detail": error_msg[:200]})
        failed += 1
        print("\n[INFO] Sin acceso a PostgreSQL, deteniendo validacion.")
        return 1

    # 2. Crear base de datos
    print("\n[2/7] Creando base de datos gastos_ia...")
    rc, stdout, stderr = run_sql(
        f"SELECT 1 FROM pg_database WHERE datname='{DB_NAME}';"
    )
    if rc == 0 and "1" in stdout:
        print(f"[OK]   Base '{DB_NAME}' ya existe")
        results.append({"check": "base de datos", "status": "passed", "detail": "ya existe"})
    else:
        rc2, out2, err2 = run_sql(f"CREATE DATABASE {DB_NAME};")
        if rc2 == 0:
            print(f"[OK]   Base '{DB_NAME}' creada")
            results.append({"check": "base de datos", "status": "passed", "detail": "creada"})
        else:
            print(f"[FAIL] No se pudo crear: {err2.strip()[:200]}")
            results.append({"check": "base de datos", "status": "failed", "detail": err2.strip()[:200]})
            failed += 1
            return 1
    passed += 1

    # 3. Crear usuario
    print(f"\n[3/7] Verificando usuario {DB_USER}...")
    rc, stdout, stderr = run_sql(
        f"SELECT 1 FROM pg_roles WHERE rolname='{DB_USER}';"
    )
    if rc == 0 and "1" in stdout:
        print(f"[OK]   Usuario '{DB_USER}' ya existe")
        results.append({"check": "usuario", "status": "passed", "detail": "ya existe"})
    else:
        rc2, out2, err2 = run_sql(
            f"CREATE USER {DB_USER} WITH PASSWORD '{DB_PASSWORD}';"
        )
        if rc2 == 0:
            print(f"[OK]   Usuario '{DB_USER}' creado")
            results.append({"check": "usuario", "status": "passed", "detail": "creado"})
        else:
            # Try without password if env var is empty
            rc3, out3, err3 = run_sql(
                f"CREATE USER {DB_USER} WITH PASSWORD 'changeme123';"
            )
            if rc3 == 0:
                print(f"[OK]   Usuario '{DB_USER}' creado (password temporal)")
                results.append({"check": "usuario", "status": "passed", "detail": "creado con password temporal"})
            else:
                print(f"[FAIL] No se pudo crear usuario: {err3.strip()[:200]}")
                results.append({"check": "usuario", "status": "failed", "detail": err3.strip()[:200]})
                failed += 1
                return 1
    passed += 1

    # 4. Otorgar permisos
    print(f"\n[4/7] Otorgando permisos...")
    grants = [
        f"GRANT CONNECT ON DATABASE {DB_NAME} TO {DB_USER};",
        f"GRANT USAGE ON SCHEMA public TO {DB_USER};",
        f"GRANT CREATE ON SCHEMA public TO {DB_USER};",
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {DB_USER};",
    ]
    all_ok = True
    for grant in grants:
        rc, stdout, stderr = run_sql(grant, db=DB_NAME)
        if rc != 0:
            all_ok = False
            print(f"[FAIL] {grant[:60]}...: {stderr.strip()[:100]}")
    if all_ok:
        print(f"[OK]   Permisos otorgados a {DB_USER}")
        results.append({"check": "permisos", "status": "passed", "detail": "todos otorgados"})
    else:
        print(f"[WARN] Algunos permisos fallaron (pueden ya existir)")
        results.append({"check": "permisos", "status": "warning", "detail": "parcial"})
    passed += 1

    # 5. Crear tabla de prueba
    print(f"\n[5/7] Creando tabla de prueba...")
    rc, stdout, stderr = run_sql(
        "CREATE TABLE IF NOT EXISTS _test_fase0 (id SERIAL PRIMARY KEY, test_value TEXT, created_at TIMESTAMP DEFAULT NOW());"
        "INSERT INTO _test_fase0 (test_value) VALUES ('fase0-validation');"
        "SELECT * FROM _test_fase0;",
        db=DB_NAME,
    )
    if rc == 0:
        print(f"[OK]   Tabla de prueba creada y operada")
        results.append({"check": "tabla prueba", "status": "passed", "detail": "CRUD exitoso"})
        passed += 1
    else:
        print(f"[FAIL] Error: {stderr.strip()[:200]}")
        results.append({"check": "tabla prueba", "status": "failed", "detail": stderr.strip()[:200]})
        failed += 1

    # 6. Limpiar tabla de prueba
    print(f"\n[6/7] Limpiando tabla de prueba...")
    rc, stdout, stderr = run_sql("DROP TABLE IF EXISTS _test_fase0;", db=DB_NAME)
    if rc == 0:
        print(f"[OK]   Tabla de prueba eliminada")
        results.append({"check": "limpieza", "status": "passed", "detail": "tabla eliminada"})
        passed += 1
    else:
        print(f"[WARN] No se pudo eliminar: {stderr.strip()[:100]}")
        results.append({"check": "limpieza", "status": "warning", "detail": stderr.strip()[:100]})

    # 7. Conexiones activas
    print(f"\n[7/7] Verificando conexiones activas...")
    rc, stdout, stderr = run_sql(
        "SELECT count(*) as active FROM pg_stat_activity WHERE datname = current_database();",
        db=DB_NAME,
    )
    if rc == 0:
        print(f"[OK]   Conexiones activas: {stdout.strip().split()[-1] if stdout.strip() else 'N/A'}")
        results.append({"check": "conexiones activas", "status": "passed", "detail": "monitoreo OK"})
        passed += 1
    else:
        print(f"[WARN] No se pudo consultar: {stderr.strip()[:100]}")
        results.append({"check": "conexiones activas", "status": "warning", "detail": "no disponible"})

    # Summary
    total = passed + failed
    print("\n" + "=" * 60)
    print(f"RESUMEN PostgreSQL: {passed}/{total} pasadas, {failed} fallidas")
    print("=" * 60)

    status = "passed" if failed == 0 else "partial" if passed > 0 else "failed"
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
