# Evidence Report — skill-installer

> **Skill:** `skill-installer`
> **Fase:** `fase4`
> **Timestamp:** `{iso8601}`
> **Estado:** `[PASADO | FALLADO | PARCIAL]`
> **Duración:** `{duration}`

---

## Resumen Ejecutivo

{Summary of automated installation: pre-flight checks, VM software setup, application deployment from git, database creation (gastos_ia DB, gastos_app user), table initialization, Google Sheets credentials setup, user creation (Ruben + Esme with Argon2id), environment variable population, service activation, validation tests, and diagnostic JSON generation. Confirm no secrets were leaked to logs or evidence.}

---

## Métricas

| Métrica | Valor |
|---|---|
| Total de verificaciones | `{N}` |
| Pasadas | `{N}` |
| Fallidas | `{N}` |
| Secretos detectados en outputs | `0` (mandatory) |
| Bases de datos creadas | `1` (gastos_ia) |
| Usuarios creados | `2` (Ruben + Esme) |
| Tablas inicializadas | `9` |

---

## Verificaciones

### Pre-ejecución

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C1 | Administrator rights | `{status}` | `{check result}` |
| C2 | Hyper-V module available | `{status}` | `{module check}` |
| C3 | Disk space sufficient | `{status}` | `{free space GB}` |
| C4 | VM pingable at 192.168.100.75 | `{status}` | `{ping result}` |
| C5 | SSH access to VM | `{status}` | `{ssh test result}` |

### Ejecución — VM Software

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C6 | Python3 installed | `{status}` | `{version}` |
| C7 | uv installed | `{status}` | `{version}` |
| C8 | PostgreSQL client installed | `{status}` | `{version}` |

### Ejecución — Application Deployment

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C9 | Repo at /opt/gastos-ia | `{status}` | `{branch, commit hash}` |
| C10 | uv sync --frozen passed | `{status}` | `{output summary}` |
| C11 | FastAPI import test | `{status}` | `{test result}` |

### Ejecución — Database

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C12 | gastos_ia database exists | `{status}` | `{psql -l output}` |
| C13 | gastos_app user exists | `{status}` | `{SELECT current_user test}` |
| C14 | Connection as gastos_app works | `{status}` | `{connection result}` |
| C15 | Tables initialized (9 tables) | `{status}` | `{\dt output}` |

### Ejecución — Google Sheets

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C16 | Service account JSON secured | `{status}` | `{path, permissions}` |
| C17 | Spreadsheet ID configured | `{status}` | `{masked ID: XXXX...XXXX}` |
| C18 | Google API test passed | `{status}` | `{connection result}` |

### Ejecución — Users

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C19 | Ruben created (admin) | `{status}` | `{Argon2id hash confirmed}` |
| C20 | Esme created (standard) | `{status}` | `{Argon2id hash confirmed}` |
| C21 | Init password vars unset | `{status}` | `{env check}` |
| C22 | No passwords in logs | `{status}` | `{audit check}` |

### Ejecución — Environment

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C23 | /etc/gastos-ia/gastos-ia.env populated | `{status}` | `{all variables filled}` |
| C24 | File permissions 0600 root:root | `{status}` | `{ls -la output}` |
| C25 | SMB credentials configured | `{status}` | `{shares mounted}` |

### Ejecución — Services

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C26 | gastos-ia.service started | `{status}` | `{systemctl status}` |
| C27 | Health endpoint responds | `{status}` | `{curl /health}` |
| C28 | Login page loads | `{status}` | `{curl /login result}` |

### Ejecución — Validation

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C29 | Tests pass | `{status}` | `{pytest summary}` |
| C30 | Ruff lint passes | `{status}` | `{ruff output}` |
| C31 | Mypy type check passes | `{status}` | `{mypy output}` |
| C32 | Ollama API responsive | `{status}` | `{ollama tags output}` |

### Post-ejecución

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C33 | Diagnostic JSON generated | `{status}` | `{file path, size}` |
| C34 | Diagnostic has no secrets | `{status}` | `{manual review}` |
| C35 | VM auto-start confirmed | `{status}` | `{Get-VM output}` |
| C36 | All evidence files exist | `{status}` | `{file count}` |
| C37 | Gitleaks scan clean | `{status}` | `{gitleaks output}` |

---

## Artefactos Generados

| Archivo | Tipo | Descripción |
|---|---|---|
| `evidence/fase4/despliegue-aplicacion.json` | `evidence/json` | Application deployment results |
| `evidence/fase4/despliegue-aplicacion.md` | `evidence/md` | Application deployment report |
| `evidence/fase4/base-datos.json` | `evidence/json` | Database creation results |
| `evidence/fase4/base-datos.md` | `evidence/md` | Database creation report |
| `evidence/fase4/credenciales-google.json` | `evidence/json` | Google Sheets setup |
| `evidence/fase4/credenciales-google.md` | `evidence/md` | Google Sheets report |
| `evidence/fase4/creacion-usuarios.json` | `evidence/json` | User account creation |
| `evidence/fase4/creacion-usuarios.md` | `evidence/md` | User account report |
| `evidence/fase4/variables-entorno.json` | `evidence/json` | Environment variables configuration |
| `evidence/fase4/variables-entorno.md` | `evidence/md` | Environment variables report |
| `evidence/fase4/activacion-servicios.json` | `evidence/json` | Service activation |
| `evidence/fase4/activacion-servicios.md` | `evidence/md` | Service activation report |
| `evidence/fase4/validacion-pruebas.json` | `evidence/json` | Validation test results |
| `evidence/fase4/validacion-pruebas.md` | `evidence/md` | Validation test report |
| `evidence/fase4/diagnostico.json` | `evidence/json` | System diagnostic (without secrets) |
| `evidence/fase4/diagnostico.md` | `evidence/md` | System diagnostic report |
| `scripts/diagnostics/diagnostic-{date}.json` | `diagnostic` | Machine diagnostic JSON |
| `/etc/gastos-ia/gastos-ia.env` | `config` | Production environment file |

---

## Configuración de Seguridad

| Recurso | Permisos | Propietario | En repo |
|---|---|---|---|
| `/etc/gastos-ia/gastos-ia.env` | `0600` | `root:root` | No (fuera) |
| `/etc/gastos-ia/google-service-account.json` | `0600` | `root:root` | No (fuera) |
| `/etc/gastos-ia/smb-credentials` | `0600` | `root:root` | No (fuera) |
| `scripts/diagnostics/diagnostic-*.json` | `0644` | `gastos-admin` | No (en .gitignore) |
| User passwords (Argon2id) | Solo hash en DB | PostgreSQL | No |

---

## Errores (si los hay)

| Código | Mensaje |
|---|---|
| `ERR_XXX` | `{description and resolution}` |

---

## Próximos Pasos

1. Execute `skill-fase5-aceptacion` to run Fase 5 acceptance testing.
2. Configure client machines to trust the Caddy self-signed certificate.
3. Inform Ruben and Esme that they must change passwords on first login.

---

## Precondiciones al Inicio

```json
{
  "skill_infrastructure": "completed",
  "vm_ip": "192.168.100.75",
  "vm_user": "gastos-admin",
  "ssh_accessible": true,
  "ollama_model": "qwen3-vl:4b",
  "smb_mounted": true,
  "caddy_running": true,
  "systemd_service_file": "/etc/systemd/system/gastos-ia.service"
}
```

---

*Reporte generado automáticamente por el arnés Gastos IA v1.0*
