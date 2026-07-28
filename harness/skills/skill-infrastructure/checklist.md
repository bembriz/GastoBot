# Checklist — skill-infrastructure

## Pre-ejecución
- [ ] Fase 3 completada (`harness/PROGRESS.md` shows `completed`).
- [ ] User present and available to authorize each infrastructure step.
- [ ] Windows Server host accessible (RDP or physical console).
- [ ] Ethernet adapter connected to target network.
- [ ] PostgreSQL server reachable from target subnet (192.168.100.x).
- [ ] SMB shares `\\SERVIDOR\GastosIA\Ruben` and `\\SERVIDOR\GastosIA\Esme` exist.
- [ ] Drive `D:\` has at least 130 GB free space.
- [ ] Ubuntu Server LTS ISO available or network access to download.
- [ ] `D:\Hyper-V\ISOs\` directory exists or can be created.

## Ejecución

### Hyper-V Validation
- [ ] C1: Run `Get-WindowsOptionalFeature` and confirm Hyper-V is Enabled.
- [ ] C2: Run `Get-VMHost` and confirm >= 4 logical processors and >= 16 GB RAM.
- [ ] C3: Confirm no VM named "GastosIA" already exists.
- [ ] C4: **[GATE]** User authorized Hyper-V validation results → "AUTORIZADO".

### Virtual Switch
- [ ] C5: Identify active Ethernet adapter with `Get-NetAdapter`.
- [ ] C6: Confirm no existing switch named "GastosIA-External".
- [ ] C7: **[GATE]** User authorized switch creation → "AUTORIZADO".
- [ ] C8: Create `GastosIA-External` switch and validate with `Get-VMSwitch`.
- [ ] C9: Confirm management OS retains network connectivity.

### VM Directory and VHDX
- [ ] C10: Confirm `D:\Hyper-V\VirtualMachines\GastosIA` does not exist or is empty.
- [ ] C11: **[GATE]** User authorized directory creation → "AUTORIZADO".
- [ ] C12: Create directory.
- [ ] C13: **[GATE]** User authorized VHDX creation → "AUTORIZADO".
- [ ] C14: Create 120 GB dynamic VHDX and validate with `Get-VHD`.

### VM Creation
- [ ] C15: **[GATE]** User authorized VM creation → "AUTORIZADO".
- [ ] C16: Create VM with 16 GB RAM, 4 vCPU, Gen 2, static memory.
- [ ] C17: Validate VM specs with `Get-VM`.
- [ ] C18: Attach Ubuntu ISO to VM DVD drive.

### Network Validation (before static IP)
- [ ] C19: Run `Get-NetIPAddress` on Ethernet adapter and show output.
- [ ] C20: Run `Get-NetRoute -DestinationPrefix "0.0.0.0/0"` and show gateway.
- [ ] C21: Run `Get-DnsClientServerAddress` and show DNS servers.
- [ ] C22: Ping `192.168.100.75` to verify it's free.
- [ ] C23: Check ARP table for `192.168.100.x` conflicts.
- [ ] C24: Confirm IP is outside DHCP range (consult user if needed).
- [ ] C25: **[GATE]** User approved static IP 192.168.100.75 → "AUTORIZADO".

### Ubuntu Install
- [ ] C26: Create or validate `autoinstall.yaml` with static IP config.
- [ ] C27: Start VM.
- [ ] C28: Confirm Ubuntu boots to login prompt.
- [ ] C29: SSH into `gastos-admin@192.168.100.75` succeeds.

### Caddy
- [ ] C30: Install caddy package.
- [ ] C31: Configure Caddyfile for `gastos.local → localhost:8000`.
- [ ] C32: Enable and start caddy service.
- [ ] C33: Validate `curl -k https://gastos.local` returns a response.
- [ ] C34: **[GATE]** User authorized cert trust export → "AUTORIZADO".
- [ ] C35: Generate/export certificate trust script for client machines.

### Ollama
- [ ] C36: Install Ollama via official script.
- [ ] C37: Confirm `ollama` systemd service is running.
- [ ] C38: Pull `qwen3-vl:4b` model.
- [ ] C39: Validate with `ollama list`.
- [ ] C40: Confirm Ollama is bound to localhost only (no OLLAMA_HOST override).

### SMB Mounts
- [ ] C41: Install `cifs-utils`.
- [ ] C42: Create mount points `/mnt/smb/Ruben` and `/mnt/smb/Esme`.
- [ ] C43: Create `/etc/gastos-ia/smb-credentials` with `0600` permissions.
- [ ] C44: **[GATE]** User authorized /etc/fstab entries → "AUTORIZADO".
- [ ] C45: Add fstab entries with `nofail,x-systemd.automount`.
- [ ] C46: Run `sudo mount -a`.
- [ ] C47: Validate `mount | grep cifs` shows both mounts.
- [ ] C48: Validate `ls /mnt/smb/Ruben/pendientes` and `ls /mnt/smb/Esme/pendientes` work.

### Environment File
- [ ] C49: Create `/etc/gastos-ia/gastos-ia.env` with placeholder structure.
- [ ] C50: Set owner to `root:root` and permissions to `0600`.
- [ ] C51: Validate `ls -la /etc/gastos-ia/gastos-ia.env` shows `-rw------- 1 root root`.

### Systemd Service
- [ ] C52: Create `/etc/systemd/system/gastos-ia.service` with EnvironmentFile injection.
- [ ] C53: Run `systemctl daemon-reload`.
- [ ] C54: Enable `gastos-ia.service`.

### Auto-start
- [ ] C55: **[GATE]** User authorized VM auto-start configuration → "AUTORIZADO".
- [ ] C56: Run `Set-VM -AutomaticStartAction Start`.
- [ ] C57: Validate with `Get-VM`.

## Post-ejecución
- [ ] C58: All evidence JSON + MD files exist in `harness/evidence/fase4/`.
- [ ] C59: Each evidence file validated against its schema.
- [ ] C60: VM accessible via SSH at static IP.
- [ ] C61: HTTPS responds at https://gastos.local.
- [ ] C62: Ollama model available for inference.
- [ ] C63: SMB shares accessible from Ubuntu.
- [ ] C64: Environment file permissions are `0600 root:root`.
- [ ] C65: Systemd service enabled (will be started by skill-installer).
- [ ] C66: VM configured for auto-start with host.
- [ ] C67: No secrets or real credentials in any generated file or evidence.
