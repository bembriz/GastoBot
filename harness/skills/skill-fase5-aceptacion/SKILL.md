# Skill: skill-fase5-aceptacion

## Identity
As the Fase 5 acceptance tester for Gastos IA, you verify that the complete application meets all 39 acceptance criteria from PRD section 33. You coordinate functional tests, concurrency tests, recovery tests, offline operation tests, and real ticket processing. You invoke `skill-unit-tests`, `skill-integration-tests`, `skill-e2e-tests`, and `skill-uat-instructions` as part of this phase, and generate the operational manual.

## Context
Fase 5 — "Aceptación" — is the final phase before the MVP is considered delivered. It validates that every feature works end-to-end, the system is reliable under adverse conditions, and the operational manual is complete. All 39 acceptance criteria from PRD section 33 must be verified.

This phase invokes the transversal testing skills (unit, integration, e2e, UAT) and performs additional manual/automated checks for concurrency, FIFO ordering, recovery, SMB lock handling, HTMX polling, offline operation, and restart resilience.

**Key PRD sections:** 33 (Criterios de aceptación, 39 items), 31 (Requisitos no funcionales), 9 (Flujo funcional), 8 (Carpetas/SMB), 10 (Interfaz web), 17 (Estados).

## Preconditions
- Fase 4 (`skill-fase4-instalador`) must be `completed`.
- Application running and accessible at `https://gastos.local`.
- Both users (Ruben and Esme) can log in.
- PostgreSQL `gastos_ia` database operational.
- Ollama with `qwen3-vl:4b` model available and responsive.
- SMB shares accessible at `/mnt/smb/Ruben` and `/mnt/smb/Esme`.
- Test images available in `ejemplos/` directory.

## Execution

### Step 1: Invoke skill-unit-tests
1. Load and execute `harness/skills/skill-unit-tests/SKILL.md`.
2. Confirm >= 90% code coverage.
3. Verify all unit tests pass.
4. Coverage must cover: database operations, authentication logic, FIFO queue logic, image processing, Sheet sync logic, catalog CRUD, description/consecutive generation.
5. Generate evidence:
   - `evidence/fase5/pruebas-unitarias.json` + `.md`

### Step 2: Invoke skill-integration-tests
1. Load and execute `harness/skills/skill-integration-tests/SKILL.md`.
2. Use real images from `ejemplos/` directory.
3. Test end-to-end pipeline: image detection → queue → Ollama processing → extraction → review.
4. Test database integration: connections, transactions, rollbacks, locks.
5. Test Google Sheets integration: read/write, sync, pestaña creation.
6. Test SMB file operations: detection, stability check, move.
7. Generate evidence:
   - `evidence/fase5/pruebas-integracion.json` + `.md`

### Step 3: Invoke skill-e2e-tests
1. Load and execute `harness/skills/skill-e2e-tests/SKILL.md`.
2. Run Playwright automated flows:
   - Login → view pending → review → submit → logout (Ruben).
   - Login → view own pending → review → submit → logout (Esme).
   - Admin catalog CRUD flow.
   - History search and update flow.
3. Generate evidence:
   - `evidence/fase5/pruebas-e2e.json` + `.md`

### Step 4: Functional Acceptance Tests (Criteria 1-8, 13-39)
Verify each of these acceptance criteria:

#### Criterion 1 — VM and services auto-start
- Reboot the host (or simulate with `sudo reboot` in VM).
- Verify: Hyper-V auto-starts the VM, Ubuntu boots, all services start.
- Verify: `systemctl is-active gastos-ia caddy ollama` = active.
- Verify: `curl -k https://gastos.local/health` responds.

#### Criterion 2 — Page accessible from both computers
- From two different client machines on the local network:
  - Browse to `https://gastos.local`.
  - Confirm login page loads.
  - (May need cert trust or hosts file entries.)

#### Criterion 3 — Ruben and Esme can log in
- Log in as Ruben with initial password.
- First login must force password change.
- Log in as Esme with initial password.
- First login must force password change.
- After password change, log in again successfully.

#### Criterion 4 — Roles work correctly
- As Ruben (admin): can access catalogs, user management, all expense records.
- As Esme (standard): can only see own records, no catalog or user access.
- Test by attempting direct URL access to admin-only routes; should be rejected.

#### Criterion 5 — Folders assign correct owner
- Copy an image to `\\SERVIDOR\GastosIA\Ruben\pendientes\`.
- Verify the detected record shows owner = "Ruben".
- Copy an image to `\\SERVIDOR\GastosIA\Esme\pendientes\`.
- Verify the detected record shows owner = "Esme".

#### Criterion 6 — Stable images detected
- Copy an image; wait for detection.
- Verify the image goes through: DETECTADO → ESPERANDO_ARCHIVO_ESTABLE → EN_COLA.
- A partially-written file (simulated) should remain in ESPERANDO_ARCHIVO_ESTABLE.

#### Criterion 7 — Temporary SMB lock doesn't cause error
- Simulate a temporary file lock on a new image.
- Verify the monitor captures the lock exception, keeps the file in ESPERANDO_ARCHIVO_ESTABLE, and retries in the next 5-second cycle.
- Verify the file is NOT moved to errores/ and NOT marked as ERROR_PROCESAMIENTO.

#### Criterion 8 — Validated images enter FIFO queue
- Drop 3 images in `pendientes/`.
- Verify all 3 enter the queue with status EN_COLA.
- Verify `enqueued_at` timestamps are in order of detection.
- Verify they are in `processing_queue` table.

#### Criterion 9 — Only one ANALIZANDO at a time
- While the first image is processing, verify no other image can enter ANALIZANDO.
- Use concurrent requests/logs to confirm only one Ollama request is active.

#### Criterion 10 — Second image stays EN_COLA
- Verify that while image #1 is ANALIZANDO, image #2 remains EN_COLA.
- Only after image #1 finishes (LISTO_PARA_REVISION or ERROR_PROCESAMIENTO) does image #2 move to ANALIZANDO.

#### Criterion 11 — FIFO order preserved
- After all images processed, verify processing order matches `enqueued_at` + `record_id` ordering.
- Check audit events for confirmation.

#### Criterion 12 — Queue survives restart
- Kill the worker process mid-processing (simulating crash).
- Verify the ANALIZANDO record is recovered to EN_COLA on restart.
- Verify no duplicate records created.
- Kill the entire VM and restart; verify queue is preserved and processing resumes from where it left off.

#### Criterion 13 — Interface shows image
- Open any expense record in review mode.
- Verify the ticket image is displayed (thumbnail + full view).
- Verify zoom, rotate, fit-to-width controls work.

#### Criterion 14 — HTMX Polling updates states
- Open the pending list in a browser.
- Copy a new image to `pendientes/`.
- Verify within 3 seconds the new record appears without pressing F5.
- Verify state transitions (EN_COLA → ANALIZANDO → LISTO_PARA_REVISION) are reflected automatically.
- Open two browser windows (or two browsers) and verify both update independently via polling.

#### Criterion 15 — Roles affect polling visibility
- As Esme, verify only her records update via polling.
- As Ruben, verify all records update via polling.

#### Criterion 16 — Model extracts 5 required fields
- Process a batch of test images from `ejemplos/`.
- Verify: `transaction_date`, `amount`, `ticket_description`, `bank`, `transaction_type` are all present in extraction.
- Verify at least 90% accuracy on dates and 95% on amounts (from Fase 0 benchmark).

#### Criterion 17 — Confidence generates warnings
- If any confidence score is < 0.70, the field should be highlighted in the UI.
- If 0.70–0.89, a warning should appear.
- If >= 0.90, normal display.

#### Criterion 18 — Date is editable
- Open a record in review mode.
- Change the date field.
- Save; verify the new date is persisted.

#### Criterion 19 — Precio unitario and Total sync
- Change "Precio unitario" in the form.
- Verify "Total" updates to the same value (since Cantidad = 1).
- Change "Total"; verify "Precio unitario" syncs.
- Both must always be equal.

#### Criterion 20 — Categoria and Cuenta are dropdowns
- Open review form.
- Verify "Categoría" shows values from the categorías catalog.
- Verify "Cuenta" shows values from the cuentas catalog.
- Verify dropdowns are searchable/filterable.

#### Criterion 21 — Consecutive avoids collisions
- Create multiple expenses in the same group.
- Verify consecutivos increment: VAL-XXXXXX-1, VAL-XXXXXX-2, VAL-XXXXXX-3.
- Verify no gaps or collisions (with concurrency testing).

#### Criterion 22 — Final description auto-generated
- Enter group "VAL", description "GASOLINA".
- Verify final description shows as "VAL-{YYYYMMDD}-{n}-GASOLINA" (n is consecutive).
- Verify format: uppercase, normalized spaces, allowed characters only.

#### Criterion 23 — Submit button blocked if fields missing
- Open review form, leave "Categoria" empty.
- Verify "Enviar a Google Sheets" button is disabled.
- Fill all required fields; verify button becomes enabled.

#### Criterion 24 — Exact duplicates blocked
- Copy the same image twice to the same `pendientes/` folder.
- Verify the second copy is detected as DUPLICADO_EXACTO.
- Verify it is moved to `errores/duplicados/`.
- Verify no second expense record is created.

#### Criterion 25 — Probable duplicates show warning
- Create two records with same date, amount, bank, and similar description.
- Verify the second one shows a warning in the UI (DUPLICADO_PROBABLE state or similar).
- Verify user can confirm and send anyway (audited).

#### Criterion 26 — Record goes to correct monthly sheet
- Submit an expense with date in August 2026.
- Verify the record is inserted into the "Agosto-26" pestaña in Google Sheets.
- Submit an expense with date in January 2027.
- Verify record goes to "Enero-27".

#### Criterion 27 — Sheets created with 16 headers
- Submit an expense to a month that doesn't have a pestaña yet.
- Verify a new pestaña is created with exactly 16 column headers.
- Verify headers match PRD section 13.1.

#### Criterion 28 — Image moved only after send
- Submit an expense successfully.
- Verify the original image is moved from `pendientes/` to `procesados/YYYY/MM/`.
- Verify it is NOT moved before submission is confirmed.

#### Criterion 29 — History allows query and update
- Search history by date range, bank, group, user.
- Verify results match filters.
- Edit a record from history.
- Submit update; verify both PostgreSQL and Sheets are updated.

#### Criterion 30 — Month change moves record
- Edit a submitted record and change its date to a different month.
- Submit update.
- Verify the record is removed from the old pestaña and added to the new one.
- Verify `_Control` is updated accordingly.

#### Criterion 31 — Offline operation preserves expense
- Disconnect the VM from the internet (disable network interface or block outbound).
- Process an image fully: detect → queue → analyze → review.
- Verify the record reaches PENDIENTE_DE_ENVIO state.
- Reconnect internet.
- Verify the record's "Enviar" button becomes available.
- Submit; verify it goes to Google Sheets successfully.

#### Criterion 32 — JSONL logs contain no secrets
- Review `app-YYYY-MM-DD.jsonl` and `audit-YYYY-MM-DD.jsonl`.
- Verify no passwords, API keys, tokens, session secrets, or SMB credentials appear.
- Verify credit card numbers or sensitive bank data is not logged.
- Run: `gitleaks detect --source /opt/gastos-ia/logs/` (or equivalent).

#### Criterion 33 — Restart doesn't lose state
- Create records in various states: EN_COLA, ANALIZANDO, LISTO_PARA_REVISION, PENDIENTE_DE_ENVIO.
- Restart the application (`sudo systemctl restart gastos-ia`).
- Verify all records are in the correct state after restart.
- ANALIZANDO records should recover to EN_COLA if no active worker.
- EN_COLA records should remain in queue.
- LISTO_PARA_REVISION records should remain reviewable.

#### Criterion 34 — No paid AI API used
- Verify Ollama runs locally.
- Verify no outbound connections to OpenAI, Anthropic, Google AI, or similar.
- Run: `netstat -tnp | grep -E ':(443|80) ' | grep -v '192.168' | grep -v '127.0.0.1'` to check external connections.
- Verify no API keys for paid services exist in environment or config.

#### Criterion 35 — Repository uses uv
- Verify `pyproject.toml` and `uv.lock` exist.
- Verify `.python-version` is present.
- Verify no `requirements.txt`, `Pipfile`, `poetry.lock`, or `environment.yml`.
- Verify `uv sync --frozen` works.
- Verify `uv run` is used for all commands.

#### Criterion 36 — No secrets versioned
- Run `gitleaks detect --source . --verbose`.
- Verify zero findings.
- Manually check `git log -p` for any commit with passwords, tokens, or keys.
- Verify `.env.example` has no real values.
- Verify `/etc/gastos-ia/` files are outside the git repository.

#### Criterion 37 — Passwords via environment variables
- Verify all passwords, tokens, secrets enter via `os.environ.get("GASTOSIA_*")`.
- Verify no hardcoded credentials in source code.
- Verify `/etc/gastos-ia/gastos-ia.env` is loaded by systemd `EnvironmentFile`.
- Verify the file is `0600 root:root` and outside the repo.

#### Criterion 38 — Only Argon2id hashes in PostgreSQL
- Connect to PostgreSQL and check `users` table.
- Verify `password_hash` column starts with `$argon2id$`.
- Verify no plaintext passwords, MD5, SHA-1, or bcrypt hashes.
- Verify the `GASTOSIA_*_INITIAL_PASSWORD` vars do NOT appear in any table.

#### Criterion 39 — No commits or pushes without authorization
- Verify `.git/hooks/pre-commit` or similar enforces the quality gate.
- Verify the AGENTS.md rules prohibit unauthorized commits/pushes.
- This criterion is process-based; confirm with the user that no unauthorized actions occurred.

### Step 5: Concurrency and FIFO Tests
1. Deploy 5 images simultaneously to `pendientes/`.
2. Monitor the processing queue via database queries:
   ```sql
   SELECT record_id, status, enqueued_at, updated_at
   FROM processing_queue ORDER BY enqueued_at ASC, record_id ASC;
   ```
3. Verify exactly 1 record in ANALIZANDO at any moment.
4. Verify records transition ANALIZANDO → LISTO_PARA_REVISION in FIFO order.
5. Verify the second record only enters ANALIZANDO after the first finishes.
6. Test with two users copying images at the same time.
7. Document the timeline of transitions.

### Step 6: Recovery Tests (Kill and Reboot)
1. **Worker kill mid-processing:**
   - Start processing an image (wait until ANALIZANDO).
   - Kill the worker process: `sudo pkill -f "uvicorn"` (or `sudo systemctl stop gastos-ia`).
   - Verify the ANALIZANDO record transitions to EN_COLA after restart.
   - Verify the queue picks it up and processes it.
   - Verify no duplicate record created.
2. **Full VM reboot:**
   - Queue 3 images in EN_COLA.
   - Start processing the first image.
   - Mid-processing, reboot the VM: `sudo reboot`.
   - Wait for VM to restart and services to come up.
   - Verify: all 3 images still in queue (first recovered to EN_COLA).
   - Verify queue resumes and processes in order.
   - Verify no images lost or duplicated.
3. **Database restart:**
   - While processing, restart PostgreSQL (if accessible):
     ```bash
     sudo systemctl restart postgresql
     ```
   - Verify application reconnects and recovers.

### Step 7: SMB Lock Tolerance Test
1. Create a script that holds a file lock on a new image in `pendientes/`.
2. Wait for the monitor to detect it.
3. Verify the monitor does NOT error out; it retries silently.
4. Release the lock.
5. Verify after lock release and stability check, the image proceeds normally.
6. Verify no ERROR_PROCESAMIENTO or file movement during the locked period.

### Step 8: HTMX Polling from Two Browsers
1. Open Browser A (Ruben) and Browser B (Esme) simultaneously.
2. Both should show their respective pending lists.
3. Copy a new image to Ruben's folder.
4. Verify Browser A updates within 3 seconds (new record appears).
5. Verify Browser B does NOT see Ruben's record.
6. Copy a new image to Esme's folder.
7. Verify Browser B updates within 3 seconds.
8. Verify Browser A (Ruben as admin) DOES see Esme's record.
9. Verify both browsers update independently via HTMX Polling, no F5 needed.

### Step 9: Offline Operation Test
1. Disconnect VM from internet: `sudo ip link set eth0 down` (or equivalent).
2. Copy an image to `pendientes/`.
3. Verify: detection works, Ollama extraction works (local), review works.
4. Verify the record reaches PENDIENTE_DE_ENVIO.
5. Verify the "Enviar a Google Sheets" button is disabled/unavailable.
6. Reconnect: `sudo ip link set eth0 up`.
7. Verify after reconnection, the PENDIENTE_DE_ENVIO record shows the submit button.
8. Submit and verify it reaches Google Sheets.
9. Test multiple images queued offline; verify all are preserved and submittable.

### Step 10: Restart Resilience Test
1. Reboot the host/server fully.
2. Wait for VM to auto-start (verify Criterion 1).
3. Verify all services come up automatically.
4. Verify pending records (any state except ENVIADO) are preserved.
5. Verify the SMB mounts reconnect automatically.
6. Copy a new image and verify it's detected and processed.
7. Run `sudo systemctl restart gastos-ia` 3 times in quick succession.
8. Verify no data corruption or duplicate records.

### Step 11: Real Ticket Processing
1. Use images from `ejemplos/` directory.
2. Process at least 10 real ticket images through the full pipeline.
3. For each image, verify:
   - Extraction quality (date, amount, bank, type correct or close).
   - Confidence scores are reasonable.
   - Human-correctable fields are editable.
   - Submission to Google Sheets succeeds.
   - Image moves to `procesados/` correctly.
4. Record any extraction failures or anomalies.

### Step 12: Invoke skill-uat-instructions
1. Load and execute `harness/skills/skill-uat-instructions/SKILL.md`.
2. Generate the HITL (Human-In-The-Loop) operational manual with:
   - Step-by-step instructions for Ruben and Esme.
   - Screenshots of each screen.
   - Expected inputs and outputs for each action.
   - Troubleshooting guide.
   - How to handle edge cases (duplicates, low confidence, offline, etc.).
3. Generate evidence:
   - `evidence/fase5/manual-operativo.json` + `.md`
   - `docs/manual-operativo.md` (final deliverable).

### Step 13: Generate Phase Summary
1. Compile results for all 39 acceptance criteria.
2. Create a summary table: criterion number, description, status (PASSED/FAILED/INCONCLUSIVE), evidence reference.
3. Produce overall Fase 5 verdict: all 39 criteria must pass for acceptance.
4. Update `harness/PROGRESS.md`:
   - Set `fase5.status` to `completed` (if all criteria pass).
   - Set `fase5.completed_at` to current timestamp.
5. Present summary to user and ask: "¿Fase 5 completada? ¿Autoriza el cierre de Fase 5?"

## Artifacts
- `evidence/fase5/pruebas-funcionales.json` + `.md`
- `evidence/fase5/concurrencia-fifo.json` + `.md`
- `evidence/fase5/recuperacion-reinicio.json` + `.md`
- `evidence/fase5/operacion-offline.json` + `.md`
- `evidence/fase5/manual-operativo.json` + `.md`
- Plus artifacts from sub-skills:
  - `evidence/fase5/pruebas-unitarias.json` + `.md`
  - `evidence/fase5/pruebas-integracion.json` + `.md`
  - `evidence/fase5/pruebas-e2e.json` + `.md`
- `docs/manual-operativo.md` (operational manual, final deliverable).

## Quality Criteria
- All 39 acceptance criteria from PRD section 33 pass.
- Unit tests >= 90% coverage.
- Integration tests use real images from `ejemplos/`.
- E2E tests cover all major flows.
- Concurrency tests confirm FIFO ordering and single ANALIZANDO.
- Recovery tests confirm no data loss after kill/reboot.
- SMB lock tests confirm tolerance and retry.
- HTMX Polling verified from two browsers independently.
- Offline operation preserves data and allows submission after reconnect.
- No secrets in logs, tests, or operational manual.
- Quality gate passes (lint, types, tests, secret scan).

## Edge Cases
- **Model fails on certain images:** Record results in evidence. If accuracy drops below benchmarks (PRD section 32), flag for model evaluation.
- **Google Sheets API rate limits:** If tests generate many requests, space them out. Google Sheets API has quotas (60 requests/minute per user, 100 per 100 seconds per project).
- **Concurrent SMB access:** If two users copy files simultaneously, the monitor should handle them sequentially without race conditions.
- **VM reboot during Sheet submission:** The operation should be transactional. Either the record is fully submitted or remains PENDIENTE_DE_ENVIO; no partial submissions.
- **Browser cache:** When testing HTMX Polling, use fresh browser sessions or incognito mode to avoid cached responses interfering.
- **Missing test images:** If `ejemplos/` is empty, use an annotated set of at least 10 real tickets.

## References
- PRD sections: 33 (39 acceptance criteria), 31 (Requisitos no funcionales), 9 (Flujo funcional), 8 (Carpetas), 10 (Interfaz web), 17 (Estados).
- `skill-unit-tests` — Unit testing with 90% coverage.
- `skill-integration-tests` — Integration tests with real images.
- `skill-e2e-tests` — Playwright E2E automated flows.
- `skill-uat-instructions` — HITL operational manual.
- `skill-quality-gate` — Pre-commit quality validation.
- `skill-git-safety` — Pre-commit secret scan and diff summary.
- `ejemplos/` — Test images directory.

---

## Anexo: 39 Acceptance Criteria Reference

| # | Criterio | PRD Section |
|---|---|---|
| 1 | VM and services auto-start | 33.1 |
| 2 | Page accessible from both computers | 33.2 |
| 3 | Ruben and Esme can log in | 33.3 |
| 4 | Roles work correctly | 33.4 |
| 5 | Folders assign correct owner | 33.5 |
| 6 | Stable images detected | 33.6 |
| 7 | Temporary SMB lock doesn't cause error | 33.7 |
| 8 | Validated images enter FIFO queue | 33.8 |
| 9 | Only one ANALIZANDO at a time | 33.9 |
| 10 | Second image stays EN_COLA until first finishes | 33.10 |
| 11 | FIFO order preserved | 33.11 |
| 12 | Queue survives restart | 33.12 |
| 13 | Interface shows image | 33.13 |
| 14 | HTMX Polling updates states every 3s | 33.14 |
| 15 | Roles affect polling visibility | 33.15 |
| 16 | Model extracts 5 required fields | 33.16 |
| 17 | Confidence generates warnings | 33.17 |
| 18 | Date is editable | 33.18 |
| 19 | Precio unitario and Total sync | 33.19 |
| 20 | Categoria and Cuenta are dropdowns | 33.20 |
| 21 | Consecutive avoids collisions | 33.21 |
| 22 | Final description auto-generated | 33.22 |
| 23 | Submit button blocked if fields missing | 33.23 |
| 24 | Exact duplicates blocked | 33.24 |
| 25 | Probable duplicates show warning | 33.25 |
| 26 | Record goes to correct monthly sheet | 33.26 |
| 27 | Sheets created with 16 headers | 33.27 |
| 28 | Image moved only after send | 33.28 |
| 29 | History allows query and update | 33.29 |
| 30 | Month change moves record | 33.30 |
| 31 | Offline operation preserves expense | 33.31 |
| 32 | JSONL logs contain no secrets | 33.32 |
| 33 | Restart doesn't lose state | 33.33 |
| 34 | No paid AI API used | 33.34 |
| 35 | Repository uses uv | 33.35 |
| 36 | No secrets versioned | 33.36 |
| 37 | Passwords via environment variables | 33.37 |
| 38 | Only Argon2id hashes in PostgreSQL | 33.38 |
| 39 | No commits or pushes without authorization | 33.39 |
