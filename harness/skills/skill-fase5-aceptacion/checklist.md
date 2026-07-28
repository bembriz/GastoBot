# Checklist — skill-fase5-aceptacion

## Pre-ejecución
- [ ] Fase 4 completed in `harness/PROGRESS.md`.
- [ ] Application running and accessible at `https://gastos.local`.
- [ ] Ruben and Esme accounts exist and passwords work.
- [ ] `ejemplos/` directory has at least 10 test images.
- [ ] Google Sheets spreadsheet available for tests.

## Ejecución — Test Skills
- [ ] C1: `skill-unit-tests` executed, >= 90% coverage.
- [ ] C2: `skill-integration-tests` executed, all pass.
- [ ] C3: `skill-e2e-tests` executed (Playwright), all flows pass.
- [ ] C4: `skill-uat-instructions` executed, operational manual generated.

## Ejecución — Acceptance Criteria (39 items)

### Infrastructure & Access (C1-C2)
- [ ] C5: Criterion 1 — VM and services auto-start on host boot.
- [ ] C6: Criterion 2 — Page accessible from both client computers.

### Authentication (C3-C4)
- [ ] C7: Criterion 3 — Ruben can log in (force password change).
- [ ] C8: Criterion 4 — Roles enforced (admin vs standard).

### Image Detection (C5-C7)
- [ ] C9: Criterion 5 — Folder determines owner (Ruben/Esme).
- [ ] C10: Criterion 6 — Stable images detected (DETECTADO → ESPERANDO → EN_COLA).
- [ ] C11: Criterion 7 — Temporary SMB lock tolerated, retried.

### FIFO Queue (C8-C12)
- [ ] C12: Criterion 8 — Validated images enter FIFO queue.
- [ ] C13: Criterion 9 — Only one ANALIZANDO at a time.
- [ ] C14: Criterion 10 — Second image stays EN_COLA until first finishes.
- [ ] C15: Criterion 11 — FIFO order matches enqueued_at + record_id.
- [ ] C16: Criterion 12 — Queue survives kill and full reboot.

### Interface (C13-C15)
- [ ] C17: Criterion 13 — Image displayed with zoom/rotate.
- [ ] C18: Criterion 14 — HTMX Polling updates states (3s, no F5).
- [ ] C19: Criterion 15 — Roles affect polling visibility.

### Extraction (C16-C17)
- [ ] C20: Criterion 16 — 5 fields extracted (date, amount, desc, bank, type).
- [ ] C21: Criterion 17 — Confidence warnings at < 0.70.

### Form (C18-C23)
- [ ] C22: Criterion 18 — Date editable.
- [ ] C23: Criterion 19 — Precio unitario and Total sync (Cantidad = 1).
- [ ] C24: Criterion 20 — Categoria and Cuenta are dropdowns.
- [ ] C25: Criterion 21 — Consecutive avoids collisions.
- [ ] C26: Criterion 22 — Final description auto-generated (GROUP-DATE-N-DESC).
- [ ] C27: Criterion 23 — Submit button blocked if required fields missing.

### Duplicates (C24-C25)
- [ ] C28: Criterion 24 — Exact duplicates (SHA-256) blocked.
- [ ] C29: Criterion 25 — Probable duplicates show warning.

### Google Sheets (C26-C30)
- [ ] C30: Criterion 26 — Record to correct monthly pestaña.
- [ ] C31: Criterion 27 — New pestañas created with 16 headers.
- [ ] C32: Criterion 28 — Image moved to procesados/ only after submit.
- [ ] C33: Criterion 29 — History query and update works.
- [ ] C34: Criterion 30 — Month change moves record between pestañas.

### Offline (C31)
- [ ] C35: Criterion 31 — Offline operation preserves expense (PENDIENTE_DE_ENVIO).
- [ ] C36: Criterion 31b — Expense sendable after reconnection.

### Logs & Security (C32, C34-C38)
- [ ] C37: Criterion 32 — JSONL logs contain no secrets.
- [ ] C38: Criterion 34 — No paid AI API used (only local Ollama).
- [ ] C39: Criterion 35 — Repository uses uv exclusively.
- [ ] C40: Criterion 36 — No secrets versioned (gitleaks clean).
- [ ] C41: Criterion 37 — Passwords via environment variables.
- [ ] C42: Criterion 38 — Only Argon2id hashes in PostgreSQL.

### Reliability (C33)
- [ ] C43: Criterion 33 — Restart doesn't lose state.

### Process (C39)
- [ ] C44: Criterion 39 — No unauthorized commits or pushes (confirmed).

## Ejecución — Advanced Tests

### Concurrency & FIFO
- [ ] C45: Deploy 5 images simultaneously.
- [ ] C46: Verify exactly 1 ANALIZANDO at any moment.
- [ ] C47: Verify FIFO order preserved.
- [ ] C48: Verify two users copying simultaneously handled correctly.

### Recovery
- [ ] C49: Kill worker mid-processing; verify ANALIZANDO → EN_COLA.
- [ ] C50: Full reboot mid-processing; verify queue preserved.
- [ ] C51: PostgreSQL restart; verify reconnection.

### SMB Lock
- [ ] C52: Hold file lock; verify monitor retries silently.
- [ ] C53: Release lock; verify processing continues normally.

### HTMX Polling Dual Browser
- [ ] C54: Browser A (Ruben) and Browser B (Esme) open simultaneously.
- [ ] C55: Ruben's image only appears in Browser A.
- [ ] C56: Esme's image appears in both Browser B and Browser A (admin view).
- [ ] C57: Both browsers update via polling without F5.

### Offline
- [ ] C58: Disconnect internet; verify local processing works.
- [ ] C59: Verify PENDIENTE_DE_ENVIO state.
- [ ] C60: Reconnect; verify submission works.
- [ ] C61: Multiple offline images preserved.

### Restart Resilience
- [ ] C62: Full host reboot; verify all services auto-start.
- [ ] C63: All pending records preserved after reboot.
- [ ] C64: SMB mounts reconnect automatically.
- [ ] C65: Rapid restarts (3x) don't corrupt data.

### Real Tickets
- [ ] C66: Process >= 10 real images from ejemplos/.
- [ ] C67: Record extraction accuracy (date, amount, bank, type).
- [ ] C68: All real images submitted to Sheets successfully.
- [ ] C69: Manual corrections applied and persisted.

## Post-ejecución
- [ ] C70: All 39 acceptance criteria pass or have documented exceptions.
- [ ] C71: All evidence JSON + MD files exist in `harness/evidence/fase5/`.
- [ ] C72: Operational manual at `docs/manual-operativo.md` complete.
- [ ] C73: Quality gate passes (ruff, mypy, pytest, pip-audit, gitleaks).
- [ ] C74: Phase summary with criteria table presented to user.
- [ ] C75: User authorizes Fase 5 closure → "AUTORIZADO".
- [ ] C76: `harness/PROGRESS.md` updated: fase5 = completed.
- [ ] C77: No secrets in any file, output, or evidence.
