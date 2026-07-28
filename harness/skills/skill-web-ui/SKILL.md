# Skill: skill-web-ui

## Identity
Act as a **Frontend Architect & Full-Stack Developer** specialized in FastAPI + Jinja2 + HTMX. You build the complete web interface for "Gastos IA": login page, main dashboard with expense list, individual expense viewer with image manipulation and edit form, HTMX polling for status updates, role-based visibility, and responsive layout.

## Context
This skill implements PRD Section 10 (Interfaz web) — the full user-facing application. It consumes endpoints and services built by Fase 1 skills (database, auth, folder monitor, FIFO queue, image extraction). The interface has two user roles: Ruben (admin, sees everything) and Esme (standard, sees own records).

**Technology stack:** FastAPI routes + Jinja2 templates + HTMX (no React, Vue, or heavy JS frameworks) + vanilla CSS or PicoCSS (minimal, no Tailwind/SCSS unless already configured).

**PRD references:**
- Section 10.1 (Autenticación) — login page
- Section 10.2 (Pantalla principal) — dashboard with expense list
- Section 10.2.1 (HTMX Polling) — 3-second status updates
- Section 10.3 (Revisión individual) — viewer with image + form
- Section 11 (Campos visibles) — form fields and rules
- Section 11.1 (Campos obligatorios) — required field validation
- Section 4 (Usuarios y permisos) — role-based visibility

## Preconditions
- `skill-authentication` completed: login endpoints, session management, Argon2id hashing
- `skill-image-extraction` completed: Ollama extraction producing JSON with confidence scores
- `skill-fifo-queue` completed: records flow through EN_COLA → ANALIZANDO → LISTO_PARA_REVISION/REQUIERE_REVISION
- `skill-folder-monitor` completed: images detected and stored with thumbnails
- `skill-database` completed: models accessible via SQLAlchemy/asyncpg
- PostgreSQL running and accessible
- FastAPI app scaffold exists at `app/main.py`
- Jinja2 configured with templates directory `templates/`
- `uv sync --frozen` passes

## Execution

### Step 1: Set Up Static Assets and Base Template
1. Create `static/css/style.css` with base styles:
   - CSS variables for colors (background, text, border, primary, warning, danger, success)
   - Typography using system fonts
   - Responsive grid/table layout
   - Status badge styles (EN_COLA, ANALIZANDO, LISTO_PARA_REVISION, REQUIERE_REVISION, ENVIADO, ERROR_PROCESAMIENTO, DUPLICADO_EXACTO, PENDIENTE_DE_ENVIO)
   - Confidence-level color coding (high >= 0.90 green, medium 0.70-0.89 amber, low < 0.70 red)
   - Form styles with validation states
   - Empty state styling
2. Create `templates/base.html` as base Jinja2 template with:
   - HTML5 doctype, lang=es, charset UTF-8
   - Responsive viewport meta
   - HTMX script from unpkg CDN (v1.9.x)
   - Blocks: `title`, `head_extra`, `content`, `scripts_extra`
   - Header with app name and user info (username + role badge + logout link) — only if `current_user` is defined
   - Navigation: Pendientes, Historial, Catálogos (admin only)
   - Flash message support for errors/success
3. Create `app/api/webui.py` with all view routes:
   - `GET /` → redirect to `/login` or `/dashboard` based on session
   - `GET /login` → login page
   - `POST /login` → process login, set session cookie
   - `GET /logout` → clear session, redirect to login
   - `GET /dashboard` → main expense list (role-filtered)
   - `GET /expenses/list` → HTML partial for expense table (HTMX polling target)
   - `GET /expenses/{record_id}` → individual expense viewer page
   - `GET /expenses/{record_id}/status` → HTML partial for status row (HTMX polling target)
   - `POST /expenses/{record_id}/save` → save form edits
   - `GET /images/{record_id}/thumbnail` → serve thumbnail image

### Step 2: Build Login Page
1. Create `templates/login.html` extending `base.html`:
   - Centered card layout (max-width 400px)
   - Username input (text, required, autofocus)
   - Password input (password, required)
   - Submit button
   - Error message display for invalid credentials or locked account
   - Redirect to dashboard on success
2. Implement server-side at `GET /login` and `POST /login`:
   - Show login form
   - Validate credentials using authentication module (Argon2id)
   - Set session cookie with `HttpOnly`, `Secure`, `SameSite` flags
   - Implement login attempt counting and temporary lockout (5 attempts, 15-min lock)
   - On first login, force password change redirect

### Step 3: Build Main Dashboard (Expense List)
1. Create `templates/dashboard.html` extending `base.html`:
   - Page title "Pendientes"
   - HTMX-polling container `div#expense-list` with `hx-get="/expenses/list" hx-trigger="every 3s"`
   - Loading indicator during HTMX requests
   - Empty state when no expenses exist
2. Create `templates/partials/expense-table.html` (partial returned by `/expenses/list`):
   - Table with columns: Thumbnail, Filename, Date, Amount, Bank, Status, Warnings, Owner (admin only)
   - Click on thumbnail or filename navigates to `/expenses/{record_id}`
   - Status badge with CSS class matching the status value
   - Warning indicator when any confidence score < 0.70
   - Owner column visible only when `current_user.role == 'admin'`
   - Each row polls its own status via `hx-get="/expenses/{record_id}/status" hx-trigger="every 3s"` if status is non-terminal, wraps within expense-table partial
3. Create `templates/partials/expense-status.html` (partial returned by `/expenses/{record_id}/status`):
   - Status badge
   - Warning indicators (low confidence fields)
   - Truncated filename, date, amount, bank, owner
   - Stop polling logic: only trigger HTMX polling if status is EN_COLA, ANALIZANDO, ESPERANDO_ARCHIVO_ESTABLE, DETECTADO, or PENDIENTE_DE_ENVIO. Terminal states (ENVIADO, DUPLICADO_EXACTO, ERROR_PROCESAMIENTO, ERROR_SHEETS) remove the polling trigger.
   - Implement this by conditionally omitting `hx-trigger` on terminal states

### Step 4: Build Expense Viewer (Individual Review)
1. Create `templates/expense-viewer.html` extending `base.html`:
   - Two-column desktop layout: image on left (60%), form on right (40%)
   - Single-column stack on mobile (< 768px)
2. **Image column** — Create `templates/partials/image-viewer.html`:
   - Full image display with `max-width: 100%` and `object-fit: contain`
   - Toolbar: zoom in (+), zoom out (−), rotate (90deg), fit-to-width, fullscreen
   - Implement zoom/rotate with CSS transforms on the `<img>` element, driven by `hx-on:*` or small vanilla JS
   - Fullscreen via `element.requestFullscreen()` browser API
   - Lazy loading
3. **Form column** — Create `templates/partials/expense-form.html`:
   - Fields in order per PRD Section 11:

   | Field | Input Type | Source | Editable |
   |---|---|---|---|
   | Fecha del gasto | `<input type="date">` | Extracted or user-set | Yes |
   | Grupo | `<input type="text">` | User input | Yes |
   | Descripción del ticket | `<textarea>` | Extracted | Yes |
   | Descripción final | Read-only `<span>` or `<input readonly>` | Computed: Grupo-Consecutivo-Descripción | No |
   | Categoría | `<select>` from catalog | Selected by user | Yes |
   | Empleado | Hidden or readonly | "RUBEN BENJAMIN VAZQUEZ EMBRIZ" | No |
   | Pagado por | Hidden or readonly | "Empresa" | No |
   | Actividades | Hidden | Empty | No |
   | Fecha contable | Hidden | Empty | No |
   | Cuenta | `<select>` from catalog | Selected by user | Yes |
   | Precio unitario | `<input type="number" step="0.01">` | Extracted amount | Yes |
   | Cantidad | Hidden or readonly | 1 | No |
   | Incluir impuestos | Hidden | Empty | No |
   | Importe de impuestos | Hidden | Empty | No |
   | Total | `<input type="number" step="0.01">` | Extracted amount | Yes |
   | Estado | Hidden or readonly | "Por reportar" | No |
   | Banco | `<input type="text">` | Extracted | Yes |
   | Tipo de transacción | `<select>` (Transferencia/Crédito) | Extracted | Yes |

   - Sync `precio_unitario` and `total` fields: when one changes, update the other via `hx-on:input` or HTMX event
   - Confidence indicators next to each extracted field: green/amber/red dot based on confidence score
   - "Enviar a Google Sheets" button — disabled if any required field empty (date, group, description, category, account, unit price, total, bank, transaction type)
   - Client-side validation: check required fields on form change, toggle button disabled state
4. **Save endpoint** `POST /expenses/{record_id}/save`:
   - Accept form data, validate required fields server-side
   - Update expense record in PostgreSQL
   - Return updated form partial or redirect on success
   - Return validation errors inline (HTMX swap)

### Step 5: Implement HTMX Polling Logic
1. For the main expense list:
   - `GET /expenses/list` returns the full `<table>` partial
   - Polling only for records in non-terminal states (EN_COLA, ANALIZANDO, ESPERANDO_ARCHIVO_ESTABLE)
   - Server-side: query expenses filtered by current_user, ordered by enqueued_at
   - Include `hx-trigger="every 3s"` only when there are non-terminal records
2. For individual status rows:
   - `GET /expenses/{record_id}/status` returns `<tr>` partial for that specific record
   - Conditionally set `hx-trigger`: include "every 3s" if status is non-terminal, omit if terminal
3. For the expense viewer form:
   - Poll description final update after group/description changes
   - `GET /expenses/{record_id}/description-preview` returns the computed description
   - Trigger on group/description input change via `hx-on:input`

### Step 6: Implement Role-Based Visibility
1. All expense queries must filter by owner when `current_user.role == 'estandar'`:
   - Esme sees only `WHERE owner = 'Esme'`
   - Ruben sees all records (no filter)
2. Navigation: catalog link only shown to admin (`{% if current_user.role == 'admin' %}`)
3. Owner column in expense table: only rendered for admin
4. All catalog routes (`/catalogs/*`) must return 403 for non-admin users
5. Admin can view/edit any expense; standard user can only view/edit own expenses
6. Test with both user accounts: verify Esme cannot access catalogs or see Ruben's records

### Step 7: Add Error Handling and Edge Cases
1. Image load failure: show placeholder thumbnail with error icon
2. Large images: serve optimized thumbnails (max 200px), full image with lazy loading
3. Concurrent edits: implement optimistic locking via `updated_at` timestamp comparison; reject save if record was modified since loaded
4. Form validation before Ollama finishes: show form fields as readonly/disabled until status becomes LISTO_PARA_REVISION or REQUIERE_REVISION
5. Polling stops automatically: no polling for terminal states
6. Session expiry: intercept 401 responses with HTMX, redirect to login
7. Network errors: show toast/notification on failed HTMX requests

### Step 8: Write Tests
1. Unit tests for view routes (mock dependencies):
   - `test_dashboard_requires_auth`
   - `test_dashboard_filters_by_owner_for_estandar`
   - `test_expense_list_returns_html_partial`
   - `test_expense_status_returns_partial`
   - `test_expense_viewer_requires_ownership`
   - `test_save_requires_ownership`
2. Integration tests:
   - Full flow: login → dashboard → click expense → view image → edit form → save
   - HTMX polling: verify status transitions render correctly
   - Role-based access: Esme cannot view/delete Ruben's records
3. E2E tests (Playwright):
   - Login both users successfully
   - Dashboard renders expense list
   - Polling updates status badge without page reload
   - Expense viewer: zoom, rotate, fullscreen
   - Form: field sync (precio unitario = total), required field blocking
   - Logout and session expiry

### Step 9: Generate Evidence
1. Create `harness/evidence/fase2/interfaz-web.json` per `evidence.schema.json`.
2. Create `harness/evidence/fase2/interfaz-web.md` per `evidence-markdown.schema.md`.
3. Include screenshots or references to test output files.
4. Record metrics: test count, coverage %, number of templates, number of routes.

## Artifacts
- `templates/base.html` — base Jinja2 layout
- `templates/login.html` — login page
- `templates/dashboard.html` — main dashboard
- `templates/expense-viewer.html` — individual expense viewer
- `templates/partials/expense-table.html` — HTMX partial for table
- `templates/partials/expense-status.html` — HTMX partial for status row
- `templates/partials/expense-form.html` — form fields
- `templates/partials/image-viewer.html` — image with controls
- `static/css/style.css` — application styles
- `app/api/webui.py` — view routes
- `harness/evidence/fase2/interfaz-web.json` — machine-readable evidence
- `harness/evidence/fase2/interfaz-web.md` — human-readable evidence

## Quality Criteria
- All view routes return correct HTTP status codes (200, 302, 401, 403)
- Login works for both users with Argon2id verification
- Session cookies have HttpOnly, Secure, SameSite flags
- Dashboard renders expense table with correct columns
- HTMX polling updates status every 3 seconds without F5
- Polling stops for terminal states (ENVIADO, DUPLICADO_EXACTO, ERROR_PROCESAMIENTO)
- Image viewer supports zoom, rotate, fullscreen
- Form fields match PRD Section 11 exactly
- Precio unitario and Total stay synchronized
- Send button disabled when required fields missing
- Ruben sees all expenses; Esme sees only own
- Esme gets 403 on catalog routes
- Login lockout after 5 failed attempts
- Responsive layout works on mobile viewport
- All unit tests pass with >= 90% coverage
- No JavaScript frameworks other than HTMX
- No hardcoded secrets or credentials
- HTML validates (no broken tags, proper nesting)

## Edge Cases
- **Polling stops for terminal states:** implement conditional `hx-trigger` — terminal states (ENVIADO, DUPLICADO_EXACTO, ERROR_PROCESAMIENTO, ERROR_SHEETS) must not have `hx-trigger="every 3s"`. Non-terminal states (EN_COLA, ANALIZANDO, LISTO_PARA_REVISION, REQUIERE_REVISION, PENDIENTE_DE_ENVIO, ESPERANDO_ARCHIVO_ESTABLE) must poll.
- **Concurrent edits:** if user A opens edit form and user B saves first, user A's save must be rejected with a message "El registro fue modificado por otro usuario. Recarga la página."
- **Image load failure:** show a placeholder with "No se pudo cargar la imagen" text and a retry button
- **Form validation before Ollama finishes:** form fields should be disabled (or shown but with a warning) until status reaches LISTO_PARA_REVISION or REQUIERE_REVISION
- **Large images (15MB):** serve resized versions for display; original only for download. Implement max-width CSS constraint.
- **Session expiry during HTMX request:** detect 401 response, show "Sesión expirada" message, redirect to login after 3 seconds
- **Empty states:** dashboard with no expenses shows helpful message; empty dropdown for catalogs shows "No hay elementos"
- **Multiple browser windows:** both should reflect real-time status via polling independently

## References
- PRD Sections 10, 10.1, 10.2, 10.2.1, 10.3, 11, 11.1
- PRD Section 4 (Usuarios y permisos)
- Related skills: `skill-authentication`, `skill-image-extraction`, `skill-fifo-queue`, `skill-database`, `skill-catalogs`, `skill-history`
- HTMX documentation: https://htmx.org/docs/
- Under `AGENTS.md` Fase 2 — skill-web-ui
