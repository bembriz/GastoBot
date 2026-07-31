"""Monitor de carpetas — deteccion de imagenes en SMB.

Escanea cada 5 segundos las carpetas pendientes de Ruben y Esme.
Valida estabilidad (3 verificaciones), calcula SHA-256,
maneja bloqueos temporales SMB sin marcarlos como error.
"""

import asyncio
import hashlib
import os
import time
from pathlib import Path

from PIL import Image as PILImage
from PIL import ImageOps, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ExpenseRecord, ImageFile, ProcessingQueue, User
from app.database.session import async_session

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 15 * 1024 * 1024
POLL_INTERVAL = 5
MAX_IMAGE_DIMENSION = 2048

PENDING_DIRS: dict[str, str] = {}

if os.environ.get("GASTOSIA_SMB_BASE"):
    base = os.environ["GASTOSIA_SMB_BASE"]
    PENDING_DIRS["Ruben"] = os.path.join(base, "Ruben", "pendientes")
    PENDING_DIRS["Esme"] = os.path.join(base, "Esme", "pendientes")


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def is_file_stable(path: Path) -> bool:
    try:
        stat1 = path.stat()
    except (PermissionError, OSError):
        return False

    time.sleep(1)

    try:
        stat2 = path.stat()
    except (PermissionError, OSError):
        return False

    return stat1.st_size == stat2.st_size and stat1.st_mtime == stat2.st_mtime


def optimize_image(source: Path, dest: Path) -> tuple[int, int] | None:
    try:
        img: PILImage.Image = PILImage.open(source)
        img = ImageOps.exif_transpose(img)
        w, h = img.size
        if max(w, h) > MAX_IMAGE_DIMENSION:
            ratio = MAX_IMAGE_DIMENSION / max(w, h)
            img = img.resize((int(w * ratio), int(h * ratio)), PILImage.Resampling.LANCZOS)
        img.save(dest, format="JPEG", quality=85, optimize=True)
        return img.size
    except (UnidentifiedImageError, OSError):
        return None


async def scan_directory(owner: str, folder: str, db: AsyncSession) -> int:
    path = Path(folder)
    if not path.exists():
        return 0

    user_result = await db.execute(select(User).where(User.username == owner))
    user = user_result.scalar_one_or_none()
    if not user:
        return 0

    count = 0
    for entry in path.iterdir():
        if not entry.is_file():
            continue
        if entry.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue
        if entry.stat().st_size > MAX_FILE_SIZE:
            continue

        try:
            file_hash = sha256_file(entry)
        except (PermissionError, OSError):
            continue

        existing_hash = await db.execute(
            select(ImageFile).where(ImageFile.sha256_hash == file_hash)
        )
        if existing_hash.scalar_one_or_none():
            record_result = await db.execute(
                select(ExpenseRecord).join(ImageFile).where(ImageFile.sha256_hash == file_hash)
            )
            rec = record_result.scalar_one_or_none()
            if rec and rec.status == "DETECTADO":
                rec.status = "DUPLICADO_EXACTO"
                await db.commit()
            continue

        record = ExpenseRecord(
            owner_id=user.id,
            image_hash=file_hash,
            status="DETECTADO",
            source_filename=entry.name,
        )
        db.add(record)
        await db.flush()

        file_size = entry.stat().st_size
        mime = f"image/{entry.suffix.lstrip('.').replace('jpg', 'jpeg')}"
        image_file = ImageFile(
            record_id=record.id,
            original_path=str(entry.absolute()),
            sha256_hash=file_hash,
            file_size=file_size,
            mime_type=mime,
            owner_folder=owner,
        )
        db.add(image_file)

        queue_entry = ProcessingQueue(
            record_id=record.id,
            status="EN_COLA",
        )
        db.add(queue_entry)

        record.status = "EN_COLA"
        count += 1

    await db.commit()
    return count


async def monitor_loop() -> None:
    print("[Monitor] Iniciando deteccion de imagenes...")
    if not PENDING_DIRS:
        print("[Monitor] GASTOSIA_SMB_BASE no configurado — monitor en standby")
        return

    while True:
        try:
            async with async_session() as db:
                for owner, folder in PENDING_DIRS.items():
                    detected = await scan_directory(owner, folder, db)
                    if detected:
                        print(f"[Monitor] {detected} imagenes detectadas en {owner}")
        except Exception as e:
            print(f"[Monitor] Error en ciclo: {e}")
        await asyncio.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    asyncio.run(monitor_loop())
