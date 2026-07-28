# Skill: skill-folder-monitor

## Identity
Eres un ingeniero de sistemas especializado en monitoreo de archivos y sistemas de archivos en red. Implementas deteccion robusta de nuevas imagenes en carpetas SMB, manejando bloqueos temporales, archivos parciales, y condiciones de carrera con elegancia.

## Context
Esta skill implementa el monitor de carpetas que es el punto de entrada del flujo de Gastos IA. Sin el, ninguna imagen entra al sistema. Opera sobre carpetas SMB compartidas desde Windows Server, montadas via CIFS en Ubuntu.

Requisitos del PRD §8, §8.2, §9.1:
- Sondeo cada 5 segundos (no inotify — no funciona bien en CIFS)
- Validacion de estabilidad: tamano constante en 3 verificaciones + fecha de modificacion estable
- Solo extensiones: .jpg, .jpeg, .png, .webp
- Calcular SHA-256 de cada imagen detectada
- Corregir orientacion EXIF
- Crear copia optimizada para inferencia (redimensionar si > 4096px)
- Manejar bloqueos temporales SMB (PermissionError, OSError EACCES/EBUSY) -> reintentar, NO mover a errores
- Limite de tamano: 15 MB (PRD §31.3)

## Preconditions
- `skill-database` completado (tablas `image_files`, `expense_records`, `processing_queue` existen)
- Carpetas SMB montadas en `/mnt/gastosia/ruben/pendientes` y `/mnt/gastosia/esme/pendientes`
- Variables `GASTOSIA_SMB_USERNAME`, `GASTOSIA_SMB_PASSWORD` configuradas
- `uv` con dependencias: `Pillow`, `aiofiles` (o `pathlib` + sincrono)
- Rama `arnes` activa

## Execution

### Step 1: Verificar montaje SMB
1. Verificar que las carpetas existen y son accesibles:
   ```bash
   ls /mnt/gastosia/ruben/pendientes /mnt/gastosia/esme/pendientes
   ```
2. Si no estan montadas, guiar al usuario para montarlas (ver `examples/smb_mount_reference.sh`)
3. Verificar permisos de lectura/escritura

### Step 2: Crear modulo de utilidades de archivo
1. Crear `app/images/__init__.py` (crear directorio si no existe)
2. Crear `app/images/file_utils.py`:
   - `ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}`
   - `MAX_FILE_SIZE = 15 * 1024 * 1024`  # 15 MB
   - `STABILITY_CHECKS = 3`
   - `SMB_TRANSIENT_ERRORS = (PermissionError,)` + errno EACCES(13), EBUSY(16)
   - `calculate_sha256(filepath) -> str`
   - `is_file_stable(filepath) -> bool` — verifica tamano constante en 3 polls de 5s cada uno
   - `is_allowed_extension(filepath) -> bool`
   - `is_valid_size(filepath) -> bool` — < 15 MB
   - `safe_stat(filepath) -> os.stat_result | None` — captura bloqueos SMB
   - `correct_exif_orientation(image_path) -> Path` — usa Pillow para leer EXIF y rotar
   - `create_inference_copy(image_path) -> Path` — redimensiona si > 4096px, convierte a RGB si es RGBA

### Step 3: Crear el monitor de carpetas
1. Crear `app/images/folder_monitor.py`:
   - Clase `FolderMonitor`:
     - `__init__(watch_paths: list[str], owner: str, db_session_factory)`
     - `known_files: set[str]` — archivos ya procesados en esta sesion
     - `pending_files: dict[str, list[int]]` — {filepath: [size1, size2, size3]}
   - Metodo `async scan()`:
     1. Listar archivos en `watch_paths`
     2. Filtrar por extension valida
     3. Filtrar por tamano <= 15 MB
     4. Para cada archivo nuevo:
        - Intentar `safe_stat`
        - Si PermissionError/OSError(EACCES/EBUSY): continuar (bloqueo temporal SMB, reintentar en siguiente scan)
        - Si el archivo ya esta en `pending_files`:
          - Agregar tamano actual a la lista
          - Si la lista tiene >= 3 valores y todos son iguales: archivo estable -> procesar
        - Si es nuevo: agregar a `pending_files` con el tamano actual
     5. Para archivos estables detectados:
        - Llamar a `process_new_file(filepath, owner)`
        - Agregar a `known_files`
        - Eliminar de `pending_files`
   - Metodo `async process_new_file(filepath, owner)`:
     1. Verificar que el archivo aun existe
     2. Calcular SHA-256
     3. Verificar duplicado exacto: `SELECT FROM image_files WHERE sha256_hash = ?`
        - Si duplicado: mover a `errores/duplicados/`, registrar audit_event, NO crear expense_record, retornar
     4. Corregir orientacion EXIF
     5. Crear copia optimizada para inferencia
     6. Crear `expense_records` con estado `DETECTADO`, `image_hash`, `source_filename`, `owner_id`
     7. Crear `image_files` con `original_path`, `optimized_path`, `sha256_hash`, `file_size`, `mime_type`, `width`, `height`, `exif_json`, `owner_folder`
     8. Insertar en `processing_queue` con estado `EN_COLA`
     9. Mantener archivo original en `pendientes/` (NO mover aun — se mueve tras envio a Sheets)
   - Metodo `async run()`:
     ```python
     while True:
         await self.scan()
         await asyncio.sleep(5)
     ```

### Step 4: Manejo de bloqueos SMB
El codigo DEBE manejar explicitamente (PRD §8.2):

```python
import errno

def is_smb_transient_error(error: OSError) -> bool:
    """Determina si un error de OS es un bloqueo temporal SMB."""
    return error.errno in (errno.EACCES, errno.EBUSY)

# Uso:
try:
    stat = os.stat(filepath)
except PermissionError:
    # Bloqueo temporal: ignorar, reintentar en siguiente ciclo
    return None
except OSError as e:
    if is_smb_transient_error(e):
        return None
    raise
```

UN BLOQUEO TEMPORAL NUNCA DEBE:
- Cambiar el estado a `ERROR_PROCESAMIENTO`
- Mover el archivo a `errores/`
- Generar una alerta o log de error

SOLO DEBE:
- Mantener el archivo en estado `ESPERANDO_ARCHIVO_ESTABLE`
- Reiniciar el contador de estabilidad
- Reintentar en el siguiente ciclo de 5 segundos

### Step 5: Manejo de EXIF y optimizacion
1. Usar Pillow para:
   - Leer metadatos EXIF (si existen)
   - Corregir orientacion usando `ImageOps.exif_transpose()`
   - Guardar imagen corregida
2. Crear copia optimizada:
   - Si ancho o alto > 4096px, redimensionar proporcionalmente a max 2048px en el lado mayor
   - Convertir RGBA/P a RGB
   - Guardar como JPEG con quality=85
   - La copia optimizada es la que se envia a Ollama

### Step 6: Crear servicio de monitoreo
1. Crear `scripts/run_monitor.py` que:
   - Inicialice `FolderMonitor` con ambas carpetas (Ruben y Esme)
   - Ejecute `monitor.run()` como tarea asincrona
2. En `app/main.py`, iniciar el monitor en el evento `startup` de FastAPI:
   ```python
   @app.on_event("startup")
   async def start_monitor():
       asyncio.create_task(monitor.run())
   ```

### Step 7: Generar evidencia
1. Crear `scripts/validation/test_folder_monitor.py` que:
   - Simule llegada de archivo a carpeta de prueba
   - Verifique deteccion en < 15s
   - Simule archivo parcialmente escrito (cambiando de tamano)
   - Verifique estabilidad: archivo no se procesa hasta 3 verificaciones estables
   - Simule bloqueo SMB (archivo sin permisos de lectura)
   - Verifique que el bloqueo NO mueve el archivo a errores
   - Verifique calculo SHA-256
   - Verifique deteccion de duplicado exacto
2. Ejecutar y generar evidencia

## Artifacts
- `app/images/__init__.py`
- `app/images/file_utils.py`
- `app/images/folder_monitor.py`
- `scripts/run_monitor.py`
- `scripts/validation/test_folder_monitor.py`
- `harness/evidence/fase1/monitor-carpetas.json`
- `harness/evidence/fase1/monitor-carpetas.md`

## Quality Criteria
- Sondeo cada 5 segundos (medir con timestamps)
- Archivo inestable NO se procesa hasta 3 verificaciones de tamano identico
- Bloqueo SMB temporal se captura y se reintenta; NO genera error ni mueve el archivo
- SHA-256 se calcula correctamente (verificar con `sha256sum` del sistema)
- Duplicados exactos se detectan y mueven a `errores/duplicados/`
- Archivos > 15 MB se ignoran con warning
- Extensiones no permitidas se ignoran silenciosamente
- EXIF se corrige (imagen rotada sale derecha)
- Copia optimizada existe y es mas pequena que el original (si era > 2048px)
- El monitor no bloquea el event loop de FastAPI (es tarea asincrona independiente)

## Edge Cases
- **Archivo con mismo nombre pero distinto contenido:** SHA-256 diferente -> se procesa como nuevo
- **Archivo con mismo contenido pero distinto nombre:** SHA-256 igual -> duplicado exacto, se rechaza
- **Carpeta no accesible (SMB caido):** loguear warning, reintentar en siguiente ciclo
- **Archivo desaparece durante el procesamiento:** manejar FileNotFoundError, continuar
- **Imagen corrupta (Pillow no puede abrir):** mover a `errores/procesamiento/`, registrar error
- **Imagen sin EXIF:** no fallar, simplemente no corregir orientacion
- **Copia optimizada ya existe:** sobrescribir (idempotencia)
- **Archivos con nombres unicode:** soportar UTF-8 en paths

## References
- PRD §8 (Carpetas y estructura)
- PRD §8.2 (Monitoreo y bloqueos SMB)
- PRD §9.1 (Ingreso y analisis)
- PRD §15 (Duplicados)
- PRD §31.3 (Compatibilidad de formatos)
- Related skills: `skill-database`, `skill-fifo-queue`, `skill-image-extraction`
