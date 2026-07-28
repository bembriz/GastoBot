# Skill: skill-fase4-instalador

## Identity
As the Fase 4 orchestrator for Gastos IA, you coordinate the infrastructure provisioning and application installation in the correct order. You invoke `skill-infrastructure` first (which requires GATE authorization at each infrastructure change), then `skill-installer` (which deploys and configures the application). You track progress, generate phase-level evidence, and present a summary to the user.

## Context
Fase 4 — "Instalador" — transforms a bare Windows Server host with Hyper-V into a fully functional Gastos IA environment. The phase has two sequential skills:

1. **skill-infrastructure:** Provisions the VM, networking, HTTPS (Caddy), Ollama, SMB mounts, environment file, systemd service. Every infrastructure change requires explicit "AUTORIZADO" from the user.
2. **skill-installer:** Deploys the application code, creates the database, configures Google Sheets, creates user accounts, populates environment variables, activates services, runs tests, generates diagnostics.

This phase produces the most artifacts (18 evidence files) and has the highest impact on the production environment. It requires the user to be present and actively authorizing changes throughout.

**Key PRD sections:** Full Fase 4 scope (sections 23, 24, plus infrastructure sections 6, 19, 19.4).

## Preconditions
- Fase 3 (`skill-fase3-sheets`) must be `completed` in `harness/PROGRESS.md`.
- Branch `arnes` must be active.
- User must be available throughout the phase to authorize infrastructure changes.
- Windows Server host with Hyper-V accessible (RDP or console).
- PostgreSQL server reachable on target network.
- SMB shares created on Windows Server.
- Google service account JSON file and spreadsheet ID available.
- `scripts/install-gastos-ia.ps1` exists in the repository.

## Execution

### Step 1: Validate Phase Preconditions
1. Read `harness/PROGRESS.md` to confirm Fase 3 is `completed`.
2. Confirm current branch is `arnes`:
   ```bash
   git branch --show-current
   ```
3. Verify `scripts/install-gastos-ia.ps1` exists.
4. Verify all Fase 3 evidence artifacts exist in `harness/evidence/fase3/`.
5. Confirm user is ready to begin and will be available for authorization prompts.
6. Update `harness/PROGRESS.md`:
   - Set `fase4.status` to `in_progress`.
   - Set `fase4.started_at` to current timestamp.
   - Set `fase4.estimated_completion` to current time + 10 hours.
7. Update `todowrite` with Fase 4 tasks.

### Step 2: Execute skill-infrastructure
1. Load `harness/skills/skill-infrastructure/SKILL.md`.
2. Follow its instructions exactly, paying special attention to:
   - Every step that requires "AUTORIZADO" from the user.
   - Validation commands that must be run and whose output must be shown.
   - Post-change validation after each authorized change.
3. Generate all evidence files specified in skill-infrastructure's artifacts list:
   - `validacion-hyperv.json` + `.md`
   - `configuracion-red.json` + `.md`
   - `creacion-vm.json` + `.md`
   - `configuracion-caddy.json` + `.md`
   - `configuracion-ollama.json` + `.md`
   - `montaje-smb.json` + `.md`
   - `archivo-entorno.json` + `.md`
   - `servicio-systemd.json` + `.md`
   - `inicio-automatico.json` + `.md`
4. Mark skill-infrastructure as completed in `harness/PROGRESS.md`.
5. Update `todowrite`.

### Step 3: Execute skill-installer
1. Load `harness/skills/skill-installer/SKILL.md`.
2. Follow its instructions, paying special attention to:
   - Secure credential prompting (never show passwords in console).
   - Immediate unsetting of temporary environment variables.
   - Validation after each major step.
3. Generate all evidence files specified in skill-installer's artifacts list:
   - `despliegue-aplicacion.json` + `.md`
   - `base-datos.json` + `.md`
   - `credenciales-google.json` + `.md`
   - `creacion-usuarios.json` + `.md`
   - `variables-entorno.json` + `.md`
   - `activacion-servicios.json` + `.md`
   - `validacion-pruebas.json` + `.md`
   - `diagnostico.json` + `.md`
4. Ensure the diagnostic JSON at `scripts/diagnostics/diagnostic-YYYY-MM-DD.json` has no secrets.
5. Mark skill-installer as completed in `harness/PROGRESS.md`.
6. Update `todowrite`.

### Step 4: Phase Summary and Quality Gate
1. Verify all 18 evidence artifacts exist (9 from infrastructure + 8 from installer + diagnostic).
2. Run the quality gate:
   ```bash
   uv sync --frozen
   uv run ruff check . && uv run ruff format --check .
   uv run mypy app/
   uv run pytest tests/unit/ --cov=app --cov-fail-under=90
   uv run pytest tests/integration/
   uv run pip-audit
   gitleaks detect --source . --verbose
   ```
3. Present phase summary to user:
   - What was provisioned/configured.
   - What artifacts were generated.
   - Quality gate results.
   - Any warnings or notes.
4. Ask user: "Fase 4 completada. ¿Autoriza el cierre de Fase 4?" Wait for explicit "AUTORIZADO".
5. Set `fase4.status` to `completed` in `harness/PROGRESS.md`.
6. Set `fase4.completed_at` to current timestamp.
7. Execute `skill-git-safety` if user wants to commit.

### Step 5: Transition to Fase 5
1. Confirm Fase 5 preconditions are ready:
   - Application is running and accessible.
   - Both users can log in.
   - Ollama model available.
   - SMB shares accessible.
2. Present transition plan to Fase 5:
   - Acceptance testing scope.
   - 39 acceptance criteria from PRD section 33.
   - Estimated effort: 8 hours.

## Artifacts
All artifacts from both sub-skills, plus:
- `evidence/fase4/` directory with 18 files (9 from infrastructure + 8 from installer + diagnostic).
- `harness/PROGRESS.md` updated with Fase 4 completion.
- Phase summary report (included in `harness/PROGRESS.md`).

## Quality Criteria
- Both `skill-infrastructure` and `skill-installer` completed with all artifacts.
- Quality gate passes entirely:
  - Dependencies synchronized (`uv sync --frozen`).
  - Format and lint pass (`ruff`).
  - Static types pass (`mypy`).
  - Unit tests >= 90% coverage.
  - Integration tests pass.
  - Dependency security audit passes (`pip-audit`).
  - Secret scan clean (`gitleaks`).
- No secrets in any evidence file, log, or committed file.
- VM accessible via SSH and HTTPS.
- Application health endpoint responds.
- Both user accounts exist with Argon2id hashes.

## Edge Cases
- **skill-infrastructure requires user absent during authorization steps:** Pause and resume when user returns. Do not execute infrastructure changes without authorization.
- **skill-infrastructure fails mid-execution:** Before retrying, validate the failed step's partial state. Some commands are idempotent (directory creation, service files), others are not (VM creation). Adjust accordingly.
- **PostgreSQL not reachable from VM:** The PostgreSQL server may be on a different subnet. Validate connectivity from host first, then from VM. May require firewall rule or routing adjustment (needs authorization).
- **Google credentials fail:** Test credentials independently with a simple API call. If they fail, ask user to verify the JSON file and that the service account has editor access to the spreadsheet.
- **Quality gate fails:** Fix issues before closing the phase. All quality gate steps must pass.

## References
- PRD sections: Full Fase 4 scope.
- `skill-infrastructure` — Phase 4, step 1.
- `skill-installer` — Phase 4, step 2.
- `skill-quality-gate` — Pre-commit validation.
- `skill-git-safety` — Pre-commit secret scan and diff summary.
- `skill-fase5-aceptacion` — Next phase.
