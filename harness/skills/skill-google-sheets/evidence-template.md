# Evidence Report — skill-google-sheets

> **Skill:** `skill-google-sheets`
> **Fase:** `fase3`
> **Timestamp:** `{iso8601}`
> **Estado:** `[PASADO | FALLADO | PARCIAL]`
> **Duración:** `{duration}`

---

## Resumen Ejecutivo

Implementación completa de la integración con Google Sheets: cliente API, sincronización de catálogos (_Categorias, _Cuentas), gestión de pestañas mensuales con 16 columnas, control de consecutivos, hoja _Control, flujo de envío (11 pasos), actualizaciones (mismo mes y cambio de mes), modo offline con cola PENDIENTE_DE_ENVIO, y conciliación bidireccional. {summary}.

---

## Métricas

| Métrica | Valor |
|---|---|
| Módulos Python creados | {N} (client, sync, tabs, control, consecutive, sender, reconciler) |
| Pestañas técnicas creadas | 3 (_Categorias, _Cuentas, _Control) |
| Columnas por pestaña mensual | 16 |
| Pasos del flujo de envío | 11 (PRD 9.4) |
| Registros enviados exitosamente | {N} |
| Registros actualizados en Sheets | {N} |
| Cambios de mes procesados | {N} |
| Registros en cola offline | {N} |
| Tests unitarios | {N}/{N} |
| Tests de integración | {N}/{N} |
| Tests E2E | {N}/{N} |
| Cobertura de código | {N}% |
| Errores | {N} |
| Advertencias | {N} |

---

## Verificaciones

### Pre-ejecución

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C1 | GASTOSIA_GOOGLE_CREDENTIALS_PATH configurado | {status} | {detail} |
| C2 | Archivo de credenciales existe | {status} | {detail} |
| C3 | GASTOSIA_GOOGLE_SPREADSHEET_ID configurado | {status} | {detail} |
| C4 | Servicio Google Sheets API habilitado | {status} | {detail} |
| C5 | Dependencias python instaladas | {status} | {detail} |
| C6 | Catálogos PostgreSQL poblados | {status} | {detail} |

### Ejecución

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C1 | GoogleSheetsClient autentica correctamente | {status} | {detail} |
| C2 | verify_connectivity() funciona | {status} | {detail} |
| C3 | get_or_create_sheet() — existente | {status} | {detail} |
| C4 | get_or_create_sheet() — nueva | {status} | {detail} |
| C5 | Rate limiting con exponential backoff | {status} | {detail} |
| C6 | Errores personalizados (SheetsError, etc.) | {status} | {detail} |
| C7 | sync_categories_from_sheets() funcional | {status} | {detail} |
| C8 | sync_accounts_from_sheets() funcional | {status} | {detail} |
| C9 | _Categorias y _Cuentas creadas si no existen | {status} | {detail} |
| C10 | get_month_tab_name() nombres en español | {status} | {detail} |
| C11 | ensure_month_tab() con 16 headers | {status} | {detail} |
| C12 | 16 headers en orden PRD 13.1 | {status} | {detail} |
| C13 | find_next_empty_row() correcto | {status} | {detail} |
| C14 | _Control sheet con 15 columnas | {status} | {detail} |
| C15 | add_control_entry() append row | {status} | {detail} |
| C16 | update_control_entry() busca por record_id | {status} | {detail} |
| C17 | delete_control_entry() elimina fila | {status} | {detail} |
| C18 | get_max_consecutive() _Control + PostgreSQL | {status} | {detail} |
| C19 | find_by_hash() detecta duplicados | {status} | {detail} |
| C20 | ConsecutiveManager.assign_next() con advisory lock | {status} | {detail} |
| C21 | Sin registros previos → consecutivo = 1 | {status} | {detail} |
| C22 | validate_assignment() re-verifica | {status} | {detail} |
| C23 | Send flow paso 1: verificar internet | {status} | {detail} |
| C24 | Send flow paso 2: sincronizar catálogos | {status} | {detail} |
| C25 | Send flow paso 3: consultar _Control | {status} | {detail} |
| C26 | Send flow paso 4: revalidar duplicados | {status} | {detail} |
| C27 | Send flow paso 5: recalcular consecutivo | {status} | {detail} |
| C28 | Send flow paso 6: determinar pestaña | {status} | {detail} |
| C29 | Send flow paso 7: crear pestaña si necesario | {status} | {detail} |
| C30 | Send flow paso 8: construir 16 columnas | {status} | {detail} |
| C31 | Send flow paso 9: insertar fila | {status} | {detail} |
| C32 | Send flow paso 10: actualizar _Control | {status} | {detail} |
| C33 | Send flow paso 11: registrar auditoría | {status} | {detail} |
| C34 | Estado ENVIANDO → ENVIADO en éxito | {status} | {detail} |
| C35 | Imagen movida a procesados/YYYY/MM | {status} | {detail} |
| C36 | Update: mismo mes sobrescribe fila | {status} | {detail} |
| C37 | Update: cambio de mes (insert + delete) | {status} | {detail} |
| C38 | Update: fila alterada manualmente (14.3) | {status} | {detail} |
| C39 | Offline: estado PENDIENTE_DE_ENVIO | {status} | {detail} |
| C40 | retry_pending_sends() procesa cola | {status} | {detail} |
| C41 | reconcile_record() match | {status} | {detail} |
| C42 | reconcile_record() mismatch | {status} | {detail} |
| C43 | reconcile_record() not_found | {status} | {detail} |
| C44 | resolve_using_local() y resolve_using_sheets() | {status} | {detail} |
| C45 | Tests unitarios >= 90% | {status} | {detail} |
| C46 | Tests de integración pasan | {status} | {detail} |
| C47 | Tests E2E pasan | {status} | {detail} |

### Post-ejecución

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C1 | Credenciales nunca en código/logs/Git | {status} | {detail} |
| C2 | 16 columnas coinciden con PRD 13.1 | {status} | {detail} |
| C3 | Consecutivos sin colisiones | {status} | {detail} |
| C4 | Movimiento entre meses sin pérdida | {status} | {detail} |
| C5 | Offline → online recupera registros | {status} | {detail} |
| C6 | Lint/mypy/ruff pasan | {status} | {detail} |

---

## Artefactos Generados

| Archivo | Tipo | Descripción |
|---|---|---|
| `app/sheets/__init__.py` | source | Módulo sheets |
| `app/sheets/client.py` | source | Cliente Google Sheets API |
| `app/sheets/sync.py` | source | Sincronización de catálogos |
| `app/sheets/tabs.py` | source | Gestión de pestañas mensuales |
| `app/sheets/control.py` | source | Hoja _Control |
| `app/sheets/consecutive.py` | source | Asignación de consecutivos |
| `app/sheets/sender.py` | source | Flujo de envío (11 pasos) |
| `app/sheets/reconciler.py` | source | Conciliación y actualizaciones |
| `app/sheets/errors.py` | source | Excepciones personalizadas |
| `tests/unit/test_sheets.py` | test | Tests unitarios |
| `tests/integration/test_sheets.py` | test | Tests de integración |
| `tests/e2e/test_sheets.py` | test | Tests E2E |

---

## Errores (si los hay)

| Código | Mensaje |
|---|---|
| {code} | {message} |

---

## Advertencias (si las hay)

- {warning}

---

## Próximos Pasos

1. Proceder a Fase 4: instalador automatizado
2. Validar credenciales de Google en entorno de producción
3. Verificar rate limiting con volumen real de envíos

---

## Precondiciones al Inicio

```json
{
  "fase2_status": "completed",
  "google_credentials_path_set": true,
  "google_credentials_file_exists": true,
  "google_spreadsheet_id_set": true,
  "google_sheets_api_enabled": true,
  "dependencies_installed": true,
  "catalogs_populated": true,
  "records_ready": true
}
```

---

*Reporte generado automáticamente por el arnés Gastos IA v1.0*
