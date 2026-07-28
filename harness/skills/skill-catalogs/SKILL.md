# Skill: skill-catalogs

## Identity
Act as a **Backend Developer & Admin Panel Builder** specialized in FastAPI + HTMX CRUD interfaces. You build the catalog management system for categories, accounts, and users — accessible only to the admin (Ruben). Everything uses HTMX for inline editing with no page reloads.

## Context
This skill implements PRD Section 10.5 (Catálogos) and Section 4 (Usuarios y permisos). Catalogs control dropdown values used in the expense review form. Only the admin can create, edit, activate, and deactivate catalog entries.

**Core principle: soft delete.** Values already used in existing expense records are never physically deleted; they are marked as `active = false` and hidden from dropdowns but preserved for data integrity.

**PRD references:**
- Section 10.5 (Catálogos) — CRUD for categories, accounts, users
- Section 4 (Usuarios y permisos) — user management
- Section 11 (Campos visibles) — dropdowns for category and account
- Section 13.4 (Pestañas técnicas) — _Categorias and _Cuentas sheets

## Preconditions
- `skill-web-ui` completed: base templates, navigation, role-based visibility working
- `skill-database` completed: users and catalog models in PostgreSQL
- `skill-authentication` completed: session management, `get_current_user` dependency
- Admin user (Ruben) created with admin role
- Standard user (Esme) created with standard role
- `uv sync --frozen` passes

## Execution

### Step 1: Create Catalog Models and Repository
1. Verify database models exist in `app/database/models.py`:
   - `Category`: id, code (unique), description, active (bool, default True), created_at, updated_at
   - `Account`: id, code (unique), description, active (bool, default True), created_at, updated_at
   - `User`: id, username (unique), password_hash, role (enum: admin/estandar), active (bool), failed_attempts (int), locked_until (datetime nullable), must_change_password (bool), created_at, updated_at
2. Create `app/catalogs/repository.py` with:
   - `CatalogRepository` class
   - `get_all_categories(include_inactive: bool = False) -> list[Category]`
   - `get_active_categories() -> list[Category]` (for dropdowns)
   - `get_category_by_id(id) -> Category`
   - `create_category(code, description) -> Category`
   - `update_category(id, code, description) -> Category`
   - `deactivate_category(id) -> Category` (soft delete — sets active=False)
   - `is_category_in_use(id) -> bool` (checks expense_records table)
   - Same pattern for Account entity
3. Create `app/users/repository.py`:
   - `get_all_users() -> list[User]`
   - `get_user_by_id(id) -> User`
   - `create_user(username, initial_password, role) -> User` (uses Argon2id)
   - `deactivate_user(id) -> User` (cannot deactivate own admin user)
   - `reset_password(id, new_password) -> User`
   - `unlock_user(id) -> User` (reset failed_attempts and locked_until)

### Step 2: Create Catalog Routes
1. Create `app/api/catalogs.py` with APIRouter:
   - All routes require admin role check via dependency
   - Return 403 for non-admin users

   **Category routes:**
   - `GET /catalogs` — main catalog page with tabs/sections for Categories, Accounts, Users
   - `GET /catalogs/categories` — HTML partial with category table
   - `POST /catalogs/categories` — create new category (Form: code, description)
   - `GET /catalogs/categories/{id}/edit` — HTML partial with inline edit form
   - `PUT /catalogs/categories/{id}` — update category
   - `DELETE /catalogs/categories/{id}` — deactivate category (soft delete)
     - If category is in use by any expense record, respond with warning: "Esta categoría está en uso en {N} registros. Se desactivará pero no se eliminará."
     - If not in use, offer option to hard delete or soft delete. Default to soft delete.

   **Account routes:** (same pattern as categories)
   - `GET /catalogs/accounts`
   - `POST /catalogs/accounts`
   - `GET /catalogs/accounts/{id}/edit`
   - `PUT /catalogs/accounts/{id}`
   - `DELETE /catalogs/accounts/{id}`

   **User routes:**
   - `GET /catalogs/users` — HTML partial with user list
   - `POST /catalogs/users` — create new user (Form: username, initial_password, role)
     - Password hashed with Argon2id before storage
     - `must_change_password` set to True
   - `GET /catalogs/users/{id}/edit` — HTML partial for editing user
   - `PUT /catalogs/users/{id}` — update user (change role, reset password)
   - `DELETE /catalogs/users/{id}` — deactivate user
     - Cannot deactivate own admin user
     - Prompt confirmation: "¿Desactivar a {username}? No podrá iniciar sesión."
   - `POST /catalogs/users/{id}/unlock` — unlock user (reset failed attempts)
   - `POST /catalogs/users/{id}/reset-password` — reset password (requires new password input)

### Step 3: Create Catalog Templates
1. `templates/catalogs.html` — main catalog page:
   - Tab navigation: Categorías | Cuentas | Usuarios
   - HTMX-loaded content area for active tab
   - Each tab loads its content via `hx-get` on click

2. `templates/partials/catalogs/categories.html`:
   - Table with columns: Código, Descripción, Activo, Acciones
   - "Nueva Categoría" button at top
   - Each row has Edit and Deactivate buttons
   - Active/inactive badge (green/gray)
   - Inline edit: clicking Edit replaces the row with a form containing code and description inputs + Save/Cancel buttons
   - Save triggers `PUT` via HTMX, row reverts to display mode on success
   - Deactivate triggers `DELETE` with confirmation dialog

3. `templates/partials/catalogs/accounts.html`: same pattern as categories

4. `templates/partials/catalogs/users.html`:
   - Table with columns: Usuario, Rol, Activo, Intentos Fallidos, Bloqueado, Acciones
   - "Nuevo Usuario" button
   - Row actions: Editar (role change), Reset Password (modal with new password input), Desbloquear (if locked), Desactivar
   - Cannot deactivate own admin user (button disabled with tooltip)
   - Failed attempts shown as "3/5" with color coding (green < 3, amber = 3-4, red >= 5)
   - Locked status shown with icon and unlock action

5. Inline edit form partials:
   - `templates/partials/catalogs/category-edit-form.html`
   - `templates/partials/catalogs/account-edit-form.html`
   - `templates/partials/catalogs/user-edit-form.html`

### Step 4: Implement Admin-Only Access
1. Create `app/auth/dependencies.py`:
   - `require_admin` dependency: checks `current_user.role == 'admin'`, returns 403 if not
2. Apply to all catalog routes:
   ```python
   @router.get("/catalogs")
   @require_admin
   async def catalogs_page(request: Request, current_user = Depends(get_current_user)):
   ```
3. Test: non-admin user accessing any `/catalogs/*` route gets 403 with message "Acceso restringido a administradores"
4. Navigation in `base.html`: catalog link only rendered for admin

### Step 5: Add Soft Delete Logic
1. **Category/Account deletion flow:**
   - Check if the entity is referenced in any `expense_records` row
   - If YES: return response with warning message, set active=False, return success "Categoría desactivada. Sigue visible en {N} registros existentes."
   - If NO: still soft-delete by default (set active=False). Optionally allow hard delete via confirmation.
2. **User deactivation:**
   - Prevent deactivating own admin account (check `current_user.id != target_user.id`)
   - Deactivate sets active=False; user cannot login
   - Active users shown in dropdowns; inactive users are hidden but preserved

### Step 6: Handle Dropdown Integration
1. The expense form (`templates/partials/expense-form.html`) loads categories and accounts via:
   - `GET /catalogs/categories/active` → returns JSON or HTML `<option>` list for dropdown
   - `GET /catalogs/accounts/active` → returns JSON or HTML `<option>` list for dropdown
2. These endpoints return only active entries
3. Dropdowns refresh via HTMX when catalog changes are made (optional: use `HX-Trigger` header to signal form update)

### Step 7: Write Tests
1. Unit tests:
   - `test_catalogs_require_admin` — non-admin gets 403
   - `test_admin_can_create_category`
   - `test_admin_can_update_category`
   - `test_deactivate_category_in_use` — sets active=False, warns user
   - `test_deactivate_category_not_in_use` — sets active=False
   - `test_cannot_deactivate_own_admin_user`
   - `test_create_user_hashes_password`
   - `test_reset_password`
   - `test_unlock_user`
2. Integration tests:
   - Full CRUD flow for each entity
   - Inline editing via HTMX: click edit → form appears → save → row updates
   - Deactivation flow with confirmation
3. E2E tests:
   - Admin logs in, navigates to catalogs, creates category, edits, deactivates
   - Non-admin user gets 403 on catalog routes
   - New user created, can login and must change password

### Step 8: Generate Evidence
1. Create `harness/evidence/fase2/catalogos.json` per schema.
2. Create `harness/evidence/fase2/catalogos.md` per schema.

## Artifacts
- `app/catalogs/repository.py` — catalog repository
- `app/users/repository.py` — user management repository
- `app/api/catalogs.py` — catalog API routes
- `app/auth/dependencies.py` — admin dependency (or update existing)
- `templates/catalogs.html` — main catalog page
- `templates/partials/catalogs/categories.html` — category table
- `templates/partials/catalogs/accounts.html` — account table
- `templates/partials/catalogs/users.html` — user table
- `templates/partials/catalogs/category-edit-form.html` — edit form
- `templates/partials/catalogs/account-edit-form.html` — edit form
- `templates/partials/catalogs/user-edit-form.html` — edit form
- `tests/unit/test_catalogs.py` — unit tests
- `tests/integration/test_catalogs.py` — integration tests
- `tests/e2e/test_catalogs.py` — E2E tests
- `harness/evidence/fase2/catalogos.json`
- `harness/evidence/fase2/catalogos.md`

## Quality Criteria
- All catalog routes return 403 for non-admin users
- Admin can create, edit, activate, deactivate categories and accounts
- Values used in existing expense records are soft-deleted (active=False), never hard-deleted
- User management: create new users, deactivate (not own admin), reset password, unlock
- Password hashing with Argon2id on user creation and password reset
- New users forced to change password on first login
- Inline editing works with HTMX (no page reload)
- Confirmation dialogs for destructive actions
- Dropdowns in expense form only show active entries
- All tests pass with >= 90% coverage
- No secrets or credentials in code

## Edge Cases
- **Delete category used in existing records:** only deactivate (set active=False). Show warning: "Esta categoría está en uso en {N} registros. Se desactivará pero no se eliminará." Never hard-delete referenced entities.
- **Concurrent catalog edits:** if two admins edit the same catalog entry simultaneously, the last save wins (no optimistic locking needed for catalogs since only one admin). Document this as accepted limitation.
- **Empty catalog handling:** empty table shows "No hay categorías registradas" message with a prominent "Crear primera categoría" button.
- **Prevent deleting own admin user:** check `current_user.id != target_user.id` before deactivation. Button should be disabled with tooltip "No puedes desactivar tu propio usuario."
- **Duplicate code/username:** server-side validation with user-friendly error message "El código '{code}' ya existe en {entity_name}."
- **Inactive items in dropdowns:** `GET /catalogs/categories/active` must exclude inactive items. Previously-selected inactive items should still display in the expense form as the selected value but with a "(desactivado)" suffix.

## References
- PRD Sections 10.5, 4, 11, 13.4
- Related skills: `skill-web-ui`, `skill-authentication`, `skill-database`
- Under `AGENTS.md` Fase 2 — skill-catalogs
