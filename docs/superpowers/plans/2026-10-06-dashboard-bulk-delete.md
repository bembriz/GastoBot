# Dashboard Bulk Delete Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a dashboard action to delete selected expense records from PostgreSQL only.

**Architecture:** Reuse the existing dashboard checkbox selection and HTMX bulk action pattern. Add a focused `/expenses/bulk-delete` route that validates ownership and deletes database rows related to each selected `ExpenseRecord`, without touching physical image files or extraction providers.

**Tech Stack:** FastAPI, SQLAlchemy async, PostgreSQL, Jinja templates, HTMX, pytest, uv, ruff, mypy.

## Global Constraints

- Delete only PostgreSQL rows; do not delete SMB/local image files.
- Do not invoke Gemini, Kimi, Ollama, or image extraction flows.
- Use local PostgreSQL for manual verification and remove generated test data afterward.
- Preserve existing bulk-send behavior.
- No commits without explicit `AUTORIZO COMMIT`.

---

## File Structure

- Modify `app/expenses/routes.py`: add imports for related models, add helper `_delete_expense_record`, add route `bulk_delete_expenses`.
- Modify `templates/dashboard.html`: add delete button and shared bulk UI state handling.
- Modify `templates/expense_list.html`: allow selecting records for deletion even when incomplete for Sheets.
- Modify `tests/unit/test_bulk_send_routes.py`: add route unit tests for bulk delete and preserve bulk-send tests.
- Update `harness/PROGRESS.md`: record the local, undeployed change after verification.

---

### Task 1: Backend Bulk Delete Route

**Files:**
- Modify: `app/expenses/routes.py`
- Test: `tests/unit/test_bulk_send_routes.py`

**Interfaces:**
- Consumes: `record_ids: list[str] | None`, `user: User`, `db: AsyncSession`.
- Produces: `bulk_delete_expenses(record_ids, user, db) -> HTMLResponse`.

- [ ] **Step 1: Write failing tests**

Add tests that assert:

```python
async def test_bulk_delete_without_selection_returns_visible_error():
    response = await bulk_delete_expenses(record_ids=None, user=MagicMock(), db=AsyncMock())
    assert response.status_code == 400
    assert "Selecciona al menos un comprobante" in response.body.decode()


async def test_bulk_delete_rejects_record_owned_by_another_user():
    record = MagicMock()
    record.id = "record-1"
    record.owner_id = "other-user"
    record.source_filename = "ticket.jpg"

    db = AsyncMock()
    db.execute.return_value = _scalar_result(record)

    user = MagicMock()
    user.role = "standard"
    user.id = "current-user"

    response = await bulk_delete_expenses(record_ids=["record-1"], user=user, db=db)
    assert "ticket.jpg: no autorizado" in response.body.decode()
    db.delete.assert_not_called()


async def test_bulk_delete_deletes_authorized_record():
    record = MagicMock()
    record.id = "record-1"
    record.owner_id = "current-user"
    record.source_filename = "ticket.jpg"

    db = AsyncMock()
    db.execute.return_value = _scalar_result(record)

    user = MagicMock()
    user.role = "standard"
    user.id = "current-user"

    response = await bulk_delete_expenses(record_ids=["record-1"], user=user, db=db)
    assert "ticket.jpg: eliminado" in response.body.decode()
    db.delete.assert_awaited_once_with(record)
    db.commit.assert_awaited_once()
```

- [ ] **Step 2: Run tests and verify failure**

Run: `uv run pytest tests/unit/test_bulk_send_routes.py -q`

Expected: import or attribute failure because `bulk_delete_expenses` does not exist.

- [ ] **Step 3: Implement minimal backend route**

Add:

```python
@router.post("/expenses/bulk-delete", response_class=HTMLResponse)
async def bulk_delete_expenses(
    record_ids: list[str] | None = Form(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    if not record_ids:
        return HTMLResponse(
            _bulk_message("Selecciona al menos un comprobante para eliminar.", "error"),
            status_code=400,
        )

    results = []
    for rid in record_ids:
        record = (
            await db.execute(select(ExpenseRecord).where(ExpenseRecord.id == rid))
        ).scalar_one_or_none()
        if not record:
            results.append(f"<span class='error'>{rid[:8]}... no encontrado</span>")
            continue
        if user.role != "admin" and record.owner_id != user.id:
            results.append(f"<span class='error'>{record.source_filename}: no autorizado</span>")
            continue
        await db.delete(record)
        await db.commit()
        results.append(
            f"<span style='color:var(--success);'>{record.source_filename}: eliminado</span>"
        )

    return HTMLResponse("<br>".join(results))
```

If FK constraints require explicit child deletion in integration/manual tests, add helper `_delete_expense_record` that deletes child rows before deleting `ExpenseRecord`.

- [ ] **Step 4: Run backend tests**

Run: `uv run pytest tests/unit/test_bulk_send_routes.py -q`

Expected: all tests pass.

---

### Task 2: Dashboard UI

**Files:**
- Modify: `templates/dashboard.html`
- Modify: `templates/expense_list.html`

**Interfaces:**
- Consumes: `.chk-record` checkboxes with `name="record_ids"`.
- Produces: `#bulk-delete-btn` posting selected `record_ids` to `/expenses/bulk-delete`.

- [ ] **Step 1: Add delete button**

Add a secondary/danger button next to send:

```html
<button id="bulk-delete-btn" class="btn" disabled
        hx-post="/expenses/bulk-delete"
        hx-target="#bulk-result"
        hx-swap="innerHTML"
        hx-include=".chk-record:checked"
        hx-confirm="Eliminar los comprobantes seleccionados de PostgreSQL? Esta accion no borra imagenes."
        hx-indicator="#bulk-indicator">
    Eliminar seleccionados
</button>
```

- [ ] **Step 2: Update selection logic**

Keep send enabled only for selected records where `data-status === 'ready'`. Enable delete when any checkbox is selected.

- [ ] **Step 3: Allow selecting incomplete records**

In `expense_list.html`, remove the checkbox `disabled` attribute for records that are incomplete for Sheets. Preserve `data-status` so send remains restricted.

- [ ] **Step 4: Run template-focused tests**

Run: `uv run pytest tests/unit/test_templates.py tests/unit/test_bulk_send_routes.py -q`

Expected: pass.

---

### Task 3: Local PostgreSQL Verification And Cleanup

**Files:**
- No permanent files unless a test helper is needed.

**Interfaces:**
- Uses app DB session and models.

- [ ] **Step 1: Inspect local DB configuration**

Run: `uv run python - <<'PY'` with read-only config inspection, avoiding secrets in output.

- [ ] **Step 2: Create synthetic test records**

Insert records with filenames prefixed `opencode-delete-test-` and no image extraction.

- [ ] **Step 3: Exercise delete path**

Call `bulk_delete_expenses` or the HTTP route against local PostgreSQL with the synthetic IDs.

- [ ] **Step 4: Verify cleanup**

Query for `source_filename LIKE 'opencode-delete-test-%'` and related rows; expected count is zero.

---

### Task 4: Final Verification

**Files:**
- Modify: `harness/PROGRESS.md`

- [ ] **Step 1: Run unit tests**

Run: `uv run pytest tests/unit/ -q`


- [ ] **Step 2: Run lint and type checks**

Run:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy app/
```

- [ ] **Step 3: Update progress**

Record the dashboard delete change, verification output, no token usage, no deployment, no commit.

## Self-Review

- Spec coverage: UI button, backend route, PostgreSQL-only deletion, local DB cleanup, and no-token constraint are covered.
- Placeholder scan: no TBD/TODO placeholders remain.
- Type consistency: route and test names match planned imports.
