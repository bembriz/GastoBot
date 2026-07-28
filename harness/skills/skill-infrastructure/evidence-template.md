# Evidence Report — skill-infrastructure

> **Skill:** `skill-infrastructure`
> **Fase:** `fase4`
> **Timestamp:** `{iso8601}`
> **Estado:** `[PASADO | FALLADO | PARCIAL]`
> **Duración:** `{duration}`

---

## Resumen Ejecutivo

{Summary of infrastructure provisioning: Hyper-V validation, VM creation (16 GB RAM, 4 vCPU, 120 GB VHDX), network configuration (static IP 192.168.100.75), Caddy HTTPS on gastos.local, Ollama installation, SMB mount setup, environment file creation, systemd service definition, and VM auto-start. Include whether all gates were authorized and all validations passed.}

---

## Métricas

| Métrica | Valor |
|---|---|
| Total de verificaciones | `{N}` |
| Pasadas | `{N}` |
| Fallidas | `{N}` |
| Autorizaciones GATE requeridas | `{N}` |
| Autorizaciones GATE recibidas | `{N}` |

---

## Verificaciones

### Pre-ejecución

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C1 | Hyper-V role enabled on host | `{status}` | `{output from Get-WindowsOptionalFeature}` |
| C2 | Host has enough CPU/RAM | `{status}` | `{output from Get-VMHost}` |
| C3 | No VM name collision (GastosIA) | `{status}` | `{output from Get-VM}` |
| C4 | SMB shares exist on SERVIDOR | `{status}` | `{confirmation}` |
| C5 | D:\ has >= 130 GB free | `{status}` | `{disk space output}` |

### Ejecución — Hyper-V & Switch

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C6 | External virtual switch created | `{status}` | `{Get-VMSwitch output}` |
| C7 | Management OS retains connectivity | `{status}` | `{ping test result}` |

### Ejecución — VM

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C8 | VHDX created (120 GB dynamic) | `{status}` | `{Get-VHD output}` |
| C9 | VM created with correct specs | `{status}` | `{Get-VM output (MemoryStartup, ProcessorCount, Generation)}` |
| C10 | Ubuntu ISO attached | `{status}` | `{Get-VMDvdDrive output}` |

### Ejecución — Network

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C11 | Ethernet adapter identified | `{status}` | `{Get-NetAdapter output}` |
| C12 | Gateway identified | `{status}` | `{Get-NetRoute output}` |
| C13 | DNS servers identified | `{status}` | `{Get-DnsClientServerAddress output}` |
| C14 | 192.168.100.75 ping test (free) | `{status}` | `{ping result}` |
| C15 | ARP table checked | `{status}` | `{arp output for 192.168.100.x}` |
| C16 | DHCP range validated | `{status}` | `{confirmation from user}` |
| C17 | Static IP configured on Ubuntu | `{status}` | `{ip addr show from VM}` |
| C18 | SSH access confirmed | `{status}` | `{ssh connection result}` |

### Ejecución — Caddy

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C19 | Caddy installed | `{status}` | `{caddy version}` |
| C20 | Caddyfile configured | `{status}` | `{Caddyfile contents (placeholder)}` |
| C21 | Caddy service running | `{status}` | `{systemctl status caddy}` |
| C22 | HTTPS responds at gastos.local | `{status}` | `{curl -k response}` |
| C23 | Cert trust script generated | `{status}` | `{script path}` |

### Ejecución — Ollama

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C24 | Ollama installed | `{status}` | `{ollama --version}` |
| C25 | Ollama service running | `{status}` | `{systemctl status ollama}` |
| C26 | qwen3-vl:4b pulled | `{status}` | `{ollama list output}` |
| C27 | Ollama bound to localhost only | `{status}` | `{no OLLAMA_HOST override}` |

### Ejecución — SMB

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C28 | cifs-utils installed | `{status}` | `{dpkg -l cifs-utils}` |
| C29 | Mount points created | `{status}` | `{ls -la /mnt/smb/}` |
| C30 | Credentials file created (0600) | `{status}` | `{ls -la output}` |
| C31 | Ruben share mounted | `{status}` | `{mount grep cifs, ls /mnt/smb/Ruben/pendientes}` |
| C32 | Esme share mounted | `{status}` | `{mount grep cifs, ls /mnt/smb/Esme/pendientes}` |

### Ejecución — Environment & Systemd

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C33 | /etc/gastos-ia/gastos-ia.env created | `{status}` | `{ls -la showing 0600 root:root}` |
| C34 | gastos-ia.service created | `{status}` | `{service file contents}` |
| C35 | service enabled | `{status}` | `{systemctl is-enabled gastos-ia}` |

### Post-ejecución

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C36 | VM auto-start configured | `{status}` | `{Get-VM AutomaticStartAction}` |
| C37 | All evidence files generated | `{status}` | `{count of files}` |
| C38 | No secrets in any output | `{status}` | `{gitleaks / manual check}` |

---

## Artefactos Generados

| Archivo | Tipo | Descripción |
|---|---|---|
| `evidence/fase4/validacion-hyperv.json` | `evidence/json` | Hyper-V capability validation |
| `evidence/fase4/validacion-hyperv.md` | `evidence/md` | Hyper-V capability report |
| `evidence/fase4/configuracion-red.json` | `evidence/json` | Network analysis and static IP config |
| `evidence/fase4/configuracion-red.md` | `evidence/md` | Network analysis report |
| `evidence/fase4/creacion-vm.json` | `evidence/json` | VM creation and specs |
| `evidence/fase4/creacion-vm.md` | `evidence/md` | VM creation report |
| `evidence/fase4/configuracion-caddy.json` | `evidence/json` | Caddy HTTPS setup |
| `evidence/fase4/configuracion-caddy.md` | `evidence/md` | Caddy HTTPS report |
| `evidence/fase4/configuracion-ollama.json` | `evidence/json` | Ollama installation and model pull |
| `evidence/fase4/configuracion-ollama.md` | `evidence/md` | Ollama configuration report |
| `evidence/fase4/montaje-smb.json` | `evidence/json` | SMB mount configuration |
| `evidence/fase4/montaje-smb.md` | `evidence/md` | SMB mount report |
| `evidence/fase4/archivo-entorno.json` | `evidence/json` | Environment file setup |
| `evidence/fase4/archivo-entorno.md` | `evidence/md` | Environment file report |
| `evidence/fase4/servicio-systemd.json` | `evidence/json` | Systemd service definition |
| `evidence/fase4/servicio-systemd.md` | `evidence/md` | Systemd service report |
| `evidence/fase4/inicio-automatico.json` | `evidence/json` | VM auto-start configuration |
| `evidence/fase4/inicio-automatico.md` | `evidence/md` | VM auto-start report |

---

## Errores (si los hay)

| Código | Mensaje |
|---|---|
| `ERR_XXX` | `{description and resolution}` |

---

## Autorizaciones GATE

| Paso | Propuesta | Output de validación | Autorización |
|---|---|---|---|
| Hyper-V check | Enable Hyper-V, validate capabilities | `{output}` | `{timestamp + "AUTORIZADO"}` |
| Virtual switch | Create GastosIA-External switch | `{output}` | `{timestamp + "AUTORIZADO"}` |
| VHDX creation | 120 GB dynamic VHDX at D:\Hyper-V\...| `{output}` | `{timestamp + "AUTORIZADO"}` |
| VM creation | 16 GB RAM, 4 vCPU, Gen 2 | `{output}` | `{timestamp + "AUTORIZADO"}` |
| Static IP | 192.168.100.75 with network analysis | `{output}` | `{timestamp + "AUTORIZADO"}` |
| SMB fstab | CIFS mounts for Ruben and Esme | `{output}` | `{timestamp + "AUTORIZADO"}` |
| Cert trust export | Export self-signed cert for clients | `{output}` | `{timestamp + "AUTORIZADO"}` |
| VM auto-start | Set VM to start with host | `{output}` | `{timestamp + "AUTORIZADO"}` |

---

## Próximos Pasos

1. Invoke `skill-installer` to deploy application code, create database, and initialize environment.
2. Fill real values in `/etc/gastos-ia/gastos-ia.env` (guided by installer).
3. Start `gastos-ia.service` after deployment.

---

## Precondiciones al Inicio

```json
{
  "branch": "arnes",
  "fase3_status": "completed",
  "host": "Windows Server with Hyper-V",
  "ethernet": "connected",
  "postgresql": "available on 192.168.100.x",
  "smb_shares": "\\\\SERVIDOR\\GastosIA\\Ruben and \\\\SERVIDOR\\GastosIA\\Esme exist"
}
```

---

*Reporte generado automáticamente por el arnés Gastos IA v1.0*
