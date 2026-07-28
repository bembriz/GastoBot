# Evidence Report — skill-folder-monitor

> **Skill:** `skill-folder-monitor`
> **Fase:** `fase1`
> **Timestamp:** `{iso8601}`
> **Estado:** `[PASADO | FALLADO | PARCIAL]`
> **Duracion:** `{duration}`

---

## Resumen Ejecutivo

{Summary: folder monitor implemented with 5s polling, stability validation, SHA-256, EXIF correction, SMB transient lock handling.}

---

## Metricas

| Metrica | Valor |
|---|---|
| Total de verificaciones | {N} |
| Pasadas | {N} |
| Fallidas | {N} |
| Carpetas monitoreadas | 2 (Ruben/pendientes, Esme/pendientes) |
| Intervalo sondeo | 5 segundos |
| Verificaciones estabilidad | 3 |
| Extensiones permitidas | .jpg, .jpeg, .png, .webp |
| Tamano maximo | 15 MB |
| Bloqueos SMB temporales capturados | {N} en pruebas |
| Errores | {N} |
| Advertencias | {N} |

---

## Verificaciones

### Pre-ejecucion

| # | Verificacion | Estado | Detalle |
|---|---|---|---|
| C1 | Carpetas SMB montadas | {status} | /mnt/gastosia/ruben/, /mnt/gastosia/esme/ |
| C2 | Tablas BD existen | {status} | image_files, expense_records, processing_queue |
| C3 | Dependencias instaladas | {status} | Pillow, aiofiles |

### Ejecucion — Utilidades

| # | Verificacion | Estado | Detalle |
|---|---|---|---|
| C1 | `calculate_sha256()` coincide con sistema | {status} | Verificado con sha256sum |
| C2 | `is_file_stable()` detecta cambios | {status} | 3 verificaciones identicas requeridas |
| C3 | `correct_exif_orientation()` funcional | {status} | Imagen rotada corregida |
| C4 | `create_inference_copy()` optimiza | {status} | Redimension y conversion RGB |
| C5 | `safe_stat()` maneja bloqueos | {status} | PermissionError, EACCES, EBUSY |

### Ejecucion — Monitor

| # | Verificacion | Estado | Detalle |
|---|---|---|---|
| C1 | Sondeo cada 5s | {status} | Timestamps verificados |
| C2 | Deteccion nuevo archivo | {status} | < 15s desde copia |
| C3 | Estabilidad validada | {status} | 3 tamano identicos requeridos |
| C4 | Filtro extensiones | {status} | Solo .jpg .jpeg .png .webp |
| C5 | Filtro tamano > 15 MB | {status} | Rechazado con warning |
| C6 | SHA-256 almacenado | {status} | En image_files.sha256_hash |
| C7 | EXIF corregido | {status} | Orientacion normalizada |
| C8 | Copia optimizada creada | {status} | JPEG quality=85, max 2048px |
| C9 | expense_record creado | {status} | Estado inicial: DETECTADO |
| C10 | processing_queue entry creada | {status} | Estado: EN_COLA |
| C11 | Original NO movido | {status} | Permanece en pendientes/ |

### Ejecucion — Bloqueos SMB

| # | Verificacion | Estado | Detalle |
|---|---|---|---|
| C1 | PermissionError -> reintento | {status} | No genera error |
| C2 | EACCES -> reintento | {status} | Contador reiniciado |
| C3 | EBUSY -> reintento | {status} | No mueve archivo |
| C4 | Estado se mantiene ESPERANDO | {status} | No cambia a ERROR |
| C5 | Archivo NO movido a errores/ | {status} | Permanece en pendientes/ |

### Ejecucion — Duplicados

| # | Verificacion | Estado | Detalle |
|---|---|---|---|
| C1 | Duplicado SHA-256 detectado | {status} | Query a image_files |
| C2 | Movido a errores/duplicados/ | {status} | Archivo reubicado |
| C3 | NO crea expense_record | {status} | Sin registro duplicado |

---

## Artefactos Generados

| Archivo | Tipo | Descripcion |
|---|---|---|
| `app/images/file_utils.py` | source | Utilidades de archivo |
| `app/images/folder_monitor.py` | source | Monitor de carpetas |
| `scripts/run_monitor.py` | script | Entry point del monitor |
| `scripts/validation/test_folder_monitor.py` | script | Pruebas del monitor |
| `harness/evidence/fase1/monitor-carpetas.json` | report | Evidencia JSON |
| `harness/evidence/fase1/monitor-carpetas.md` | report | Evidencia Markdown |

---

## Errores (si los hay)

| Codigo | Mensaje |
|---|---|
| `ERR_XXX` | {description} |

---

## Advertencias (si las hay)

- {warning}

---

## Proximos Pasos

1. Proceder con `skill-fifo-queue`
2. Probar con archivos reales en carpetas SMB
3. Monitorear tiempo de deteccion en condiciones reales

---

## Precondiciones al Inicio

```json
{
  "smb_mounted": true,
  "mount_paths": ["/mnt/gastosia/ruben/pendientes", "/mnt/gastosia/esme/pendientes"],
  "database_skill_completed": true,
  "pillow_installed": true
}
```

---

*Reporte generado automaticamente por el arnes Gastos IA v1.0*
