# Skill: skill-installer

## Identity
As the deployment engineer for Gastos IA, you execute the automated PowerShell installer (`install-gastos-ia.ps1`) that deploys the application, creates the database, initializes users, and generates diagnostics. You handle secure credential prompting and ensure the installer executes each of the 19 steps from PRD section 23.

## Context
This skill runs the automated installer that transforms a provisioned Ubuntu VM (from `skill-infrastructure`) into a running Gastos IA application. It deploys code, installs Python dependencies via `uv`, creates the PostgreSQL database and user, initializes tables, creates user accounts with Argon2id hashes, configures Google Sheets credentials, fills environment variables, activates services, and generates a diagnostic JSON report.

This is a **Fase 4** skill. It runs after `skill-infrastructure` and is the last skill of Fase 4.

**Key PRD sections:** 23 (Instalación automatizada), 23.1 (Datos humanos), 24 (Inicio automático), 11 (Campos visibles), 18 (PostgreSQL), 19 (Variables de entorno).

## Preconditions
- `skill-infrastructure` completed successfully:
  - VM running, SSH accessible at 192.168.100.75.
  - Caddy running, HTTPS at https://gastos.local.
  - Ollama running, `qwen3-vl:4b` model pulled.
  - SMB shares mounted at `/mnt/smb/Ruben` and `/mnt/smb/Esme`.
  - Environment directory `/etc/gastos-ia/` exists.
  - Systemd service `gastos-ia.service` created but not started.
- `install-gastos-ia.ps1` script exists at `scripts/install-gastos-ia.ps1`.
- Git repository accessible (either cloned or local).
- PostgreSQL admin credentials known to user.
- Google service account JSON file available.
- Google spreadsheet ID known.

## Execution

### Step 1: Validate installer script exists
1. Confirm `scripts/install-gastos-ia.ps1` exists and is a well-formed PowerShell script.
2. Review the script against the 19 steps from PRD section 23.
3. Confirm all secure credential prompts use `Read-Host -AsSecureString` or equivalent.
4. Confirm no hardcoded secrets or credentials.

### Step 2: Run pre-flight checks (Steps 1-3 of installer)
Execute the pre-validation section of the installer:
1. **Admin rights check:** Confirm running as Administrator.
2. **Hyper-V capability:** Validate Hyper-V module is available.
3. **Disk space:** Confirm `D:\Hyper-V\VirtualMachines\GastosIA` has sufficient space.
4. **Network reachability:** Ping `192.168.100.75` to confirm VM is up.
5. **SSH access:** Test SSH connection to `gastos-admin@192.168.100.75`.
6. Report all results. If any pre-check fails, fix before proceeding.

### Step 3: Post-install SSH setup (Step 4 of installer)
1. If not already done, configure SSH key-based authentication for smoother deployment.
2. Copy SSH public key to VM: `ssh-copy-id gastos-admin@192.168.100.75` (or manual setup).
3. Validate by running a non-interactive SSH command:
   ```bash
   ssh gastos-admin@192.168.100.75 'uname -a'
   ```

### Step 4: Install Python, uv, and PostgreSQL client (Steps 5-6 of installer)
Execute on the VM via SSH:
1. Update apt: `sudo apt update && sudo apt upgrade -y`
2. Install Python:
   ```bash
   sudo apt install -y python3 python3-pip python3-venv
   ```
3. Install `uv`:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   Or via pipx: `sudo apt install -y pipx && pipx install uv`
4. Install PostgreSQL client:
   ```bash
   sudo apt install -y postgresql-client
   ```
5. Validate:
   ```bash
   python3 --version
   uv --version
   psql --version
   ```

### Step 5: Deploy application from git (Steps 7-8 of installer)
1. Clone or copy repository to `/opt/gastos-ia/`:
   ```bash
   sudo mkdir -p /opt/gastos-ia
   sudo chown gastos-admin:gastos-admin /opt/gastos-ia
   git clone <repo-url> /opt/gastos-ia
   # OR: scp -r ./gastos-ia/ gastos-admin@192.168.100.75:/opt/gastos-ia/
   ```
2. Checkout the correct branch (e.g., `arnes`).
3. Install Python dependencies:
   ```bash
   cd /opt/gastos-ia
   uv sync --frozen
   ```
4. Validate: `uv run python -c "import fastapi; print('FastAPI OK')"`

### Step 6: Create database and user (Steps 9-10 of installer)
1. **Prompt user securely for PostgreSQL admin password.**
2. Execute on VM against existing PostgreSQL server:
   ```sql
   CREATE DATABASE gastos_ia;
   CREATE USER gastos_app WITH PASSWORD '<app_password>';
   GRANT ALL PRIVILEGES ON DATABASE gastos_ia TO gastos_app;
   ```
3. Validate connection as `gastos_app`:
   ```bash
   PGPASSWORD='<app_password>' psql -h <host> -p 5432 -U gastos_app -d gastos_ia -c "SELECT 1;"
   ```
4. **Do not log or store the passwords.**

### Step 7: Initialize tables (Step 11 of installer)
1. Run migrations or schema initialization:
   ```bash
   cd /opt/gastos-ia
   uv run python -m app.database.init
   ```
2. Validate all tables exist:
   ```sql
   \dt
   ```
   Expected tables: `users`, `expense_records`, `image_files`, `extraction_runs`, `processing_queue`, `catalog_cache`, `sheet_sync`, `audit_events`, `system_settings`.

### Step 8: Configure Google credentials (Step 12 of installer)
1. **Prompt user for path to Google service account JSON file.**
2. Copy the JSON to a secure location outside the repo:
   ```bash
   sudo mkdir -p /etc/gastos-ia
   sudo cp <source-json> /etc/gastos-ia/google-service-account.json
   sudo chown root:root /etc/gastos-ia/google-service-account.json
   sudo chmod 600 /etc/gastos-ia/google-service-account.json
   ```
3. **Prompt user for Google spreadsheet ID.**
4. Add to environment: `GASTOSIA_GOOGLE_SPREADSHEET_ID=<id>`
5. Validate the credentials work:
   ```bash
   cd /opt/gastos-ia
   uv run python -c "from app.sheets.client import test_connection; test_connection()"
   ```

### Step 9: Create user accounts (Step 13 of installer)
1. **Prompt user securely for Ruben's initial password (hidden).**
2. **Prompt user securely for Esme's initial password (hidden).**
3. **Prompt user for or generate a session secret:**
   ```bash
   openssl rand -hex 32  # suggested method
   ```
4. Set temporary environment variables and run user creation:
   ```bash
   export GASTOSIA_RUBEN_INITIAL_PASSWORD='<password>'
   export GASTOSIA_ESME_INITIAL_PASSWORD='<password>'
   cd /opt/gastos-ia
   uv run python -m app.auth.create_users
   ```
5. Validate: passwords are hashed with Argon2id in PostgreSQL. Verify with:
   ```sql
   SELECT username, password_hash LIKE '$argon2id$%' FROM users;
   ```
6. **Unset the temporary password environment variables immediately after.**
7. Confirm no passwords in bash history, logs, or environment.

### Step 10: Fill environment variables (Step 14 of installer)
1. Populate `/etc/gastos-ia/gastos-ia.env` with actual values from previous steps:
   ```ini
   GASTOSIA_APP_ENV=production
   GASTOSIA_DATABASE_HOST=<host>
   GASTOSIA_DATABASE_PORT=5432
   GASTOSIA_DATABASE_NAME=gastos_ia
   GASTOSIA_DATABASE_USER=gastos_app
   GASTOSIA_DATABASE_PASSWORD=<app_password>
   GASTOSIA_SESSION_SECRET=<generated_hex>
   GASTOSIA_SMB_USERNAME=<smb_user>
   GASTOSIA_SMB_PASSWORD=<smb_pass>
   GASTOSIA_GOOGLE_CREDENTIALS_PATH=/etc/gastos-ia/google-service-account.json
   GASTOSIA_GOOGLE_SPREADSHEET_ID=<spreadsheet_id>
   ```
2. Confirm permissions still `0600 root:root`.
3. Validate all variables are populated (none empty or placeholder):
   ```bash
   grep -c '=$' /etc/gastos-ia/gastos-ia.env   # Should be 0 (no empty values)
   ```

### Step 11: Fill SMB credentials (Step 15 of installer)
1. **Prompt user for SMB username and password.**
2. Update `/etc/gastos-ia/smb-credentials`:
   ```text
   username=<smb_user>
   password=<smb_pass>
   ```
3. Confirm `0600` permissions.
4. Remount shares if needed:
   ```bash
   sudo mount -a
   ```

### Step 12: Activate services (Step 16 of installer)
1. Start the gastos-ia service:
   ```bash
   sudo systemctl start gastos-ia
   ```
2. Check status:
   ```bash
   sudo systemctl status gastos-ia
   ```
3. Check application health:
   ```bash
   curl -k https://gastos.local/health
   ```
4. Review logs if service fails:
   ```bash
   sudo journalctl -u gastos-ia -n 50 --no-pager
   ```

### Step 13: Configure VM auto-start (Step 17 of installer)
1. Confirm VM auto-start was already configured in `skill-infrastructure`.
2. Verify from host:
   ```powershell
   Get-VM -Name "GastosIA" | Format-List Name, AutomaticStartAction, AutomaticStopAction
   ```

### Step 14: Run validation tests (Step 18 of installer)
1. Run basic smoke tests from the host:
   ```bash
   # SSH into VM and run
   cd /opt/gastos-ia
   uv run pytest tests/ --tb=short -x
   ```
2. Check that the quality gate passes:
   ```bash
   uv run ruff check . && uv run ruff format --check .
   uv run mypy app/
   ```
3. Verify the web interface loads:
   ```bash
   curl -k -s https://gastos.local/login | head -20
   ```
4. Verify Ollama is responsive:
   ```bash
   curl http://localhost:11434/api/tags
   ```

### Step 15: Generate diagnostic JSON (Step 19 of installer)
1. Run the diagnostics script:
   ```bash
   cd /opt/gastos-ia
   uv run python -m scripts.diagnostics.generate
   ```
2. Save output to `scripts/diagnostics/diagnostic-YYYY-MM-DD.json`.
3. **The diagnostic JSON must NOT contain any secrets, passwords, tokens, or sensitive values.**
4. Validate the diagnostic:
   - Contains: VM specs, service statuses, DB connection status, model info, disk usage.
   - Does NOT contain: passwords, API keys, SMB credentials, Google account data, session secrets.
5. Present diagnostic summary to user.

## Authorization
This skill does not require the same GATE mechanism as `skill-infrastructure` because it operates within an already-provisioned VM. However:
- **Credential prompts must use secure input** (`Read-Host -AsSecureString` in PowerShell, hidden prompts in Python).
- **No secrets may be written to logs, console output, or evidence files.**
- **Temporary environment variables that hold passwords must be unset immediately after use.**

## Artifacts
- `evidence/fase4/despliegue-aplicacion.json` + `.md`
- `evidence/fase4/base-datos.json` + `.md`
- `evidence/fase4/credenciales-google.json` + `.md`
- `evidence/fase4/creacion-usuarios.json` + `.md`
- `evidence/fase4/variables-entorno.json` + `.md`
- `evidence/fase4/activacion-servicios.json` + `.md`
- `evidence/fase4/validacion-pruebas.json` + `.md`
- `evidence/fase4/diagnostico.json` + `.md`
- `scripts/diagnostics/diagnostic-YYYY-MM-DD.json` (no secrets)
- `/etc/gastos-ia/gastos-ia.env` (populated, 0600)

Each JSON artifact follows `harness/config/schemas/evidence.schema.json`.
Each MD artifact follows `harness/config/schemas/evidence-markdown.schema.md`.

## Quality Criteria
- PostgreSQL database `gastos_ia` created with user `gastos_app`.
- All 9 tables initialized.
- Google service account JSON placed outside repo with `0600` permissions.
- Google Sheets API connectivity validated.
- User accounts for Ruben (admin) and Esme (standard) created with Argon2id hashes.
- `GASTOSIA_RUBEN_INITIAL_PASSWORD` and `GASTOSIA_ESME_INITIAL_PASSWORD` unset after use.
- Environment file fully populated with no empty values.
- `gastos-ia.service` started and responding at `https://gastos.local`.
- Quality gate passes (lint, types, tests).
- Diagnostic JSON generated with no secrets.
- No credentials or secrets in any evidence or log file.

## Edge Cases
- **Partial install recovery:** If a step fails, the installer should be idempotent. Check if resources already exist before creating. For example: `CREATE DATABASE IF NOT EXISTS` logic, or `CREATE USER IF NOT EXISTS`.
- **Hyper-V service restart required:** If VM won't start, check Hyper-V services on host. Run `Restart-Service vmms` if needed.
- **Ubuntu download failure:** Retry with `--retry` flag or download from a mirror. Verify checksum.
- **Password validation:** Ensure passwords meet minimum length (8 chars) and complexity (mix of character types). Reject and re-prompt if insufficient.
- **Existing VM conflict:** If a VM named `GastosIA` already exists but is from a failed previous installation, offer to remove it or rename it.
- **uv not found in PATH:** After installing uv, source shell profile or use full path `$HOME/.local/bin/uv`.
- **PostgreSQL connection refused:** Check pg_hba.conf on server, verify `gastos_app` has connect privileges, check firewall rules.
- **Database already exists:** If `gastos_ia` DB exists from a previous install, offer to drop and recreate (with user confirmation) or run migrations on existing DB.
- **Google credentials invalid:** Test with a simple API call before populating environment file. Prompt user to re-provide valid credentials.

## References
- PRD sections: 23 (Instalación automatizada), 23.1 (Datos humanos), 24 (Inicio automático), 18 (PostgreSQL), 19 (Variables de entorno), 20 (Credencial de Google).
- `install-gastos-ia.ps1` at `scripts/install-gastos-ia.ps1`.
- `skill-infrastructure` (prerequisite).
- `skill-fase4-instalador` (orchestrator).
- `skill-quality-gate` (pre-commit validation).
- `skill-git-safety` (pre-commit secret scan).
