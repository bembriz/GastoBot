# Evidence Report — skill-history

> **Skill:** `skill-history`
> **Fase:** `fase2`
> **Timestamp:** `{iso8601}`
> **Estado:** `[PASADO | FALLADO | PARCIAL]`
> **Duración:** `{duration}`

---

## Resumen Ejecutivo

Implementación del historial de gastos con búsqueda, filtros avanzados, paginación, edición inline, conciliación con Google Sheets, detección de cambios de mes, reenvío manual y visualización de auditoría. {summary}.

---

## Métricas

| Métrica | Valor |
|---|---|
| Rutas API creadas | {N} |
| Templates creados | {N} |
| Partial templates (HTMX) | {N} |
| Filtros disponibles | {N} (user, date, bank, group, status, text) |
| Registros por página | 25 |
| Registros de prueba | {N} |
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
| C1 | skill-web-ui completado | {status} | {detail} |
| C2 | skill-catalogs completado | {status} | {detail} |
| C3 | skill-database completado | {status} | {detail} |
| C4 | Datos de prueba disponibles | {status} | {detail} |

### Ejecución

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C1 | HistoryRepository con search, audit, reconcile | {status} | {detail} |
| C2 | Filtro por usuario (admin) | {status} | {detail} |
| C3 | Filtro por rango de fechas | {status} | {detail} |
| C4 | Filtro por banco | {status} | {detail} |
| C5 | Filtro por grupo | {status} | {detail} |
| C6 | Filtro por estado | {status} | {detail} |
| C7 | Filtro por texto (descripción, archivo, grupo) | {status} | {detail} |
| C8 | Paginación: 25 registros por página | {status} | {detail} |
| C9 | Role filter: Esme solo ve propios | {status} | {detail} |
| C10 | Role filter: Ruben ve todos | {status} | {detail} |
| C11 | Página principal /history | {status} | {detail} |
| C12 | Resultados filtrados vía HTMX | {status} | {detail} |
| C13 | Vista detalle con todos los campos | {status} | {detail} |
| C14 | Ubicación Sheets: pestaña + fila | {status} | {detail} |
| C15 | Formulario de edición desde historial | {status} | {detail} |
| C16 | Guardar cambios con validación | {status} | {detail} |
| C17 | Warning cambio de mes en edición | {status} | {detail} |
| C18 | Confirmación cambio de mes | {status} | {detail} |
| C19 | Mover registro entre pestañas | {status} | {detail} |
| C20 | Conciliación: match | {status} | {detail} |
| C21 | Conciliación: mismatch con diferencias | {status} | {detail} |
| C22 | Conciliación: not found | {status} | {detail} |
| C23 | Resolución de conflictos lado a lado | {status} | {detail} |
| C24 | Reenvío a Google Sheets manual | {status} | {detail} |
| C25 | Verificación internet antes de reenviar | {status} | {detail} |
| C26 | Auditoría: timeline de cambios | {status} | {detail} |
| C27 | Auditoría: field diffs (valor_anterior → valor_nuevo) | {status} | {detail} |
| C28 | Paginación HTMX sin recarga | {status} | {detail} |
| C29 | Empty state: sin resultados | {status} | {detail} |
| C30 | Bloqueo optimista en edición | {status} | {detail} |
| C31 | Tests unitarios >= 90% | {status} | {detail} |
| C32 | Tests integración | {status} | {detail} |
| C33 | Tests E2E | {status} | {detail} |

### Post-ejecución

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C1 | Filtros combinados funcionan | {status} | {detail} |
| C2 | Paginación navega correctamente | {status} | {detail} |
| C3 | Cambio de mes sin pérdida de datos | {status} | {detail} |
| C4 | Conciliación sin sobrescritura silenciosa | {status} | {detail} |
| C5 | Sin secretos | {status} | {detail} |
| C6 | Lint/mypy/ruff pasan | {status} | {detail} |

---

## Artefactos Generados

| Archivo | Tipo | Descripción |
|---|---|---|
| `app/history/repository.py` | source | Repositorio de historial |
| `app/api/history.py` | source | Rutas API de historial |
| `templates/history.html` | template | Página principal de historial |
| `templates/history-detail.html` | template | Detalle de registro |
| `templates/partials/history/filters.html` | template | Barra de filtros |
| `templates/partials/history/table.html` | template | Tabla de resultados |
| `templates/partials/history/edit-form.html` | template | Formulario de edición |
| `templates/partials/history/audit.html` | template | Línea de auditoría |
| `templates/partials/history/pagination.html` | template | Controles de paginación |
| `tests/unit/test_history.py` | test | Tests unitarios |
| `tests/integration/test_history.py` | test | Tests de integración |
| `tests/e2e/test_history.py` | test | Tests E2E |

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

1. Iniciar Fase 3: integración con Google Sheets
2. Verificar flujo completo: dashboard → review → send → history → edit → resend
3. Probar reconciliación con datos reales de Google Sheets

---

## Precondiciones al Inicio

```json
{
  "web_ui_skill": "completed",
  "catalogs_skill": "completed",
  "database_skill": "completed",
  "folder_monitor_skill": "completed",
  "image_extraction_skill": "completed",
  "test_records_exist": true,
  "audit_events_table": "exists"
}
```

---

*Reporte generado automáticamente por el arnés Gastos IA v1.0*
