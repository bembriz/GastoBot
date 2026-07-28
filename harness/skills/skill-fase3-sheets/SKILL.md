# Skill: skill-fase3-sheets

## Identity
Act as the **Fase 3 Orchestrator Agent**. You coordinate the execution of Fase 3 skills: `skill-google-sheets`. You do not implement code directly; you invoke each skill, validate its evidence, and produce the phase-level summary report.

## Context
Fase 3 integrates Google Sheets as the business destination for expense records. It builds on the Fase 2 web interface: records that have been reviewed and approved will be sent to Google Sheets via the Google Sheets API.

**PRD references:**
- Section 13 (Google Sheets) — full scope
- Section 13.1 (Columnas mensuales) — 16 column structure
- Section 13.2 (Mapeo) — field-to-column mapping
- Section 13.3 (Pestañas mensuales) — month naming and creation
- Section 13.4 (Pestañas técnicas) — _Categorias, _Cuentas, _Control
- Section 9.4 (Envío) — send flow
- Section 9.5 (Operación sin Internet) — offline handling
- Section 14 (Actualización de registros) — update in sheets

## Preconditions
- Fase 2 completed (all Fase 2 skills: `skill-web-ui`, `skill-catalogs`, `skill-history`)
- All Fase 2 evidence artifacts present
- PostgreSQL with populated catalog data (categories and accounts)
- At least some expense records in LISTO_PARA_REVISION or REQUIERE_REVISION status ready for sending
- `GASTOSIA_GOOGLE_CREDENTIALS_PATH` environment variable set (path to service account JSON, outside repo)
- `GASTOSIA_GOOGLE_SPREADSHEET_ID` environment variable set
- Google Sheets API enabled for the service account
- Service account has editor access to the target spreadsheet
- Branch `arnes` active

## Execution

### Step 1: Validate Preconditions
1. Check that Fase 2 status is `completed` in `AGENTS.md` frontmatter.
2. Verify all Fase 2 evidence files exist: `harness/evidence/fase2/interfaz-web.json`, `interfaz-web.md`, `catalogos.json`, `catalogos.md`, `historial.json`, `historial.md`, `fase2-summary.json`, `fase2-summary.md`.
3. Verify Google Sheets prerequisites:
   - Check env var `GASTOSIA_GOOGLE_CREDENTIALS_PATH` is set and file exists
   - Check env var `GASTOSIA_GOOGLE_SPREADSHEET_ID` is set
   - Run a quick connectivity test (read spreadsheet metadata using the API)
4. Run `uv sync --frozen` to ensure dependencies.
5. If any precondition fails, stop and report.

### Step 2: Update Phase Status
1. In `AGENTS.md`, change `fase3.status` from `pending` to `in_progress`.
2. Update `harness/PROGRESS.md` with current phase, ETA (12 hours), and skill checklist.
3. Update `todowrite` with tasks: `skill-google-sheets`, `phase-summary`.

### Step 3: Execute skill-google-sheets
1. Invoke `skill-google-sheets` by loading `harness/skills/skill-google-sheets/SKILL.md`.
2. Follow its instructions exactly to build: catalog sync, monthly tabs with 16 headers, _Control sheet management, consecutive number assignment, insert/update/delete rows, month change handling, offline queue, reconciliation.
3. After completion, verify that evidence files exist:
   - `harness/evidence/fase3/integracion-sheets.json`
   - `harness/evidence/fase3/integracion-sheets.md`
4. Confirm all quality criteria pass before proceeding.

### Step 4: Run Quality Gate
1. Invoke `skill-quality-gate` for the Fase 3 scope.
2. Verify: `uv sync --frozen`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy app/`, `uv run pytest tests/unit/ --cov=app --cov-fail-under=90`, `uv run pytest tests/integration/`, `uv run pytest tests/e2e/`, `uv run pip-audit`, `gitleaks detect`.
3. If any gate fails, fix issues and re-run.

### Step 5: Generate Phase Summary
1. Aggregate all Fase 3 evidence into a phase-level summary report:
   - File: `harness/evidence/fase3/fase3-summary.md`
   - Include: skill status, metrics, artifacts, errors/warnings, next steps
2. Create JSON summary: `harness/evidence/fase3/fase3-summary.json` per `evidence.schema.json`.

### Step 6: Close Fase 3
1. Verify all 4 evidence files exist (1 skill x2 + phase summary x2).
2. In `AGENTS.md`, change `fase3.status` from `in_progress` to `completed`.
3. Update `harness/PROGRESS.md` with completion status.
4. Present summary to user.

### Step 7: Present GATE
1. Present executive summary of Fase 3 completion.
2. Request explicit authorization to proceed to Fase 4.
3. Do NOT invoke `skill-fase4-instalador` until user says "AUTORIZO".

## Artifacts
- `harness/evidence/fase3/integracion-sheets.json`
- `harness/evidence/fase3/integracion-sheets.md`
- `harness/evidence/fase3/fase3-summary.json`
- `harness/evidence/fase3/fase3-summary.md`
- `harness/PROGRESS.md` (updated)

## Quality Criteria
- Google Sheets skill completed with `passed` status
- All quality gate checks passing
- Evidence files present and schema-valid
- End-to-end flow: review → send → sheet row created → _Control updated → image moved
- Catalog sync from _Categorias and _Cuentas works
- Month tabs created with 16 headers
- Consecutive numbers correctly assigned per group
- Offline send queuing works
- No hardcoded secrets

## Edge Cases
- Google Sheets skill fails mid-execution: stop pipeline, report, do not proceed
- Google credentials missing or invalid: report and stop; this is a prerequisite gap
- Quality gate fails: fix issues within the google-sheets skill scope, re-run gate
- Internet unavailable during validation: skip connectivity tests, note in evidence; skill must handle offline mode

## References
- PRD Sections 13, 13.1, 13.2, 13.3, 13.4
- PRD Sections 9.4, 9.5, 14
- Related skills: `skill-google-sheets`, `skill-quality-gate`
- Parent: `AGENTS.md` Fase 3 definition
