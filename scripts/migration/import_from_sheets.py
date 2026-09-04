"""Importar registros historicos desde Google Sheets a la BD nueva.

Migra:
  1. Catalogos (categorias/cuentas) desde docs/Catalogo.xlsx.
  2. Registros de la pestana `_Control` (historicos, status HISTORICO -> ENVIADO).
  3. Registros de las pestanas mensuales del formato `Mes-AA` (p. ej. Julio-26),
     mapeando categoria/cuenta por descripcion contra el catalogo sembrado.
  4. Vincula imagenes de {GASTOSIA_SMB_BASE}/{Owner}/procesados cuando la fecha
     del nombre de archivo (patron WhatsApp) coincide con la fecha del gasto.

Idempotente: omite registros cuyo image_hash ya existe.

Ejecutar dentro del contenedor app:
  docker exec gastos-ia-app uv run --no-sync \
      python scripts/migration/import_from_sheets.py [--dry-run]

Para reparar solo los vinculos categoria->cuenta (parent_id) en una BD ya
migrada, sin tocar registros:
  docker exec gastos-ia-app uv run --no-sync \
      python scripts/migration/import_from_sheets.py --catalogs-only [--dry-run]
"""

import argparse
import asyncio
import hashlib
import os
import re
import sys
import uuid
import zipfile
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from xml.etree import ElementTree as ET

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import CatalogCache, ExpenseRecord, ImageFile, User
from app.database.session import async_session
from app.sheets.client import get_spreadsheet

CONTROL_TAB = "_Control"
MONTH_TAB_RE = re.compile(r"^[A-Za-z]+-\d{2}$")
DESC_RE = re.compile(r"^([A-Za-z0-9]+-[0-9]+)-(\d+)-(.*)$")
FILENAME_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
CATALOGO_PATH = Path("/app/docs/Catalogo.xlsx")
SMB_BASE = os.environ.get("GASTOSIA_SMB_BASE", "/data/gastos")
XLSX_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def parse_datetime(value: str) -> datetime | None:
    value = value.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def parse_amount(value: str) -> Decimal | None:
    value = value.strip().replace(",", "").replace("$", "")
    if not value:
        return None
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def parse_transaction_type(value: str) -> str | None:
    """Normaliza al dominio del check constraint: 'Transferencia' | 'Credito' | None."""
    v = value.strip().lower().replace("é", "e")
    if v.startswith("transf"):
        return "Transferencia"
    if v.startswith("credito"):
        return "Credito"
    return None


def read_catalogo_rows(path: Path) -> list[tuple[str, str]]:
    """Lee pares (categoria, cuenta) de docs/Catalogo.xlsx sin dependencias extra."""
    z = zipfile.ZipFile(path)
    shared = ET.fromstring(z.read("xl/sharedStrings.xml"))
    strings = [
        "".join(t.text or "" for t in si.iter(XLSX_NS + "t")) for si in shared.iter(XLSX_NS + "si")
    ]
    sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    rows: list[tuple[str, str]] = []
    for row in sheet.iter(XLSX_NS + "row"):
        vals: dict[str, str] = {}
        for cell in row.iter(XLSX_NS + "c"):
            ref = cell.get("r", "")
            col = re.sub(r"\d", "", ref)
            v = cell.find(XLSX_NS + "v")
            if v is None or v.text is None:
                continue
            vals[col] = strings[int(v.text)] if cell.get("t") == "s" else v.text
        cat, acc = vals.get("A", "").strip(), vals.get("B", "").strip()
        if cat and acc and cat.lower() != "categoría":
            rows.append((cat, acc))
    return rows


async def seed_catalogs(db: AsyncSession, dry_run: bool) -> dict[str, uuid.UUID]:
    """Siembra catalogos desde Catalogo.xlsx. Devuelve mapa descripcion -> id.

    Cada par (categoria, cuenta) del xlsx liga la categoria a su cuenta via
    parent_id. Al re-ejecutar sobre una BD ya sembrada repara (backfill) los
    parent_id faltantes o distintos.
    """
    result = await db.execute(select(CatalogCache))
    entries = {e.description: e for e in result.scalars()}
    mapping: dict[str, uuid.UUID] = {d: e.id for d, e in entries.items()}

    created = linked = 0
    used_codes: set[tuple[str, str]] = {(e.catalog_type, e.code) for e in entries.values()}
    pairs = read_catalogo_rows(CATALOGO_PATH)
    for cat_str, acc_str in pairs:
        for catalog_type, full in (("categoria", cat_str), ("cuenta", acc_str)):
            if full in mapping:
                continue
            if catalog_type == "categoria":
                m = re.match(r"\[(.*?)\]\s*(.*)", full)
                code = m.group(1) if m else full
            else:
                code = full.split(" ", 1)[0]
            code = code[:50]
            suffix = 2  # codigo truncado a varchar(50); evitar colisiones
            while (catalog_type, code) in used_codes:
                tail = f"~{suffix}"
                code = f"{code[: 50 - len(tail)]}{tail}"
                suffix += 1
            used_codes.add((catalog_type, code))
            entry = CatalogCache(
                id=uuid.uuid4(), catalog_type=catalog_type, code=code, description=full
            )
            mapping[full] = entry.id
            entries[full] = entry
            created += 1
            if not dry_run:
                db.add(entry)

    for cat_str, acc_str in pairs:
        cat_entry, acc_entry = entries.get(cat_str), entries.get(acc_str)
        if cat_entry and acc_entry and cat_entry.parent_id != acc_entry.id:
            cat_entry.parent_id = acc_entry.id
            linked += 1

    if not dry_run:
        await db.flush()
    print(
        f"[catalogos] {created} entradas nuevas, {linked} vinculos padre, {len(mapping)} totales"
    )
    return mapping


async def load_users(db: AsyncSession) -> dict[str, User]:
    result = await db.execute(select(User))
    users = {u.username: u for u in result.scalars()}
    missing = {"Ruben", "Esme"} - set(users)
    if missing:
        raise RuntimeError(f"Faltan usuarios en la BD: {missing}. Ejecuta scripts/init_users.py")
    return users


async def hash_exists(db: AsyncSession, image_hash: str) -> bool:
    result = await db.execute(
        select(ExpenseRecord.id).where(ExpenseRecord.image_hash == image_hash)
    )
    return result.scalar_one_or_none() is not None


async def import_control_tab(
    db: AsyncSession, users: dict[str, User], dry_run: bool
) -> tuple[int, int]:
    """Importa la pestana _Control (historicos). Devuelve (insertados, omitidos)."""
    ws = get_spreadsheet().worksheet(CONTROL_TAB)
    rows = ws.get_all_values()
    idx = {h: i for i, h in enumerate(rows[0])}
    inserted = skipped = collisions = 0

    # Pares (group_code, consecutive) ya usados: el indice es UNIQUE y los
    # historicos pueden traer duplicados; en colision se importa sin el par.
    result = await db.execute(
        select(ExpenseRecord.group_code, ExpenseRecord.consecutive).where(
            ExpenseRecord.group_code.isnot(None), ExpenseRecord.consecutive.isnot(None)
        )
    )
    used_pairs: set[tuple[str, int]] = {(g, c) for g, c in result.all()}

    for r in rows[1:]:
        if not any(r):
            continue
        image_hash = r[idx["image_hash"]]
        if await hash_exists(db, image_hash):
            skipped += 1
            continue
        group_code = r[idx["group_code"]] or None
        consecutive = int(r[idx["consecutive"]]) if r[idx["consecutive"]].isdigit() else None
        if group_code and consecutive is not None:
            if (group_code, consecutive) in used_pairs:
                group_code, consecutive = None, None
                collisions += 1
            else:
                used_pairs.add((group_code, consecutive))
        owner = users.get(r[idx["owner"]], users["Ruben"])
        record = ExpenseRecord(
            id=uuid.uuid4(),
            owner_id=owner.id,
            image_hash=image_hash,
            transaction_date=parse_datetime(r[idx["expense_date"]]),
            amount=parse_amount(r[idx["amount"]]),
            final_description=r[idx["final_description"]] or None,
            group_code=group_code,
            consecutive=consecutive,
            bank=r[idx["bank"]] or None,
            transaction_type=parse_transaction_type(r[idx["transaction_type"]]),
            status="ENVIADO",
            sheet_name=r[idx["sheet_name"]] or None,
            sheet_row=int(r[idx["sheet_row"]]) if r[idx["sheet_row"]].isdigit() else None,
            source_filename=r[idx["source_filename"]] or None,
        )
        inserted += 1
        if not dry_run:
            db.add(record)

    print(
        f"[_Control] {inserted} registros importados, {skipped} omitidos (ya existian), "
        f"{collisions} colisiones grupo/consecutivo (importados sin el par)"
    )
    return inserted, skipped


def scan_procesados() -> dict[str, list[tuple[Path, str]]]:
    """Escanea {SMB_BASE}/{Owner}/procesados. Devuelve owner -> [(path, fecha YYYY-MM-DD)]."""
    result: dict[str, list[tuple[Path, str]]] = {}
    for owner in ("Ruben", "Esme"):
        folder = Path(SMB_BASE) / owner / "procesados"
        files = []
        if folder.is_dir():
            for p in sorted(folder.iterdir()):
                if p.suffix.lower() not in IMAGE_EXTS or not p.is_file():
                    continue
                m = FILENAME_DATE_RE.search(p.name)
                files.append((p, m.group(1) if m else ""))
        result[owner] = files
    return result


async def import_month_tabs(
    db: AsyncSession, users: dict[str, User], catalogs: dict[str, uuid.UUID], dry_run: bool
) -> tuple[int, int, int]:
    """Importa pestanas Mes-AA. Devuelve (insertados, omitidos, imagenes vinculadas)."""
    sh = get_spreadsheet()
    procesados = scan_procesados()
    inserted = skipped = linked = collisions = 0

    result = await db.execute(
        select(ExpenseRecord.group_code, ExpenseRecord.consecutive).where(
            ExpenseRecord.group_code.isnot(None), ExpenseRecord.consecutive.isnot(None)
        )
    )
    used_pairs: set[tuple[str, int]] = {(g, c) for g, c in result.all()}

    for ws in sh.worksheets():
        if not MONTH_TAB_RE.match(ws.title):
            continue
        rows = ws.get_all_values()
        for i, r in enumerate(rows[1:], start=2):
            if not any(r):
                continue
            r = r + [""] * (16 - len(r))
            fecha, categoria, desc, empleado = r[0], r[1], r[2], r[3]
            cuenta, total, banco, transaccion = r[7], r[12], r[14], r[15]

            image_hash = sha256_text(f"sheet|{ws.title}|{i}")
            if await hash_exists(db, image_hash):
                skipped += 1
                continue

            owner = users["Esme"] if "ESME" in empleado.upper() else users["Ruben"]
            m = DESC_RE.match(desc.strip())
            group_code = m.group(1) if m else None
            consecutive = int(m.group(2)) if m else None
            if group_code and consecutive is not None:
                if (group_code, consecutive) in used_pairs:
                    group_code, consecutive = None, None
                    collisions += 1
                else:
                    used_pairs.add((group_code, consecutive))
            ticket = m.group(3).strip() if m else desc.strip()
            tx_date = parse_datetime(fecha)

            record = ExpenseRecord(
                id=uuid.uuid4(),
                owner_id=owner.id,
                image_hash=image_hash,
                transaction_date=tx_date,
                amount=parse_amount(total),
                ticket_description=ticket or None,
                final_description=desc.strip() or None,
                group_code=group_code,
                consecutive=consecutive,
                category_id=catalogs.get(categoria.strip()),
                account_id=catalogs.get(cuenta.strip()),
                bank=banco.strip() or None,
                transaction_type=parse_transaction_type(transaccion),
                status="ENVIADO",
                sheet_name=ws.title,
                sheet_row=i,
                sent_at=datetime.now(UTC),
            )
            inserted += 1

            # Vincular imagen: coincidencia exacta de fecha en nombre de archivo (WhatsApp)
            already_imported = False
            if tx_date is not None and owner.username in procesados:
                date_str = tx_date.strftime("%Y-%m-%d")
                candidates = procesados[owner.username]
                for pos, (path, fdate) in enumerate(candidates):
                    if fdate == date_str:
                        file_hash = sha256_file(path)
                        if await hash_exists(db, file_hash):
                            already_imported = True
                            candidates.pop(pos)
                            break
                        record.image_hash = file_hash
                        image = ImageFile(
                            id=uuid.uuid4(),
                            record_id=record.id,
                            original_path=str(path),
                            sha256_hash=file_hash,
                            file_size=path.stat().st_size,
                            mime_type="image/"
                            + path.suffix.lstrip(".").lower().replace("jpg", "jpeg"),
                            owner_folder=owner.username,
                        )
                        candidates.pop(pos)
                        linked += 1
                        if not dry_run:
                            db.add(image)
                        break

            if already_imported:
                inserted -= 1
                skipped += 1
                continue

            if not dry_run:
                db.add(record)

        print(f"[{ws.title}] procesado")

    print(
        f"[Mes-AA] {inserted} registros importados, {skipped} omitidos, "
        f"{linked} imagenes vinculadas, {collisions} colisiones grupo/consecutivo"
    )
    return inserted, skipped, linked


async def main(dry_run: bool, catalogs_only: bool) -> int:
    async with async_session() as db:
        catalogs = await seed_catalogs(db, dry_run)
        if not catalogs_only:
            users = await load_users(db)
            await import_control_tab(db, users, dry_run)
            await import_month_tabs(db, users, catalogs, dry_run)
        if dry_run:
            await db.rollback()
            print("\n[dry-run] Sin cambios en la BD")
        else:
            await db.commit()
            print("\n[OK] Migracion completada y confirmada")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--catalogs-only",
        action="store_true",
        help="Solo siembra/repara catalogos (parent_id); no importa registros",
    )
    args = parser.parse_args()
    sys.exit(asyncio.run(main(args.dry_run, args.catalogs_only)))
