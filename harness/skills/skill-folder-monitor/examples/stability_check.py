#!/usr/bin/env python3
"""
Ejemplo de verificacion de estabilidad de archivos y manejo de bloqueos SMB.

Referencia para app/images/file_utils.py - NO ejecutar en produccion directamente.
"""

import errno
import hashlib
import os
import time
from pathlib import Path

# Constantes (PRD §8.2, §31.3)
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB
STABILITY_CHECKS = 3
STABILITY_INTERVAL = 5.0  # segundos entre verificaciones


def calculate_sha256(filepath: str) -> str:
    """Calcula SHA-256 de un archivo."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def is_smb_transient_error(error: OSError) -> bool:
    """
    PRD §8.2: Determina si un error es bloqueo temporal SMB.
    Estos NO deben tratarse como error definitivo.
    """
    return error.errno in (errno.EACCES, errno.EBUSY)


def safe_stat(filepath: str) -> os.stat_result | None:
    """
    Intenta obtener stat del archivo capturando bloqueos SMB.

    Retorna None si es bloqueo temporal (reintentar en siguiente ciclo).
    Lanza la excepcion si es otro tipo de error.
    """
    try:
        return os.stat(filepath)
    except PermissionError:
        # Bloqueo temporal SMB: reintentar en siguiente ciclo
        return None
    except OSError as e:
        if is_smb_transient_error(e):
            return None
        raise


def is_file_stable(filepath: str) -> bool:
    """
    Verifica estabilidad: tamano constante en STABILITY_CHECKS verificaciones.

    PRD §8.2: Tamano estable durante 3 verificaciones, fecha de modificacion estable.
    """
    path = Path(filepath)
    if not path.exists():
        return False

    sizes = []
    mod_times = []

    for _ in range(STABILITY_CHECKS):
        stat = safe_stat(filepath)
        if stat is None:
            # Bloqueo temporal: archivo no esta listo
            return False

        sizes.append(stat.st_size)
        mod_times.append(stat.st_mtime)

        time.sleep(STABILITY_INTERVAL)

    # Todas las verificaciones deben tener el mismo tamano
    return len(set(sizes)) == 1 and len(set(mod_times)) == 1


def is_allowed_extension(filepath: str) -> bool:
    """Verifica extension permitida (PRD §31.3)."""
    ext = Path(filepath).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


def is_valid_size(filepath: str) -> bool:
    """Verifica que el archivo no exceda 15 MB (PRD §31.3)."""
    stat = safe_stat(filepath)
    if stat is None:
        return False
    return stat.st_size <= MAX_FILE_SIZE


# Ejemplo de uso asincrono
async def scan_folder_demo(watch_path: str, known_files: set):
    """Demo de escaneo de carpeta - referencia para FolderMonitor.scan()."""
    path = Path(watch_path)

    for filepath in path.iterdir():
        if not filepath.is_file():
            continue

        fpath = str(filepath)

        # Filtrar extension
        if not is_allowed_extension(fpath):
            continue

        # Verificar tamano
        if not is_valid_size(fpath):
            print(f"[WARN] Archivo muy grande: {fpath}")
            continue

        # Verificar estabilidad
        if not is_file_stable(fpath):
            print(f"[INFO] Archivo inestable, reintentando: {fpath}")
            continue

        # Procesar si es nuevo
        if fpath not in known_files:
            sha256 = calculate_sha256(fpath)
            print(f"[DETECTED] {fpath} -> {sha256}")
            known_files.add(fpath)


if __name__ == "__main__":
    print("Este archivo es referencia. Ejecuta test_folder_monitor.py para pruebas reales.")
