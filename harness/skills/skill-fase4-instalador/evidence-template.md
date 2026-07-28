# Evidence Report — skill-fase4-instalador (Fase 4 Orchestrator)

> **Skill:** `skill-fase4-instalador`
> **Fase:** `fase4`
> **Timestamp:** `{iso8601}`
> **Estado:** `[PASADO | FALLADO | PARCIAL]`
> **Duración:** `{duration}`

---

## Resumen Ejecutivo

{Fase 4 — Instalador — completion summary. What infrastructure was provisioned (VM specs, network, HTTPS, Ollama, SMB, systemd) and what was deployed (application, database, users, Google Sheets). Total artifacts generated, GATE authorizations received, quality gate results. Confirm application is running and accessible at https://gastos.local.}

---

## Métricas

| Métrica | Valor |
|---|---|
| Total de verificaciones | `{N}` |
| Sub-skills ejecutados | `2/2` (infrastructure + installer) |
| Autorizaciones GATE (infra) | `{N}/{N}` |
| Artefactos generados (total) | `{N}` |
| Usuarios creados | `2` (Ruben + Esme) |
| Bases de datos | `1` (gastos_ia) |
| Tablas | `9` |
| Servicios activos | `4` (caddy, ollama, gastos-ia, systemd-resolved) |
| Tests pasados | `{N}/{N}` |
| Cobertura | `{N}%` |
| Secretos detectados | `0` (mandatory) |

---

## Sub-Skill 1: skill-infrastructure

| Métrica | Valor |
|---|---|
| Estado | `[passed|failed|partial]` |
| Artefactos generados | `9` |
| Autorizaciones GATE | `{list of all "AUTORIZADO" timestamps}` |

### Resumen de Infraestructura

| Recurso | Configuración | Estado |
|---|---|---|
| Hyper-V | Enabled | `{status}` |
| External Switch | GastosIA-External | `{status}` |
| VM | 16 GB RAM, 4 vCPU, Gen 2 | `{status}` |
| VHDX | 120 GB dynamic at D:\Hyper-V\... | `{status}` |
| Ubuntu | LTS, static IP 192.168.100.75 | `{status}` |
| Caddy | HTTPS gastos.local → localhost:8000 | `{status}` |
| Ollama | qwen3-vl:4b, localhost only | `{status}` |
| SMB Ruben | /mnt/smb/Ruben | `{status}` |
| SMB Esme | /mnt/smb/Esme | `{status}` |
| Environment | /etc/gastos-ia/gastos-ia.env (0600) | `{status}` |
| Systemd | gastos-ia.service (enabled) | `{status}` |
| Auto-start | VM auto-starts with host | `{status}` |

---

## Sub-Skill 2: skill-installer

| Métrica | Valor |
|---|---|
| Estado | `[passed|failed|partial]` |
| Artefactos generados | `8` |
| Credenciales seguras solicitadas | `{N}` |

### Resumen de Instalación

| Componente | Detalle | Estado |
|---|---|---|
| Python | `{version}` | `{status}` |
| uv | `{version}` | `{status}` |
| psql | `{version}` | `{status}` |
| Repo | /opt/gastos-ia, branch `{branch}` | `{status}` |
| DB gastos_ia | Created, gastos_app user | `{status}` |
| Tables | 9 tables initialized | `{status}` |
| Google Sheets | Credential JSON secured, API tested | `{status}` |
| Users | Ruben (admin) + Esme (standard) | `{status}` |
| Environment | All vars filled, no empties | `{status}` |
| Service | gastos-ia active (running) | `{status}` |
| Tests | `{passed}/{total}` passed | `{status}` |
| Diagnostic | `scripts/diagnostics/diagnostic-{date}.json` | `{status}` |

---

## Quality Gate Results

| Paso | Comando | Estado |
|---|---|---|
| Dependencies | `uv sync --frozen` | `{status}` |
| Format | `uv run ruff format --check .` | `{status}` |
| Lint | `uv run ruff check .` | `{status}` |
| Types | `uv run mypy app/` | `{status}` |
| Unit tests | `uv run pytest tests/unit/ --cov=app --cov-fail-under=90` | `{status}` |
| Integration tests | `uv run pytest tests/integration/` | `{status}` |
| Security audit | `uv run pip-audit` | `{status}` |
| Secret scan | `gitleaks detect --source . --verbose` | `{status}` |

---

## Artefactos Generados

| Archivo | Skill | Tipo |
|---|---|---|
| `evidence/fase4/validacion-hyperv.json` | infrastructure | `evidence/json` |
| `evidence/fase4/validacion-hyperv.md` | infrastructure | `evidence/md` |
| `evidence/fase4/configuracion-red.json` | infrastructure | `evidence/json` |
| `evidence/fase4/configuracion-red.md` | infrastructure | `evidence/md` |
| `evidence/fase4/creacion-vm.json` | infrastructure | `evidence/json` |
| `evidence/fase4/creacion-vm.md` | infrastructure | `evidence/md` |
| `evidence/fase4/configuracion-caddy.json` | infrastructure | `evidence/json` |
| `evidence/fase4/configuracion-caddy.md` | infrastructure | `evidence/md` |
| `evidence/fase4/configuracion-ollama.json` | infrastructure | `evidence/json` |
| `evidence/fase4/configuracion-ollama.md` | infrastructure | `evidence/md` |
| `evidence/fase4/montaje-smb.json` | infrastructure | `evidence/json` |
| `evidence/fase4/montaje-smb.md` | infrastructure | `evidence/md` |
| `evidence/fase4/archivo-entorno.json` | infrastructure | `evidence/json` |
| `evidence/fase4/archivo-entorno.md` | infrastructure | `evidence/md` |
| `evidence/fase4/servicio-systemd.json` | infrastructure | `evidence/json` |
| `evidence/fase4/servicio-systemd.md` | infrastructure | `evidence/md` |
| `evidence/fase4/inicio-automatico.json` | infrastructure | `evidence/json` |
| `evidence/fase4/inicio-automatico.md` | infrastructure | `evidence/md` |
| `evidence/fase4/despliegue-aplicacion.json` | installer | `evidence/json` |
| `evidence/fase4/despliegue-aplicacion.md` | installer | `evidence/md` |
| `evidence/fase4/base-datos.json` | installer | `evidence/json` |
| `evidence/fase4/base-datos.md` | installer | `evidence/md` |
| `evidence/fase4/credenciales-google.json` | installer | `evidence/json` |
| `evidence/fase4/credenciales-google.md` | installer | `evidence/md` |
| `evidence/fase4/creacion-usuarios.json` | installer | `evidence/json` |
| `evidence/fase4/creacion-usuarios.md` | installer | `evidence/md` |
| `evidence/fase4/variables-entorno.json` | installer | `evidence/json` |
| `evidence/fase4/variables-entorno.md` | installer | `evidence/md` |
| `evidence/fase4/activacion-servicios.json` | installer | `evidence/json` |
| `evidence/fase4/activacion-servicios.md` | installer | `evidence/md` |
| `evidence/fase4/validacion-pruebas.json` | installer | `evidence/json` |
| `evidence/fase4/validacion-pruebas.md` | installer | `evidence/md` |
| `evidence/fase4/diagnostico.json` | installer | `evidence/json` |
| `evidence/fase4/diagnostico.md` | installer | `evidence/md` |
| `scripts/diagnostics/diagnostic-{date}.json` | installer | `diagnostic` |

---

## Errores (si los hay)

| Código | Mensaje |
|---|---|
| `ERR_XXX` | `{description and resolution}` |

---

## Próximos Pasos

1. Execute `skill-fase5-aceptacion` for acceptance testing.
2. Verify all 39 acceptance criteria from PRD section 33.
3. Generate operational manual.

---

## Precondiciones al Inicio

```json
{
  "fase3": "completed",
  "branch": "arnes",
  "installer_script": "scripts/install-gastos-ia.ps1",
  "host": "Windows Server with Hyper-V enabled",
  "user_availability": "confirmed for GATE authorizations"
}
```

---

*Reporte generado automáticamente por el arnés Gastos IA v1.0*
