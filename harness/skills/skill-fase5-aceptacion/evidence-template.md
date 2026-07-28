# Evidence Report — skill-fase5-aceptacion

> **Skill:** `skill-fase5-aceptacion`
> **Fase:** `fase5`
> **Timestamp:** `{iso8601}`
> **Estado:** `[PASADO | FALLADO | PARCIAL]`
> **Duración:** `{duration}`

---

## Resumen Ejecutivo

{Fase 5 — Aceptación — completion summary. Total acceptance criteria verified (39/39), sub-skills executed (unit, integration, e2e, UAT), advanced tests performed (concurrency/FIFO, recovery/kill-reboot, SMB lock, HTMX polling dual browser, offline, restart resilience, real tickets). Operational manual generated. Overall verdict: accepted or blocked.}

---

## Métricas

| Métrica | Valor |
|---|---|
| Acceptance criteria total | 39 |
| Acceptance criteria passed | `{N}` |
| Acceptance criteria failed | `{N}` |
| Sub-skills executed | 4/4 |
| Real tickets processed | `{N}` |
| Concurrency tests | `{N}` |
| Recovery scenarios tested | `{N}` |
| Test images used | `{count from ejemplos/}` |
| Unit test coverage | `{N}%` |
| Integration tests passed | `{N}/{N}` |
| E2E tests passed | `{N}/{N}` |
| Secretos detectados | `0` (mandatory) |

---

## Acceptance Criteria Results

| # | Criterio | Estado | Evidencia |
|---|---|---|---|
| 1 | VM and services auto-start | `{status}` | `systemctl status + curl /health` |
| 2 | Page accessible from both computers | `{status}` | `Browser screenshots` |
| 3 | Ruben and Esme can log in | `{status}` | `Login screenshots` |
| 4 | Roles work correctly | `{status}` | `Permission test URLs` |
| 5 | Folders assign correct owner | `{status}` | `DB query: owner field` |
| 6 | Stable images detected | `{status}` | `Audit events` |
| 7 | SMB lock tolerance | `{status}` | `Lock test log` |
| 8 | Images enter FIFO queue | `{status}` | `processing_queue table` |
| 9 | Only one ANALIZANDO | `{status}` | `Concurrency timeline` |
| 10 | Second image stays EN_COLA | `{status}` | `State transition log` |
| 11 | FIFO order preserved | `{status}` | `enqueued_at ordering` |
| 12 | Queue survives restart | `{status}` | `Recovery test output` |
| 13 | Interface shows image | `{status}` | `Screenshot: visor` |
| 14 | HTMX Polling updates (3s) | `{status}` | `Browser dev tools HAR` |
| 15 | Roles affect polling | `{status}` | `Dual browser screenshot` |
| 16 | 5 fields extracted | `{status}` | `Extraction quality report` |
| 17 | Confidence warnings | `{status}` | `Screenshot: low confidence` |
| 18 | Date editable | `{status}` | `Form interaction` |
| 19 | Precio/Total sync | `{status}` | `Form sync test` |
| 20 | Categoria/Cuenta dropdowns | `{status}` | `Screenshot: dropdowns` |
| 21 | Consecutive no collisions | `{status}` | `DB query: consecutivos` |
| 22 | Final description auto-gen | `{status}` | `Sample descriptions` |
| 23 | Submit blocked if missing | `{status}` | `Button state test` |
| 24 | Exact duplicates blocked | `{status}` | `DUPLICADO_EXACTO state` |
| 25 | Probable duplicates warning | `{status}` | `DUPLICADO_PROBABLE state` |
| 26 | Correct monthly sheet | `{status}` | `Sheets screenshot` |
| 27 | 16 headers on new sheet | `{status}` | `Sheets screenshot` |
| 28 | Image moved after send | `{status}` | `procesados/YYY/MM/ check` |
| 29 | History query and update | `{status}` | `History screen flow` |
| 30 | Month change moves record | `{status}` | `Two-sheet verification` |
| 31 | Offline preserves expense | `{status}` | `Offline test log` |
| 32 | Logs have no secrets | `{status}` | `Gitleaks on logs` |
| 33 | Restart doesn't lose state | `{status}` | `Restart + DB query` |
| 34 | No paid AI API used | `{status}` | `Network traffic analysis` |
| 35 | Repository uses uv | `{status}` | `pyproject.toml check` |
| 36 | No secrets versioned | `{status}` | `Gitleaks clean` |
| 37 | Passwords via env vars | `{status}` | `EnvironmentFile check` |
| 38 | Only Argon2id in DB | `{status}` | `password_hash format check` |
| 39 | No unauthorized commits | `{status}` | `Process confirmation` |

---

## Sub-Skill Results

| Sub-Skill | Estado | Cobertura/Result | Artefacto |
|---|---|---|---|
| `skill-unit-tests` | `{status}` | `{N}%` | `pruebas-unitarias.json` |
| `skill-integration-tests` | `{status}` | `{N}/{N}` passed | `pruebas-integracion.json` |
| `skill-e2e-tests` | `{status}` | `{N}/{N}` flows | `pruebas-e2e.json` |
| `skill-uat-instructions` | `{status}` | Manual generated | `manual-operativo.json` |

---

## Advanced Test Results

### Concurrency / FIFO

| Test | Resultado | Observaciones |
|---|---|---|
| 5 simultaneous images | `{status}` | `{timeline}` |
| Only 1 ANALIZANDO | `{status}` | `{confirmation}` |
| FIFO order preserved | `{status}` | `{order check}` |
| Two users copying simultaneously | `{status}` | `{result}` |

### Recovery

| Test | Resultado | Observaciones |
|---|---|---|
| Kill worker mid-processing | `{status}` | `{ANALIZANDO → EN_COLA}` |
| Full VM reboot mid-processing | `{status}` | `{queue preserved, no duplicates}` |
| PostgreSQL restart | `{status}` | `{reconnection OK}` |

### SMB Lock

| Test | Resultado | Observaciones |
|---|---|---|
| File locked → monitor retries | `{status}` | `{silent retry, no error}` |
| Lock released → normal processing | `{status}` | `{processing resumed}` |

### HTMX Polling (Dual Browser)

| Test | Resultado | Observaciones |
|---|---|---|
| Browser A (Ruben) + Browser B (Esme) | `{status}` | `{independent updates}` |
| Ruben's image visible only to A | `{status}` | `{confirmation}` |
| Esme's image visible to both | `{status}` | `{admin sees all}` |
| No F5 required | `{status}` | `{true}` |

### Offline Operation

| Test | Resultado | Observaciones |
|---|---|---|
| Detection + extraction offline | `{status}` | `{local only}` |
| PENDIENTE_DE_ENVIO state | `{status}` | `{confirmed}` |
| Reconnect + submit | `{status}` | `{successful}` |
| Multiple offline images | `{status}` | `{all preserved}` |

### Restart Resilience

| Test | Resultado | Observaciones |
|---|---|---|
| Full host reboot | `{status}` | `{all services auto-start}` |
| Pending records preserved | `{status}` | `{DB check}` |
| SMB mounts reconnect | `{status}` | `{automount works}` |
| Rapid restarts (3x) | `{status}` | `{no corruption}` |

### Real Tickets

| Imagen | Date Accuracy | Amount Accuracy | Bank | Type | Submitted |
|---|---|---|---|---|---|
| `ejemplos/ticket_01.jpg` | `{yes/no}` | `{yes/no}` | `{detected}` | `{detected}` | `{status}` |
| `ejemplos/ticket_02.jpg` | `{yes/no}` | `{yes/no}` | `{detected}` | `{detected}` | `{status}` |
| ... | ... | ... | ... | ... | ... |

---

## Quality Gate Results

| Paso | Comando | Estado |
|---|---|---|
| Dependencies | `uv sync --frozen` | `{status}` |
| Format | `ruff format --check .` | `{status}` |
| Lint | `ruff check .` | `{status}` |
| Types | `mypy app/` | `{status}` |
| Unit tests | `pytest tests/unit/ --cov=app --cov-fail-under=90` | `{status}` |
| Integration tests | `pytest tests/integration/` | `{status}` |
| Security audit | `pip-audit` | `{status}` |
| Secret scan | `gitleaks detect --source .` | `{status}` |

---

## Artefactos Generados

| Archivo | Skill | Tipo |
|---|---|---|
| `evidence/fase5/pruebas-unitarias.json` | unit-tests | `evidence/json` |
| `evidence/fase5/pruebas-unitarias.md` | unit-tests | `evidence/md` |
| `evidence/fase5/pruebas-integracion.json` | integration-tests | `evidence/json` |
| `evidence/fase5/pruebas-integracion.md` | integration-tests | `evidence/md` |
| `evidence/fase5/pruebas-e2e.json` | e2e-tests | `evidence/json` |
| `evidence/fase5/pruebas-e2e.md` | e2e-tests | `evidence/md` |
| `evidence/fase5/pruebas-funcionales.json` | fase5-aceptacion | `evidence/json` |
| `evidence/fase5/pruebas-funcionales.md` | fase5-aceptacion | `evidence/md` |
| `evidence/fase5/concurrencia-fifo.json` | fase5-aceptacion | `evidence/json` |
| `evidence/fase5/concurrencia-fifo.md` | fase5-aceptacion | `evidence/md` |
| `evidence/fase5/recuperacion-reinicio.json` | fase5-aceptacion | `evidence/json` |
| `evidence/fase5/recuperacion-reinicio.md` | fase5-aceptacion | `evidence/md` |
| `evidence/fase5/operacion-offline.json` | fase5-aceptacion | `evidence/json` |
| `evidence/fase5/operacion-offline.md` | fase5-aceptacion | `evidence/md` |
| `evidence/fase5/manual-operativo.json` | uat-instructions | `evidence/json` |
| `evidence/fase5/manual-operativo.md` | uat-instructions | `evidence/md` |
| `docs/manual-operativo.md` | uat-instructions | `documentation` |

---

## Errores (si los hay)

| Código | Criterio | Mensaje |
|---|---|---|
| `ERR_XXX` | `C{N}` | `{description and resolution}` |

---

## Fase 5 Verdict

```
{ if all 39 pass }

  VEREDICTO: MVP ACEPTADO
  Todos los 39 criterios de aceptación del PRD sección 33 han sido verificados.
  El sistema está listo para producción.

{ if any fail }

  VEREDICTO: BLOQUEADO
  {N} criterios no pasan. Ver tabla de errores arriba.
  Se requiere corrección antes de aceptar el MVP.
```

---

## Próximos Pasos

1. If accepted: inform Ruben and Esme to begin using the system.
2. If blocked: create issues for failed criteria, assign to appropriate phase for fixes.
3. Consider post-MVP improvements (not in scope).

---

## Precondiciones al Inicio

```json
{
  "fase4": "completed",
  "app_url": "https://gastos.local",
  "users": ["ruben", "esme"],
  "ollama_model": "qwen3-vl:4b",
  "test_images_available": "{N}",
  "google_sheets_configured": true
}
```

---

*Reporte generado automáticamente por el arnés Gastos IA v1.0*
