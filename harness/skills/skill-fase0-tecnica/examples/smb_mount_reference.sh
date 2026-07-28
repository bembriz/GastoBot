# SMB Mount Commands for Gastos IA

## Montaje de carpetas SMB en Ubuntu

```bash
# Instalar cifs-utils
sudo apt-get update && sudo apt-get install -y cifs-utils

# Crear puntos de montaje
sudo mkdir -p /mnt/gastosia/ruben/pendientes
sudo mkdir -p /mnt/gastosia/ruben/procesados
sudo mkdir -p /mnt/gastosia/ruben/errores
sudo mkdir -p /mnt/gastosia/esme/pendientes
sudo mkdir -p /mnt/gastosia/esme/procesados
sudo mkdir -p /mnt/gastosia/esme/errores
sudo mkdir -p /mnt/gastosia/logs

# Montar con credenciales desde variables de entorno
# NO hardcodear usuario/contraseña aquí

sudo mount -t cifs \
  "//${GASTOSIA_SMB_HOST:-SERVIDOR}/GastosIA/Ruben/pendientes" \
  /mnt/gastosia/ruben/pendientes \
  -o "username=${GASTOSIA_SMB_USERNAME},password=${GASTOSIA_SMB_PASSWORD},iocharset=utf8,vers=3.0"
```

## Verificación de estabilidad de archivos

```python
import os
import time
from pathlib import Path

def is_file_stable(filepath: Path, polls: int = 3, interval: float = 5.0) -> bool:
    """
    Verifica que un archivo este estable (tamano constante en N verificaciones).
    
    PRD §8.2: Tamano estable durante al menos 3 verificaciones.
    """
    sizes = []
    for _ in range(polls):
        try:
            stat = os.stat(filepath)
            sizes.append(stat.st_size)
            if len(sizes) >= 2 and sizes[-1] != sizes[-2]:
                time.sleep(interval)
                continue
            time.sleep(interval)
        except (PermissionError, OSError) as e:
            # Bloqueo temporal SMB - reintentar en siguiente ciclo
            # NO tratar como error definitivo (PRD §8.2)
            return False
    
    # Tamano estable en todas las verificaciones
    return len(sizes) >= polls and len(set(sizes)) == 1
```

## Manejo de bloqueos temporales SMB

```python
# PRD §8.2: Bloqueos temporales NO deben mover archivo a errores
# Capturar explicitamente y reintentar en siguiente ciclo

SMB_TRANSIENT_ERRORS = (PermissionError,)

def safe_open(filepath, mode='rb'):
    try:
        return open(filepath, mode)
    except SMB_TRANSIENT_ERRORS:
        # Bloqueo temporal: ignorar silenciosamente, reintentar en siguiente ciclo
        return None
    except OSError as e:
        if e.errno in (13, 16):  # EACCES, EBUSY
            return None
        raise
```
