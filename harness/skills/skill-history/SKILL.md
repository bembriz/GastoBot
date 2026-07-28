# Skill: skill-history

## Identity
Act as a **Full-Stack Developer** specialized in data-rich interfaces with FastAPI + HTMX. You build the searchable expense history with filters, pagination, inline editing, Google Sheets reconciliation, and audit trail display.

## Context
This skill implements PRD Section 10.4 (Historial), Section 14 (Actualización de registros), and parts of Section 9.4 (Envío). The history provides a complete record of all expenses that have been processed, reviewed, and sent (or are pending send). Users can search and filter the history, edit records, and trigger sheet updates.

**PRD references:**
- Section 10.4 (Historial) — filters, sheet location, editing, pagination
- Section 14 (Actualización de registros) — same-month update, month change, reconciliation
- Section 14.1 (Mismo mes) — update row in same sheet
- Section 14.2 (Cambio de mes) — move to new month tab
- Section 14.3 (Fila alterada manualmente) — reconciliation via description and _Control
- Section 13 (Google Sheets) — sheet location display
- Section 4 (Usuarios y permisos) — role-based filtering

## Preconditions
- `skill-web-ui` completed: base templates, navigation, role-based access
- `skill-catalogs` completed: categories and accounts for dropdowns
- `skill-database` completed: expense_records and audit_events tables
- `skill-folder-monitor` completed: image file metadata
- `skill-image-extraction` completed: extraction data in records
- At least some test records exist in the database (seed data or real processed records)
- `uv sync --frozen` passes

## Execution

### Step 1: Create History Repository
1. Create `app/history/repository.py` with `HistoryRepository` class:
   - `search_expenses(filters, pagination) -> tuple[list[ExpenseRecord], int]`
     - Filters: user/owner, date_from, date_to, bank, group_code, status, search_text
     - Supports all filter combinations (empty = no filter applied)
     - Role-based filtering: if current_user.role != 'admin', force owner = current_user.username
     - Returns tuple of (records, total_count) for pagination
     - Default sort: expense_date DESC, then created_at DESC
   - `get_audit_trail(record_id) -> list[AuditEvent]`
     - Returns all audit events for a record, ordered by created_at ASC
     - Each event: timestamp, user, action (CREATED, UPDATED, SENT, RECONCILED, etc.), field_changes (JSON diff)
   - `reconcile_record(record_id) -> ReconciliationResult`
     - Compares local data with Google Sheets `_Control` sheet
     - Detects manual changes in Sheets
     - Returns: match_status (MATCH, MISMATCH, NOT_FOUND), differences (list of field diffs)
2. Create pagination helper:
   - Page size: 25 records per page
   - HTMX infinite scroll or paginated table with Previous/Next
   - Page query parameter: `?page=1&per_page=25`

### Step 2: Create History Routes
1. Create `app/api/history.py` with APIRouter:

   **List/Filter routes:**
   - `GET /history` — main history page with filters and table
   - `GET /history/list` — HTML partial with filtered + paginated results (HTMX target)
   - `GET /history/filters` — HTML partial with filter input bar (user, dates, bank, group, status)
   - Filter form uses `hx-get="/history/list"` with query parameters

   **Detail/Edit routes:**
   - `GET /history/{record_id}` — individual history record detail page
   - `GET /history/{record_id}/edit` — HTML partial with edit form (same fields as expense viewer form)
   - `POST /history/{record_id}/update` — save edits (validates required fields)
   - `POST /history/{record_id}/reconcile` — trigger reconciliation with Google Sheets
   - `POST /history/{record_id}/resend` — re-send to Google Sheets (manual trigger)

   **Audit routes:**
   - `GET /history/{record_id}/audit` — HTML partial with audit trail for that record

   **Sheet location routes:**
   - `GET /history/{record_id}/sheet-location` — returns sheet name and row number display

### Step 3: Create History Templates
1. `templates/history.html` — main history page extending base.html:
   - Filter bar at top: Usuario (admin only), Fecha desde/hasta, Banco, Grupo, Estado, search text
   - "Buscar" button and "Limpiar filtros" button
   - Filter bar submits via HTMX `hx-get="/history/list" hx-trigger="submit"`
   - Results area with table and pagination
   - HTMX indicator during load

2. `templates/partials/history/filters.html`:
   - Compact filter bar layout
   - Date picker inputs for date_from and date_to
   - Bank input (text with autocomplete from existing values)
   - Group input (text)
   - Status dropdown (multiselect or single select with all statuses)
   - User dropdown (admin only, shows both users)
   - Search text input (searches description, filename, group)
   - Submit and clear buttons

3. `templates/partials/history/table.html`:
   - Table columns: Fecha, Grupo, Descripción, Monto, Banco, Estado, Usuario(admin), Sheet, Acciones
   - Each row has action buttons: Ver, Editar
   - Sheet column shows "Agosto-26 #42" format (pestaña + row)
   - Status badge with CSS class
   - Click on row navigates to detail view (or use explicit Ver button)
   - Paginated: shows "Mostrando 1-25 de 150 resultados" at top
   - Previous/Next pagination links using `hx-get="/history/list?page={n}"`

4. `templates/history-detail.html`:
   - Full expense record display with image thumbnail
   - All fields displayed (read-only view)
   - Sheet location: "Pestaña: Agosto-26, Fila: 42"
   - Audit trail section showing history of changes
   - Action buttons: Editar, Reconciliar, Reenviar a Sheets
   - Link back to history list

5. `templates/partials/history/edit-form.html`:
   - Same form fields as expense review form (PRD Section 11)
   - Editable fields: transaction_date, group_code, ticket_description, category, account, unit_price, total, bank, transaction_type
   - Hidden fields: updated_at (for optimistic locking)
   - Read-only display: description_final (computed), empleado, pagado_por, cantidad
   - Description final preview updates via HTMX when group or description changes
   - Warning if editing will cause month change: "La fecha ingresada ({new_month}) es diferente a la pestaña actual ({current_month}). El registro se moverá de pestaña al guardar."
   - Action buttons: Guardar Cambios, Cancelar

6. `templates/partials/history/audit.html`:
   - Timeline-style list of audit events
   - Each event: timestamp, user who made change, action description
   - Field changes shown as "Campo: valor_anterior → valor_nuevo"
   - Color coding: green for additions, red for deletions, blue for modifications

### Step 4: Implement Month Change Logic
1. When editing a record's transaction_date:
   - Before saving, compute the expected sheet name from the new date: `"{month_name}-{YY}"` (e.g., "Agosto-26")
   - Compare with the current sheet_name stored in the record
   - If same month: update the row in the existing sheet tab
   - If different month:
     - Show confirmation dialog: "La nueva fecha corresponde a {new_month}. El registro se moverá de {old_month} a {new_month}. ¿Continuar?"
     - On confirmation: insert the record in the new month tab, delete from the old tab, update _Control, update audit
     - If Google Sheets is offline, save locally with status `PENDIENTE_DE_ENVIO` and flag for month-change action

2. Month name generation:
   - Spanish month names: Enero, Febrero, Marzo, Abril, Mayo, Junio, Julio, Agosto, Septiembre, Octubre, Noviembre, Diciembre
   - Two-digit year: datetime.strptime(date).strftime("%y")
   - Format: "{Mes}-{AA}"

### Step 5: Implement Reconciliation
1. `POST /history/{record_id}/reconcile`:
   - Reads the record from PostgreSQL
   - Queries Google Sheets `_Control` sheet for matching `record_id`
   - If found: compares 16 column values with PostgreSQL data
   - If not found in _Control: attempts to find by `final_description` in `_Control`
   - If still not found: marks as "No encontrado en Sheets"
   - Results displayed inline: green checkmark for matches, red X for mismatches with specific field differences
   - Option to "Sincronizar" — overwrites one side with the other (user chooses direction)

2. Conflict resolution UI:
   - Side-by-side comparison: Local (PostgreSQL) vs Sheets
   - Individual field differences highlighted
   - Radio buttons or dropdown per field: "Usar local" or "Usar Sheets"
   - "Aplicar Cambios" button that updates the chosen side

### Step 6: Implement Resend Functionality
1. `POST /history/{record_id}/resend`:
   - Re-executes the send flow (PRD Section 9.4):
     1. Verify internet connectivity
     2. Sync catalogs from _Categorias and _Cuentas
     3. Check _Control for existing entry
     4. Re-validate duplicates
     5. Recalculate consecutive number
     6. Determine sheet tab from transaction_date
     7. Create tab if not exists
     8. Insert/update row
     9. Update _Control
     10. Log audit event
   - Returns success/failure with details
   - If send fails, record stays in current state with error message displayed

### Step 7: Implement Pagination
1. Server-side pagination:
   - `GET /history/list?page=1&per_page=25&filters...`
   - Response includes pagination metadata: total_count, page, per_page, total_pages
   - Template renders pagination controls
2. HTMX-driven navigation:
   - Previous/Next links use `hx-get="/history/list?page={n}" hx-target="#history-results"`
   - Page number links for direct navigation
   - Optionally: infinite scroll using HTMX intersection observer or `hx-trigger="revealed"` on sentinel element

### Step 8: Write Tests
1. Unit tests:
   - `test_history_search_all_filters`
   - `test_history_pagination`
   - `test_history_role_filter_estandar`
   - `test_history_admin_sees_all`
   - `test_month_change_detection`
   - `test_reconcile_match`
   - `test_reconcile_mismatch`
   - `test_reconcile_not_found`
   - `test_resend_flow`
2. Integration tests:
   - Full search → filter → paginate → edit → save flow
   - Month change: edit date → confirm → verify sheet name change
3. E2E tests:
   - History page loads with records
   - Apply filters, verify results
   - Edit record, save, verify update
   - Reconcile record, see differences
   - Resend triggers sheet update

### Step 9: Generate Evidence
1. Create `harness/evidence/fase2/historial.json` per schema.
2. Create `harness/evidence/fase2/historial.md` per schema.

## Artifacts
- `app/history/repository.py` — history repository with search and audit
- `app/api/history.py` — history API routes
- `templates/history.html` — main history page
- `templates/history-detail.html` — record detail page
- `templates/partials/history/filters.html` — filter bar partial
- `templates/partials/history/table.html` — results table partial
- `templates/partials/history/edit-form.html` — edit form partial
- `templates/partials/history/audit.html` — audit trail partial
- `templates/partials/history/pagination.html` — pagination controls
- `tests/unit/test_history.py` — unit tests
- `tests/integration/test_history.py` — integration tests
- `tests/e2e/test_history.py` — E2E tests
- `harness/evidence/fase2/historial.json`
- `harness/evidence/fase2/historial.md`

## Quality Criteria
- Search and filter all available fields (user, date range, bank, group, status, text)
- Role-based: Ruben sees all, Esme sees only own
- Pagination works with 25 records per page
- Sheet location correctly displayed (tab name + row number)
- Edit form validates required fields before save
- Month change detection works correctly
- Reconciliation detects Sheet vs local differences
- Resend triggers full Google Sheets flow
- Audit trail displays complete change history
- All tests pass with >= 90% coverage
- HTMX interactions work without page reloads
- No hardcoded secrets or credentials

## Edge Cases
- **Record edited in Sheets manually:** reconciliation detects discrepancies. Show side-by-side comparison. User chooses which version to keep. Never silently overwrite local or Sheets data.
- **Update across month boundaries:** detect when new transaction_date falls in a different month. Show confirmation dialog with the two month names. On confirm, insert in new tab and delete from old tab. Update `_Control` atomically.
- **Very large history (1000+ records):** pagination ensures manageable page sizes. Filters reduce result sets. Use database-level filtering (WHERE clauses), not Python-level filtering. Consider adding database indexes on (owner, expense_date, status, group_code, bank).
- **Deleted/missing history items:** if a record exists in _Control but not locally (or vice versa), reconciliation flags it as "NOT_FOUND". Provide option to re-import or ignore.
- **Concurrent edits from history:** optimistic locking via updated_at timestamp. If another user/admin saves first, reject with "Modificado por otro usuario" message.
- **Resend when offline:** check internet connectivity before resend. If offline, display "Sin conexión a Internet. Intente de nuevo más tarde." Do not change record state.
- **Empty history:** show "No se encontraron gastos" with a link to go to pending expenses.
- **Filter combination with zero results:** show "No hay resultados con los filtros seleccionados" with a "Limpiar filtros" link.

## References
- PRD Sections 10.4, 14, 14.1, 14.2, 14.3
- PRD Section 9.4 (Envío flow)
- PRD Section 13 (Google Sheets structure)
- PRD Section 4 (Usuarios y permisos)
- Related skills: `skill-web-ui`, `skill-catalogs`, `skill-google-sheets`
- Under `AGENTS.md` Fase 2 — skill-history
