# Checklist — skill-folder-monitor

## Pre-ejecucion
- [ ] `skill-database` completado (tablas `image_files`, `expense_records`, `processing_queue`)
- [ ] Carpetas SMB montadas y accesibles en `/mnt/gastosia/`
- [ ] `uv add Pillow aiofiles` ejecutado
- [ ] Rama `arnes` activa

## Ejecucion — Utilidades de archivo
- [ ] `app/images/file_utils.py` creado
- [ ] `ALLOWED_EXTENSIONS` definido (.jpg, .jpeg, .png, .webp)
- [ ] `MAX_FILE_SIZE = 15 * 1024 * 1024`
- [ ] `STABILITY_CHECKS = 3`
- [ ] `calculate_sha256()` funcional y coincide con `sha256sum`
- [ ] `is_file_stable()` verifica 3 tamano iguales en 3 polls
- [ ] `is_allowed_extension()` filtra correctamente
- [ ] `is_valid_size()` rechaza > 15 MB
- [ ] `safe_stat()` captura PermissionError y OSError EACCES/EBUSY
- [ ] `correct_exif_orientation()` usa Pillow ImageOps.exif_transpose
- [ ] `create_inference_copy()` redimensiona > 4096px, convierte RGBA->RGB

## Ejecucion — Monitor
- [ ] `app/images/folder_monitor.py` creado
- [ ] Clase `FolderMonitor` con `scan()` y `process_new_file()`
- [ ] `scan()` lista archivos cada 5 segundos
- [ ] `scan()` filtra por extension y tamano
- [ ] `scan()` maneja bloqueos SMB sin mover a errores
- [ ] `scan()` rastrea estabilidad con `pending_files` dict
- [ ] `process_new_file()` calcula SHA-256
- [ ] `process_new_file()` verifica duplicados en BD
- [ ] `process_new_file()` corrige EXIF y crea copia optimizada
- [ ] `process_new_file()` crea expense_record, image_files, processing_queue entry
- [ ] `process_new_file()` NO mueve el original (se mueve tras envio a Sheets)
- [ ] `run()` es un bucle infinito con `asyncio.sleep(5)`

## Ejecucion — Manejo de bloqueos SMB
- [ ] PermissionError capturado y tratado como reintento
- [ ] OSError con errno EACCES (13) tratado como reintento
- [ ] OSError con errno EBUSY (16) tratado como reintento
- [ ] Bloqueo NO cambia estado a ERROR_PROCESAMIENTO
- [ ] Bloqueo NO mueve archivo a errores/
- [ ] Bloqueo reinicia contador de estabilidad
- [ ] Bloqueo se reintenta en siguiente ciclo de 5s

## Ejecucion — Integracion con FastAPI
- [ ] `scripts/run_monitor.py` creado
- [ ] Monitor inicia como tarea asincrona en startup de FastAPI
- [ ] Monitor no bloquea el event loop

## Ejecucion — Pruebas
- [ ] `scripts/validation/test_folder_monitor.py` ejecutado
- [ ] Deteccion de archivo nuevo en < 15s
- [ ] Archivo parcial (tamano cambiante) no se procesa
- [ ] Archivo estable se procesa tras 3 verificaciones
- [ ] Bloqueo SMB no mueve archivo a errores
- [ ] SHA-256 correcto
- [ ] Duplicado exacto detectado y movido a errores/duplicados/
- [ ] Imagen > 15 MB ignorada
- [ ] Extension no permitida ignorada
- [ ] EXIF corregido (imagen rotada -> derecha)
- [ ] Copia optimizada generada

## Post-ejecucion
- [ ] Evidencia `monitor-carpetas.json` generada
- [ ] Evidencia `monitor-carpetas.md` generada
- [ ] `skill-quality-gate` ejecutado
- [ ] `harness/PROGRESS.md` actualizado
