# Skill: skill-fase2-interfaz

## Identity
Act as the **Fase 2 Orchestrator Agent**. You coordinate the sequential execution of Fase 2 skills: `skill-web-ui`, `skill-catalogs`, and `skill-history`. You do not implement code directly; you invoke each skill in order, validate its evidence, and produce the phase-level summary report.

## Context
Fase 2 builds the entire web interface (login, dashboard, expense viewer, catalogs, history) on top of the Fase 1 core (database, authentication, folder monitor, FIFO queue, image extraction).

**PRD references:**
- Section 10 (Interfaz web) — full scope
- Section 10.2.1 (HTMX Polling)
- Section 10.3 (Revisión individual)
- Section 10.4 (Historial)
- Section 10.5 (Catálogos)
- Section 4 (Usuarios y permisos)
- Section 11 (Campos visibles y reglas)

## Preconditions
- Fase 1 completed (all Fase 1 skills: `skill-database`, `skill-authentication`, `skill-folder-monitor`, `skill-fifo-queue`, `skill-image-extraction`)
- PostgreSQL schema deployed and migrations applied
- Authentication system operational with Argon2id hashing
- Folder monitor detecting images and placing them in the FIFO queue
- Image extraction producing JSON with confidence scores
- All Fase 1 evidence artifacts present under `harness/evidence/fase1/`
- Branch `arnes` active

## Execution

### Step 1: Validate Preconditions
1. Check that Fase 1 status is `completed` in `AGENTS.md` frontmatter.
2. Verify all Fase 1 evidence files exist: `harness/evidence/fase1/schema-postgresql.json`, `schema-postgresql.md`, `sistema-autenticacion.json`, `sistema-autenticacion.md`, `monitor-carpetas.json`, `monitor-carpetas.md`, `cola-fifo.json`, `cola-fifo.md`, `extraccion-imagenes.json`, `extraccion-imagenes.md`.
3. Run `uv sync --frozen` to ensure dependencies are available.
4. If any precondition fails, stop and report the gap. Do not proceed.

### Step 2: Update Phase Status
1. In `AGENTS.md`, change `fase2.status` from `pending` to `in_progress`.
2. Create/update `harness/PROGRESS.md` with current phase, ETA (16 hours), and skill checklist.
3. Update `todowrite` with tasks: `skill-web-ui`, `skill-catalogs`, `skill-history`, `phase-summary`.

### Step 3: Execute skill-web-ui
1. Invoke `skill-web-ui` by loading `harness/skills/skill-web-ui/SKILL.md`.
2. Follow its instructions exactly to build: login page, main dashboard with expense list, individual expense viewer with image + form, HTMX polling every 3 seconds, role-based visibility.
3. After completion, verify that evidence files exist:
   - `harness/evidence/fase2/interfaz-web.json`
   - `harness/evidence/fase2/interfaz-web.md`
4. Confirm all quality criteria pass before proceeding.
5. If the skill fails or produces partial results, stop and report.

### Step 4: Execute skill-catalogs
1. Invoke `skill-catalogs` by loading `harness/skills/skill-catalogs/SKILL.md`.
2. Follow its instructions exactly to build: category CRUD, account CRUD, user management, admin-only access, soft delete, HTMX inline editing.
3. After completion, verify that evidence files exist:
   - `harness/evidence/fase2/catalogos.json`
   - `harness/evidence/fase2/catalogos.md`
4. Confirm all quality criteria pass before proceeding.
5. If the skill fails, stop and report.

### Step 5: Execute skill-history
1. Invoke `skill-history` by loading `harness/skills/skill-history/SKILL.md`.
2. Follow its instructions exactly to build: searchable history, filters, pagination, inline editing, Google Sheets reconciliation, audit trail.
3. After completion, verify that evidence files exist:
   - `harness/evidence/fase2/historial.json`
   - `harness/evidence/fase2/historial.md`
4. Confirm all quality criteria pass before proceeding.

### Step 6: Run Quality Gate
1. Invoke `skill-quality-gate` for the Fase 2 scope.
2. Verify: `uv sync --frozen`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy app/`, `uv run pytest tests/unit/ --cov=app --cov-fail-under=90`, `uv run pytest tests/integration/`, `uv run pytest tests/e2e/`, `uv run pip-audit`, `gitleaks detect`.
3. If any gate fails, fix issues and re-run. Do not proceed with failures.

### Step 7: Generate Phase Summary
1. Aggregate all Fase 2 evidence into a phase-level summary report:
   - File: `harness/evidence/fase2/fase2-summary.md`
   - Include: skill statuses, total duration, metrics summary, artifacts list, errors/warnings, next steps.
2. Create a JSON summary: `harness/evidence/fase2/fase2-summary.json` following `evidence.schema.json`.

### Step 8: Close Fase 2
1. Verify all 8 evidence files exist (3 skills x2 + phase summary x2).
2. In `AGENTS.md`, change `fase2.status` from `in_progress` to `completed`.
3. Update `harness/PROGRESS.md` with completion status.
4. Present a summary to the user with: skills completed, test results, coverage, files created, and any issues.

### Step 9: Present GATE
1. Present the executive summary of Fase 2 completion.
2. Request explicit authorization to proceed to Fase 3.
3. Do NOT invoke `skill-fase3-sheets` or modify Fase 3 status until the user says "AUTORIZO".

## Artifacts
- `harness/evidence/fase2/interfaz-web.json` — machine-readable evidence from skill-web-ui
- `harness/evidence/fase2/interfaz-web.md` — human-readable evidence from skill-web-ui
- `harness/evidence/fase2/catalogos.json` — machine-readable evidence from skill-catalogs
- `harness/evidence/fase2/catalogos.md` — human-readable evidence from skill-catalogs
- `harness/evidence/fase2/historial.json` — machine-readable evidence from skill-history
- `harness/evidence/fase2/historial.md` — human-readable evidence from skill-history
- `harness/evidence/fase2/fase2-summary.json` — phase-level machine-readable summary
- `harness/evidence/fase2/fase2-summary.md` — phase-level human-readable summary
- `harness/PROGRESS.md` (updated) — progress tracking

## Quality Criteria
- All three Fase 2 skills completed with `passed` status
- All quality gate checks passing (lint, types, tests >= 90% coverage, no secrets exposed)
- All evidence files present and schema-valid
- End-to-end flows working: login → dashboard → polling → review → catalogs → history
- Both users (Ruben and Esme) see correct role-based views
- HTMX polling updates status without page reload
- No hardcoded secrets anywhere

## Edge Cases
- A Fase 2 skill fails mid-execution: stop the pipeline, report which skill failed, do not proceed to the next skill
- Quality gate fails: fix issues within the relevant skill scope, re-run that skill's verification, then re-run the gate
- Fase 1 evidence missing but Fase 1 marked completed: flag inconsistency and request user clarification
- User interrupts during execution: preserve current progress, report what was completed and what remains

## References
- PRD Sections 10, 10.2.1, 10.3, 10.4, 10.5
- PRD Section 4 (Usuarios y permisos)
- PRD Section 11 (Campos visibles)
- Related skills: `skill-web-ui`, `skill-catalogs`, `skill-history`, `skill-quality-gate`
- Parent: `AGENTS.md` Fase 2 definition
