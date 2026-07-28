# Checklist — skill-history

## Pre-ejecución
- [ ] skill-web-ui completado (base templates, nav, roles)
- [ ] skill-catalogs completado (dropdowns para categorías y cuentas)
- [ ] skill-database completado (modelos expense_records, audit_events)
- [ ] skill-folder-monitor completado (metadata de archivos)
- [ ] skill-image-extraction completado (datos de extracción)
- [ ] Al menos algunos registros de prueba en la base de datos
- [ ] `uv sync --frozen` exitoso
- [ ] Branch `arnes` activa

## Ejecución
- [ ] Paso 1: app/history/repository.py con search_expenses, get_audit_trail, reconcile_record
- [ ] Paso 1: Filtros: user(admin), date_from, date_to, bank, group_code, status, search_text
- [ ] Paso 1: Paginación: 25 registros por página, total_count
- [ ] Paso 2: app/api/history.py con rutas de historial
- [ ] Paso 2: GET /history (página principal)
- [ ] Paso 2: GET /history/list (resultados filtrados + paginados)
- [ ] Paso 2: GET /history/{id} (detalle de registro)
- [ ] Paso 2: GET /history/{id}/edit (formulario de edición)
- [ ] Paso 2: POST /history/{id}/update (guardar cambios)
- [ ] Paso 2: POST /history/{id}/reconcile (conciliar con Sheets)
- [ ] Paso 2: POST /history/{id}/resend (reenviar a Sheets)
- [ ] Paso 2: GET /history/{id}/audit (auditoría)
- [ ] Paso 2: GET /history/{id}/sheet-location (ubicación en Sheets)
- [ ] Paso 3: templates/history.html con filtros y tabla
- [ ] Paso 3: templates/partials/history/filters.html
- [ ] Paso 3: templates/partials/history/table.html con paginación
- [ ] Paso 3: templates/history-detail.html con auditoría
- [ ] Paso 3: templates/partials/history/edit-form.html
- [ ] Paso 3: templates/partials/history/audit.html (timeline)
- [ ] Paso 4: Detección de cambio de mes al editar fecha
- [ ] Paso 4: Confirmación de cambio de mes
- [ ] Paso 4: Mover registro entre pestañas al cambiar mes
- [ ] Paso 5: Conciliación local vs Sheets (_Control)
- [ ] Paso 5: UI de comparación lado a lado
- [ ] Paso 5: Resolución de conflictos (usar local / usar Sheets)
- [ ] Paso 6: Funcionalidad de reenvío a Google Sheets
- [ ] Paso 6: Verificación de conectividad antes de reenviar
- [ ] Paso 7: Paginación con controles Previous/Next
- [ ] Paso 7: Carga de páginas vía HTMX sin recarga completa
- [ ] Paso 8: Tests unitarios pasan (>= 90% cobertura)
- [ ] Paso 8: Tests de integración pasan
- [ ] Paso 8: Tests E2E pasan
- [ ] Paso 9: Evidencia JSON generada
- [ ] Paso 9: Evidencia MD generada

## Post-ejecución
- [ ] Búsqueda y filtros funcionales
- [ ] Esme solo ve sus propios registros
- [ ] Ruben ve todos los registros
- [ ] Paginación funcional (25 por página)
- [ ] Ubicación en Sheets visible ("Agosto-26 #42")
- [ ] Edición inline con validación de campos
- [ ] Cambio de mes detectado y confirmado
- [ ] Conciliación detecta diferencias
- [ ] Reenvío ejecuta flujo completo de Sheets
- [ ] Auditoría muestra historial de cambios
- [ ] HTMX: todas las interacciones sin recarga
- [ ] Cobertura >= 90%
- [ ] Sin secretos en código
- [ ] Lint, mypy, ruff pasan
