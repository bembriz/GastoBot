# Checklist — skill-fase4-instalador

## Pre-ejecución
- [ ] Fase 3 completed in `harness/PROGRESS.md`.
- [ ] Current branch is `arnes`.
- [ ] `scripts/install-gastos-ia.ps1` exists.
- [ ] All Fase 3 evidence artifacts present in `harness/evidence/fase3/`.
- [ ] User confirmed available for infrastructure authorization prompts.
- [ ] Windows Server host accessible.
- [ ] Google credentials and SMB credentials available (user has them).

## Ejecución — skill-infrastructure
- [ ] C1: Load `skill-infrastructure/SKILL.md`.
- [ ] C2: Execute Hyper-V validation (get "AUTORIZADO" from user).
- [ ] C3: Create virtual switch (get "AUTORIZADO" from user).
- [ ] C4: Create VHDX and VM directory (get "AUTORIZADO" from user).
- [ ] C5: Create VM with 16 GB RAM, 4 vCPU (get "AUTORIZADO" from user).
- [ ] C6: Validate network and configure static IP 192.168.100.75 (get "AUTORIZADO" from user).
- [ ] C7: Install Ubuntu Server LTS unattended.
- [ ] C8: Validate SSH access to VM.
- [ ] C9: Install and configure Caddy for gastos.local HTTPS.
- [ ] C10: Generate cert trust script (get "AUTORIZADO" from user).
- [ ] C11: Install Ollama and pull qwen3-vl:4b.
- [ ] C12: Mount SMB shares via CIFS (get "AUTORIZADO" for fstab entries).
- [ ] C13: Create /etc/gastos-ia/gastos-ia.env (0600, root:root).
- [ ] C14: Create systemd gastos-ia.service with EnvironmentFile.
- [ ] C15: Configure VM auto-start (get "AUTORIZADO" from user).
- [ ] C16: Verify all 9 infrastructure evidence files generated.

## Ejecución — skill-installer
- [ ] C17: Load `skill-installer/SKILL.md`.
- [ ] C18: Run pre-flight checks on host.
- [ ] C19: Install Python, uv, psql on VM.
- [ ] C20: Deploy application to /opt/gastos-ia via git clone.
- [ ] C21: Run uv sync --frozen.
- [ ] C22: **[SECURE PROMPT]** Create database gastos_ia and user gastos_app.
- [ ] C23: Initialize all 9 tables.
- [ ] C24: **[SECURE PROMPT]** Copy Google service account JSON (outside repo, 0600).
- [ ] C25: Validate Google Sheets API connectivity.
- [ ] C26: **[SECURE PROMPT]** Create Ruben and Esme with Argon2id hashes.
- [ ] C27: Unset temporary password environment variables.
- [ ] C28: Populate /etc/gastos-ia/gastos-ia.env with all values.
- [ ] C29: **[SECURE PROMPT]** Configure SMB credentials.
- [ ] C30: Start gastos-ia.service and verify status.
- [ ] C31: Run tests, lint, and type checks.
- [ ] C32: Generate diagnostic JSON (no secrets).
- [ ] C33: Verify all 8 installer evidence files generated.

## Post-ejecución
- [ ] C34: All 18 evidence files exist in `harness/evidence/fase4/`.
- [ ] C35: Quality gate passes (uv sync, ruff, mypy, pytest, pip-audit, gitleaks).
- [ ] C36: Phase summary presented to user with "¿Autoriza el cierre de Fase 4?"
- [ ] C37: User explicitly responds "AUTORIZADO".
- [ ] C38: `harness/PROGRESS.md` updated: fase4 = completed with timestamp.
- [ ] C39: `todowrite` updated with Fase 4 completion.
- [ ] C40: No secrets in any file, output, or evidence.
