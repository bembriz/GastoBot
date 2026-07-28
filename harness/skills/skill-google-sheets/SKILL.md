# Skill: skill-google-sheets

## Identity
Act as a **Google Sheets Integration Engineer** specialized in Google Sheets API v4 with Python + FastAPI. You build the complete Google Sheets integration: catalog sync, monthly tab management, _Control sheet operations, consecutive number assignment, row insertion/update/deletion, month boundary moves, offline queuing, and reconciliation.

## Context
This skill implements PRD Section 13 (Google Sheets) — the business destination for all expense records. It connects the local PostgreSQL expense data with a Google Sheets spreadsheet that serves as the canonical financial record.

**Critical constraint:** The Google Sheets credential JSON is NOT stored in the repository. Its path is provided via the `GASTOSIA_GOOGLE_CREDENTIALS_PATH` environment variable. The spreadsheet ID is provided via `GASTOSIA_GOOGLE_SPREADSHEET_ID`.

**PRD references:**
- Section 13 (Google Sheets) — full scope
- Section 13.1 (Columnas mensuales) — 16 column structure
- Section 13.2 (Mapeo) — field-to-column mapping
- Section 13.3 (Pestañas mensuales) — "Mes-AA" naming, creation
- Section 13.4 (Pestañas técnicas) — _Categorias, _Cuentas, _Control
- Section 9.4 (Envío) — 11-step send flow
- Section 9.5 (Operación sin Internet) — offline mode
- Section 12 (Descripción y consecutivo) — consecutive numbering
- Section 14 (Actualización de registros) — update in sheets
- Section 15 (Duplicados) — dedup via _Control

## Preconditions
- Fase 2 completed: web UI, catalogs, history operational
- PostgreSQL with populated catalog data (categories, accounts)
- Expense records ready for sending
- `GASTOSIA_GOOGLE_CREDENTIALS_PATH` env var set and file exists (outside repo)
- `GASTOSIA_GOOGLE_SPREADSHEET_ID` env var set
- Google Sheets API enabled, service account with editor access
- `google-auth`, `google-api-python-client` in pyproject.toml dependencies
- `uv sync --frozen` passes

## Execution

### Step 1: Set Up Google Sheets Client
1. Create `app/sheets/client.py`:
   - `GoogleSheetsClient` class wrapping `googleapiclient.discovery.build("sheets", "v4")`
   - Constructor reads `GASTOSIA_GOOGLE_CREDENTIALS_PATH` and `GASTOSIA_GOOGLE_SPREADSHEET_ID` from env vars
   - Validates both are set and credentials file exists on init
   - Lazy initialization of the service object
   - Methods:
     - `verify_connectivity() -> bool` — tries reading spreadsheet metadata, returns True/False
     - `get_or_create_sheet(sheet_name: str) -> int` — returns sheet ID, creates if missing
     - `read_range(range_name: str) -> list[list]` — read values from a range
     - `write_range(range_name: str, values: list[list])` — write values to a range
     - `append_row(sheet_name: str, values: list)` — append a single row
     - `delete_row(sheet_name: str, row_index: int)` — delete a row (shift up)
     - `batch_update(requests: list[dict])` — execute batch operations
   - All methods wrap Google API calls with try/except for `HttpError`
2. Configure rate limiting:
   - Google Sheets API free tier: 60 requests per minute per user, 300 per minute per project
   - Implement exponential backoff retry with max 3 attempts
   - Handle 429 (rate limit) and 500 (server error) gracefully
3. Create `app/sheets/errors.py`:
   - `SheetsConnectionError` — no internet
   - `SheetsAuthError` — invalid credentials
   - `SheetsNotFoundError` — spreadsheet not found
   - `SheetsRateLimitError` — rate limited
   - `SheetsConflictError` — concurrent modification detected

### Step 2: Implement Catalog Sync
1. Create `app/sheets/sync.py` with `CatalogSync` class:
   - `sync_categories_from_sheets()` — reads `_Categorias` sheet, upserts into PostgreSQL `categories` table
     - Expected columns: A=código, B=descripción, C=activo
     - Skips header row (row 1)
     - Maps to Category model (code, description, active)
     - Inserts new, updates existing by code
   - `sync_accounts_from_sheets()` — reads `_Cuentas` sheet, same pattern
   - `sync_categories_to_sheets()` — pushes PostgreSQL categories to `_Categorias` sheet
     - Writes header (Código, Descripción, Activo) if sheet empty
     - Replaces all data rows
   - `sync_accounts_to_sheets()` — same pattern for `_Cuentas`
   - Sync direction: when sending expense, sync FROM sheets first (sheets are source of truth for catalogs), then use local data

2. Create `_Categorias` sheet if it doesn't exist:
   - Headers: Código | Descripción | Activo
   - Populate from PostgreSQL categories

3. Create `_Cuentas` sheet if it doesn't exist:
   - Headers: Código | Descripción | Activo
   - Populate from PostgreSQL accounts

### Step 3: Implement Monthly Tab Management
1. Create `app/sheets/tabs.py`:
   - `get_month_tab_name(expense_date: date) -> str`:
     - Spanish month names: Enero, Febrero, Marzo, Abril, Mayo, Junio, Julio, Agosto, Septiembre, Octubre, Noviembre, Diciembre
     - Two-digit year: `str(date.year)[-2:]`
     - Format: `"{Mes}-{AA}"` = e.g., "Agosto-26"
   - `ensure_month_tab(sheet_name: str)`:
     - Check if tab/sheet exists in spreadsheet
     - If not, create it with `addSheet` batch update
     - Write 16 column headers in row 1 (PRD Section 13.1):
       ```
       A: Fecha del gasto
       B: Categoría
       C: Descripción
       D: Empleado
       E: Pagado por
       F: Actividades
       G: Fecha contable
       H: Cuenta
       I: Precio unitario
       J: Cantidad
       K: Incluir impuestos
       L: Importe de impuestos
       M: Total
       N: Estado
       O: Banco
       P: Transaccion
       ```
     - Apply bold formatting to header row (optional, nice-to-have)
   - `find_next_empty_row(sheet_name: str) -> int`:
     - Read column A of the sheet, find first empty row after last data row
     - Return 1-indexed row number (row 1 is headers)

### Step 4: Implement _Control Sheet Management
1. Create `app/sheets/control.py`:
   - `ensure_control_sheet()` — creates `_Control` sheet if not exists with headers:
     ```
     record_id, image_hash, owner, group_code, consecutive,
     final_description, expense_date, amount, bank,
     transaction_type, sheet_name, sheet_row, status,
     source_filename, created_at, updated_at
     ```
   - `get_control_entries(group_code: str = None) -> list[dict]` — read control entries
   - `add_control_entry(record_data: dict)` — append a new row to _Control
   - `update_control_entry(record_id: int, updates: dict)` — update existing control row
     - Find row by record_id in column A
     - Update relevant columns
   - `delete_control_entry(record_id: int)` — remove row from _Control (on month move deletion)
   - `get_max_consecutive(group_code: str) -> int`:
     - Query _Control for max consecutive value for given group_code
     - Also query local PostgreSQL for max consecutive (accounts for unsent records)
     - Return max of both + 1 (for the next number)
   - `find_by_hash(image_hash: str) -> dict | None` — check for duplicate by SHA-256
   - `find_by_record_id(record_id: int) -> dict | None` — find control entry by record_id

### Step 5: Implement Consecutive Number Assignment
1. Create `app/sheets/consecutive.py`:
   - `ConsecutiveManager.assign_next(group_code: str) -> int`:
     1. Acquire a PostgreSQL advisory lock for the group_code (prevents concurrent assignments)
        ```python
        await session.execute(select(func.pg_advisory_xact_lock(hash(group_code))))
        ```
     2. Query `_Control` sheet for max consecutive with this group_code
     3. Query local `expense_records` table for max consecutive with this group_code
     4. Take max of both, add 1
     5. If no existing records, start at 1
     6. Return the assigned number
   - `ConsecutiveManager.validate_assignment(group_code: str, consecutive: int) -> bool`:
     - Before writing to Sheets, re-validate no collision occurred
     - Query _Control again, check the number is still available

### Step 6: Implement Send Flow (PRD Section 9.4)
1. Create `app/sheets/sender.py` with `ExpenseSender` class:
   - `async send_expense_to_sheets(record_id: int, current_user: User) -> SendResult`:
     Implements the 11-step send flow:
     1. **Verify internet:** `client.verify_connectivity()`. If offline → set status to `PENDIENTE_DE_ENVIO`, return.
     2. **Sync catalogs:** read `_Categorias` and `_Cuentas` from sheets, update local catalog cache.
     3. **Query _Control:** read `_Control` sheet for existing entries.
     4. **Re-validate duplicates:** check `_Control` for `image_hash`. If duplicate found → set status to `DUPLICADO_EXACTO`, return.
     5. **Recalculate consecutive:** `ConsecutiveManager.assign_next(group_code)`.
     6. **Determine sheet tab:** `get_month_tab_name(expense_date)`, `ensure_month_tab(tab_name)`.
     7. **Find next row:** `find_next_empty_row(tab_name)`.
     8. **Build row data** (16 columns mapped per PRD Section 13.2):
        ```
        A: transaction_date (formatted as DD/MM/YYYY or YYYY-MM-DD)
        B: category.code + " - " + category.description
        C: final_description (Grupo-Consecutivo-Descripción del ticket)
        D: "RUBEN BENJAMIN VAZQUEZ EMBRIZ"
        E: "Empresa"
        F: "" (empty)
        G: "" (empty)
        H: account.code + " - " + account.description
        I: unit_price (as number)
        J: 1
        K: "" (empty)
        L: "" (empty)
        M: total (as number)
        N: "Por reportar"
        O: bank
        P: transaction_type
        ```
     9. **Insert row:** `write_range(f"'{tab_name}'!A{row}:P{row}", [row_data])`.
     10. **Update _Control:** `add_control_entry(record_data)`.
     11. **Log audit event:** record the send in `audit_events` table.

   - Set record status to `ENVIANDO` before the operation
   - On success: set status to `ENVIADO`, move image to `procesados/YYYY/MM`
   - On failure: set status based on error type (ERROR_SHEETS for API errors, PENDIENTE_DE_ENVIO for connectivity)

### Step 7: Implement Update Flow (PRD Section 14)
1. `async update_expense_in_sheets(record_id: int, data: dict, current_user: User) -> UpdateResult`:
   - **Same month update (14.1):**
     - Read record's current `sheet_name` and `sheet_row`
     - Build 16-column row data from updated fields
     - `write_range(f"'{sheet_name}'!A{sheet_row}:P{sheet_row}", [row_data])`
     - `update_control_entry(record_id, updates)`
     - Log audit event
   - **Month change (14.2):**
     - Detect new expense_date belongs to different month tab
     - Insert row in new month tab (steps 6-9 from send flow)
     - Delete old row from previous tab: `delete_row(old_sheet_name, old_row)`
     - Update _Control: `update_control_entry(record_id, {sheet_name: new_sheet, sheet_row: new_row})`
     - Log audit event with old/new sheet info
   - **Fila alterada manualmente (14.3):**
     - Read _Control row by record_id
     - If not found: try finding by `final_description` in _Control
     - If multiple matches found: block update, return "Conciliación manual requerida"
     - If exact match found: use found row for update

### Step 8: Implement Offline Mode (PRD Section 9.5)
1. On any send operation, check connectivity first:
   ```python
   if not await client.verify_connectivity():
       await repo.set_status(record_id, "PENDIENTE_DE_ENVIO")
       return SendResult(False, "Sin conexión a Internet. El gasto se enviará cuando se restablezca.")
   ```
2. `async retry_pending_sends()` — background/triggered function:
   - Query all records with status `PENDIENTE_DE_ENVIO`, ordered by `created_at`
   - Verify connectivity
   - If connected, process each one through the send flow
   - If send succeeds, update status to `ENVIADO`
   - If send fails due to non-connectivity error, set `ERROR_SHEETS`
   - If still offline, stop processing (don't waste API calls)
3. Manual trigger: button in UI "Reintentar envíos pendientes"
4. Offline queue visualization in dashboard: show count of PENDIENTE_DE_ENVIO records

### Step 9: Implement Reconciliation
1. `async reconcile_record(record_id: int) -> ReconciliationResult`:
   - Read local record from PostgreSQL
   - Read control entry from _Control sheet
   - Read actual row data from the monthly sheet using `sheet_row` from control
   - Compare 16 columns:
     - Map sheet columns back to local fields (Section 13.2 reverse mapping)
     - Detect differences per field
   - Return structure:
     ```python
     {
         "status": "MATCH" | "MISMATCH" | "NOT_FOUND_IN_CONTROL" | "NOT_FOUND_IN_SHEET",
         "differences": [
             {"field": "amount", "local": 700.00, "sheets": 750.00},
             ...
         ],
         "control_entry": {...},
         "sheet_row_data": [...],
         "local_data": {...},
     }
     ```
2. Conflict resolution: provide methods to sync in either direction
   - `resolve_using_local(record_id)` — overwrite sheet row with local data
   - `resolve_using_sheets(record_id)` — overwrite local data with sheet data

### Step 10: Write Tests
1. Unit tests (mock Google Sheets API):
   - `test_verify_connectivity_online`
   - `test_verify_connectivity_offline`
   - `test_get_or_create_sheet_existing`
   - `test_get_or_create_sheet_new`
   - `test_get_month_tab_name` (all 12 months + year)
   - `test_monthly_headers_16_columns`
   - `test_consecutive_assignment_no_existing`
   - `test_consecutive_assignment_with_existing`
   - `test_consecutive_lock_prevents_race`
   - `test_catalog_sync_from_sheets`
   - `test_catalog_sync_to_sheets`
   - `test_send_flow_success`
   - `test_send_flow_offline_queues`
   - `test_update_same_month`
   - `test_update_month_change`
   - `test_reconcile_match`
   - `test_reconcile_mismatch`
   - `test_rate_limit_retry`
2. Integration tests (use real or sandbox spreadsheet):
   - Full send flow: create test record → send → verify row in sheet
   - Update flow: modify record → update in sheet → verify
   - Month change: change date → verify row moved tabs
   - Offline: disconnect → send → verify PENDIENTE_DE_ENVIO → reconnect → retry → verify ENVIADO
3. E2E tests:
   - Dashboard → review → send → verify Google Sheets reflects the record

### Step 11: Generate Evidence
1. Create `harness/evidence/fase3/integracion-sheets.json` per schema.
2. Create `harness/evidence/fase3/integracion-sheets.md` per schema.

## Artifacts
- `app/sheets/client.py` — Google Sheets API client
- `app/sheets/sync.py` — catalog sync logic
- `app/sheets/tabs.py` — monthly tab management
- `app/sheets/control.py` — _Control sheet operations
- `app/sheets/consecutive.py` — consecutive number assignment
- `app/sheets/sender.py` — send flow (11 steps)
- `app/sheets/reconciler.py` — reconciliation logic
- `app/sheets/errors.py` — custom exceptions
- `app/sheets/offline.py` — offline queue management (optional)
- `tests/unit/test_sheets.py` — unit tests
- `tests/integration/test_sheets.py` — integration tests
- `tests/e2e/test_sheets.py` — E2E tests
- `harness/evidence/fase3/integracion-sheets.json`
- `harness/evidence/fase3/integracion-sheets.md`

## Quality Criteria
- Google Sheets API client authenticates successfully
- _Categorias and _Cuentas sheets synced bidirectionally with PostgreSQL
- Monthly tabs created with exactly 16 column headers
- Month naming follows "Mes-AA" format (Spanish months)
- Consecutive numbers assigned correctly per group, no collisions
- Advisory lock prevents concurrent consecutive assignment
- 11-step send flow executes in order (Section 9.4)
- Image moved to procesados/YYYY/MM only after successful send
- _Control sheet updated on every send/update
- Same-month updates overwrite the correct row
- Month changes move row between tabs (insert + delete old)
- Offline mode queues records as PENDIENTE_DE_ENVIO
- Retry mechanism processes queued records when internet returns
- Reconciliation detects discrepancies between local and Sheets data
- Rate limiting handled with exponential backoff
- Duplicate SHA-256 detection via _Control
- No Google credentials or tokens in code, logs, or versioned files
- All tests pass with >= 90% coverage

## Edge Cases
- **API rate limiting (429):** implement exponential backoff: 1s, 2s, 4s (max 3 retries). If all retries exhausted, set status to PENDIENTE_DE_ENVIO and log warning. Never silently drop data.
- **Sheet not found:** if spreadsheet ID returns 404, raise `SheetsNotFoundError`. Do not create a new spreadsheet (spreadsheet must be pre-created by the installer).
- **_Control out of sync:** when reading _Control and a record_id is missing, attempt to find by `final_description` and `owner`. If found, update _Control with the correct record_id. If not found, flag for manual reconciliation.
- **Concurrent sends from same group:** PostgreSQL advisory lock on group_code ensures only one process computes consecutive at a time. The second process waits for the lock, then reads the updated _Control, getting the correct next number.
- **Month change during send:** if expense_date is changed between consecutive assignment and actual send (race condition), re-evaluate sheet tab just before writing. A mismatch at this point results in a retry.
- **Internet drops mid-send:** if the API call fails mid-operation, the record may be partially written. Check if the row exists in the sheet before marking as failed. If row exists but _Control entry doesn't, create the _Control entry and mark as ENVIADO. If incomplete, delete the partial row and retry.
- **Sheet row manually deleted:** if _Control references a row number that no longer has data (or has different data), reconciliation will detect NOT_FOUND_IN_SHEET. Do not blindly write to that row; require manual reconciliation to avoid overwriting someone else's data.
- **Empty sheet with only headers:** `find_next_empty_row` should return row 2 (first data row after headers).

## References
- PRD Sections 13, 13.1, 13.2, 13.3, 13.4
- PRD Sections 9.4, 9.5
- PRD Sections 12, 14, 15
- Google Sheets API v4: https://developers.google.com/sheets/api/reference/rest
- Related skills: `skill-database`, `skill-authentication`, `skill-image-extraction`
- Under `AGENTS.md` Fase 3 — skill-google-sheets
