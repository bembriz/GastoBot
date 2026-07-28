# Checklist — skill-installer

## Pre-ejecución
- [ ] `skill-infrastructure` completed and all artifacts exist in `harness/evidence/fase4/`.
- [ ] VM reachable via SSH at `gastos-admin@192.168.100.75`.
- [ ] `install-gastos-ia.ps1` script exists at `scripts/install-gastos-ia.ps1`.
- [ ] Git repository accessible (local or remote).
- [ ] PostgreSQL admin credentials available.
- [ ] Google service account JSON file available.
- [ ] Google spreadsheet ID known.
- [ ] SMB credentials for `\\SERVIDOR\GastosIA` known.

## Ejecución

### Pre-flight Checks
- [ ] C1: Confirm running as Administrator (PowerShell admin check).
- [ ] C2: Validate Hyper-V module available.
- [ ] C3: Confirm disk space on `D:\`.
- [ ] C4: Ping `192.168.100.75` successfully.
- [ ] C5: SSH connection to VM works.

### VM Software Installation
- [ ] C6: `python3` installed on VM (>= 3.10).
- [ ] C7: `uv` installed and available in PATH.
- [ ] C8: `psql` client installed on VM.
- [ ] C9: Validate versions with `python3 --version`, `uv --version`, `psql --version`.

### Application Deployment
- [ ] C10: Repository cloned/copied to `/opt/gastos-ia/`.
- [ ] C11: Correct branch checked out (arnes or feature branch).
- [ ] C12: `uv sync --frozen` completes without errors.
- [ ] C13: FastAPI import test passes.

### Database Setup
- [ ] C14: **[SECURE PROMPT]** PostgreSQL admin password obtained via secure input.
- [ ] C15: Database `gastos_ia` created.
- [ ] C16: User `gastos_app` created with secure password.
- [ ] C17: `gastos_app` has ALL PRIVILEGES on `gastos_ia`.
- [ ] C18: Connection test as `gastos_app` succeeds.
- [ ] C19: Admin password NOT in any log, evidence, or output.

### Table Initialization
- [ ] C20: Schema migration/initialization run successfully.
- [ ] C21: All 9 tables confirmed with `\dt`: `users`, `expense_records`, `image_files`, `extraction_runs`, `processing_queue`, `catalog_cache`, `sheet_sync`, `audit_events`, `system_settings`.

### Google Sheets Setup
- [ ] C22: **[SECURE PROMPT]** Google service account JSON path obtained (not file contents).
- [ ] C23: JSON copied to `/etc/gastos-ia/google-service-account.json`.
- [ ] C24: File permissions are `0600 root:root`.
- [ ] C25: Spreadsheet ID obtained and set.
- [ ] C26: Google API connectivity test passes.

### User Creation
- [ ] C27: **[SECURE PROMPT]** Ruben's initial password obtained via hidden input.
- [ ] C28: **[SECURE PROMPT]** Esme's initial password obtained via hidden input.
- [ ] C29: Session secret generated with `openssl rand -hex 32`.
- [ ] C30: User creation script run with temporary env vars.
- [ ] C31: Argon2id hashes confirmed in PostgreSQL (`$argon2id$` prefix).
- [ ] C32: Temporary `GASTOSIA_*_INITIAL_PASSWORD` variables explicitly unset.
- [ ] C33: No passwords in bash history, logs, or evidence.

### Environment File
- [ ] C34: `/etc/gastos-ia/gastos-ia.env` populated with all values.
- [ ] C35: No empty values (`grep -c '=$'` returns 0).
- [ ] C36: Permissions still `0600 root:root`.

### SMB Credentials
- [ ] C37: **[SECURE PROMPT]** SMB credentials obtained.
- [ ] C38: `/etc/gastos-ia/smb-credentials` populated.
- [ ] C39: Shares remounted and accessible.

### Service Activation
- [ ] C40: `sudo systemctl start gastos-ia` succeeds.
- [ ] C41: `sudo systemctl status gastos-ia` shows `active (running)`.
- [ ] C42: Health endpoint `https://gastos.local/health` responds OK.
- [ ] C43: Login page `https://gastos.local/login` loads.

### Validation
- [ ] C44: Tests pass: `uv run pytest tests/ --tb=short`.
- [ ] C45: Lint passes: `uv run ruff check .`.
- [ ] C46: Type check passes: `uv run mypy app/`.
- [ ] C47: Ollama API responds: `curl http://localhost:11434/api/tags`.

### Diagnostics
- [ ] C48: Diagnostic JSON generated at `scripts/diagnostics/diagnostic-YYYY-MM-DD.json`.
- [ ] C49: Diagnostic contains: VM specs, service statuses, DB state, model info, disk usage.
- [ ] C50: Diagnostic does NOT contain any passwords, keys, tokens, or credentials.
- [ ] C51: Diagnostic summary presented to user.

## Post-ejecución
- [ ] C52: All evidence JSON + MD files exist in `harness/evidence/fase4/`.
- [ ] C53: `gastos-ia.service` set to auto-restart (`Restart=always`).
- [ ] C54: VM auto-start confirmed with host.
- [ ] C55: HTTPS accessible at `https://gastos.local` from authorized clients.
- [ ] C56: Ruben can log in (first login should force password change).
- [ ] C57: Esme can log in (first login should force password change).
- [ ] C58: No secrets, passwords, or credentials in any generated file or evidence.
- [ ] C59: Gitleaks scan passes on the repository.
