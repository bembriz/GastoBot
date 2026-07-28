# Evidence Report — skill-fase3-sheets

> **Skill:** `skill-fase3-sheets`
> **Fase:** `fase3`
> **Timestamp:** `{iso8601}`
> **Estado:** `[PASADO | FALLADO | PARCIAL]`
> **Duración:** `{duration}`

---

## Resumen Ejecutivo

Informe de orquestación de Fase 3 — Google Sheets. Se coordinó la ejecución de `skill-google-sheets` para integrar el envío de gastos a Google Sheets, sincronización de catálogos, pestañas mensuales, control de consecutivos y manejo de operación sin Internet. {summary}.

---

## Métricas

| Métrica | Valor |
|---|---|
| Skills ejecutados | 1 |
| Skills completados | {N} |
| Duración total (min) | {N} |
| Registros enviados a Sheets | {N} |
| Registros actualizados en Sheets | {N} |
| Pestañas mensuales creadas | {N} |
| Tests unitarios totales | {N} |
| Tests unitarios pasados | {N}/{N} |
| Cobertura de código | {N}% |
| Errores | {N} |
| Advertencias | {N} |

### Desglose por Skill

| Skill | Estado | Duración | Tests | Cobertura |
|---|---|---|---|---|
| skill-google-sheets | {status} | {duration} | {N}/{N} | {N}% |

---

## Verificaciones

### Pre-ejecución

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C1 | Fase 2 completada | {status} | {detail} |
| C2 | Artefactos Fase 2 presentes | {status} | {detail} |
| C3 | Google credentials configuradas | {status} | {detail} |
| C4 | Google Sheets API accesible | {status} | {detail} |
| C5 | Spreadsheet ID válido | {status} | {detail} |
| C6 | Catálogos poblados en PostgreSQL | {status} | {detail} |
| C7 | Registros listos para envío | {status} | {detail} |

### Ejecución

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C1 | skill-google-sheets completado | {status} | {detail} |
| C2 | Autenticación Google API funcional | {status} | {detail} |
| C3 | Sincronización _Categorias → PostgreSQL | {status} | {detail} |
| C4 | Sincronización _Cuentas → PostgreSQL | {status} | {detail} |
| C5 | Pestaña mensual creada con 16 headers | {status} | {detail} |
| C6 | Pestaña mensual reutilizada si ya existe | {status} | {detail} |
| C7 | _Control sheet con campos mínimos | {status} | {detail} |
| C8 | Consecutivos asignados por grupo | {status} | {detail} |
| C9 | Inserción de nuevo registro | {status} | {detail} |
| C10 | Actualización de registro existente | {status} | {detail} |
| C11 | Cambio de mes: mover entre pestañas | {status} | {detail} |
| C12 | Eliminación de fila anterior al mover mes | {status} | {detail} |
| C13 | Offline: estado PENDIENTE_DE_ENVIO | {status} | {detail} |
| C14 | Reintento de envío cuando vuelve internet | {status} | {detail} |
| C15 | Conciliación con _Control | {status} | {detail} |
| C16 | Rate limiting manejado | {status} | {detail} |
| C17 | Imagen movida a procesados tras envío | {status} | {detail} |

### Post-ejecución

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C1 | Quality gate: lint | {status} | {detail} |
| C2 | Quality gate: tipos (mypy) | {status} | {detail} |
| C3 | Quality gate: tests unitarios >= 90% | {status} | {detail} |
| C4 | Quality gate: tests integración | {status} | {detail} |
| C5 | Quality gate: tests E2E | {status} | {detail} |
| C6 | Quality gate: pip-audit | {status} | {detail} |
| C7 | Quality gate: gitleaks | {status} | {detail} |
| C8 | 4 archivos de evidencia en fase3/ | {status} | {detail} |
| C9 | AGENTS.md actualizado a completed | {status} | {detail} |
| C10 | PROGRESS.md actualizado | {status} | {detail} |

---

## Artefactos Generados

| Archivo | Tipo | Descripción |
|---|---|---|
| `harness/evidence/fase3/integracion-sheets.json` | report | Evidencia machine-readable de skill-google-sheets |
| `harness/evidence/fase3/integracion-sheets.md` | report | Evidencia human-readable de skill-google-sheets |
| `harness/evidence/fase3/fase3-summary.json` | report | Resumen de fase machine-readable |
| `harness/evidence/fase3/fase3-summary.md` | report | Resumen de fase human-readable |

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

1. Obtener autorización explícita para avanzar a Fase 4
2. Invocar `skill-fase4-instalador` para infraestructura e instalador
3. Preparar script PowerShell de instalación automatizada

---

## Precondiciones al Inicio

```json
{
  "fase2_status": "completed",
  "branch": "arnes",
  "google_credentials_configured": true,
  "google_sheets_api_accessible": true,
  "spreadsheet_id_valid": true,
  "catalogs_populated": true,
  "records_ready_for_send": true
}
```

---

*Reporte generado automáticamente por el arnés Gastos IA v1.0*
