"""Traslado de imagenes desde procesados hacia gastobot/enviadas/<mes>/."""

import filecmp
import hashlib
import os
import shutil
from pathlib import Path
from typing import Any


def _short_hash(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()[:8]


def move_image_to_sent(image: Any, month_label: str) -> str | None:
    """Mover la imagen a <GASTOSIA_SENT_IMAGES_DIR>/<month_label>/.

    No lanza excepciones: ante cualquier fallo devuelve None y deja la imagen
    donde estaba. Si el destino ya existe con el mismo contenido, elimina el
    origen para que el reenvio sea idempotente.
    """
    try:
        base = os.environ.get("GASTOSIA_SENT_IMAGES_DIR", "").strip()
        if not base:
            print("[Imagenes] GASTOSIA_SENT_IMAGES_DIR no configurado", flush=True)
            return None

        source_path = getattr(image, "original_path", None)
        if not source_path:
            return None

        source = Path(source_path)
        if not source.exists():
            print(f"[Imagenes] Archivo no encontrado: {source}", flush=True)
            return None

        dest_dir = Path(base) / month_label
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / source.name

        if source.resolve() == dest.resolve():
            image.original_path = str(dest)
            return str(dest)

        if dest.exists():
            if filecmp.cmp(source, dest, shallow=False):
                os.remove(source)
            else:
                suffix = source.suffix
                dest = dest_dir / f"{source.stem}-{_short_hash(source)}{suffix}"
                if dest.exists():
                    os.remove(source)
                else:
                    shutil.copy2(source, dest)
                    os.remove(source)
        else:
            shutil.copy2(source, dest)
            os.remove(source)

        image.original_path = str(dest)
        print(f"[Imagenes] Movido a enviadas: {dest}", flush=True)
        return str(dest)
    except Exception as e:
        print(f"[Imagenes] Error moviendo imagen: {e}", flush=True)
        return None
