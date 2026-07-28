# Skill: skill-infrastructure

## Identity
As an infrastructure engineer for Gastos IA, you configure the Windows Server host and Ubuntu VM that will run the application stack. You never execute changes without explicit user authorization. You validate before and after every step.

## Context
This skill provisions the entire execution environment for Gastos IA on a Windows Server host with Hyper-V. It creates the Ubuntu Server VM, configures networking, HTTPS (Caddy), Ollama, SMB mounts, environment files, and systemd services. All secret values enter via environment variables; none are hardcoded.

This is a **Fase 4** skill. It runs before `skill-installer`.

**Key PRD sections:** 6 (Infraestructura), 6.1 (Máquina virtual), 6.2 (Red), 6.3 (HTTPS local), 19 (Variables de entorno), 19.4 (Servicios), 23 (Instalación), 24 (Inicio automático).

## Preconditions
- Fase 3 must be `completed`.
- Windows Server host with Hyper-V role available.
- Ethernet adapter connected.
- PostgreSQL instance accessible from target subnet.
- SMB shares `\\SERVIDOR\GastosIA\Ruben` and `\\SERVIDOR\GastosIA\Esme` already exist.
- Docker or podman not used for the application; FastAPI runs directly via systemd.
- User must be present and willing to authorize each infrastructure change with "AUTORIZADO".

## Execution

### Step 1: Validate Hyper-V is enabled and capable
1. Run validation command: `Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All`
2. Confirm State is `Enabled`.
3. Run: `Get-VMHost | Format-List Name, LogicalProcessorCount, MemoryCapacity`
4. Confirm at least 4 logical processors and 16 GB RAM available for host.
5. Run: `Get-VM | Format-Table Name, State` to list existing VMs.
6. Check for name collision: no existing VM named `GastosIA`.
7. **Present output to user and wait for "AUTORIZADO" before proceeding.**

### Step 2: Create external virtual switch
1. Identify active Ethernet adapter: `Get-NetAdapter -Physical | Where-Object Status -eq 'Up'`
2. Check no existing switch with same name: `Get-VMSwitch -Name "GastosIA-External"` should return nothing.
3. **Propose switch creation command:**
   ```powershell
   New-VMSwitch -Name "GastosIA-External" -NetAdapterName "<adapter>" -AllowManagementOS $true
   ```
4. **Wait for "AUTORIZADO".**
5. Execute and validate: `Get-VMSwitch -Name "GastosIA-External" | Format-List Name, SwitchType, NetAdapterInterfaceDescription`
6. Confirm management OS keeps connectivity by pinging gateway.

### Step 3: Create VM directory and VHDX
1. Verify `D:\Hyper-V\VirtualMachines\GastosIA` does not exist (or is empty):
   ```powershell
   Test-Path "D:\Hyper-V\VirtualMachines\GastosIA"
   ```
2. **Propose directory creation.** Wait for "AUTORIZADO".
3. Create: `New-Item -Path "D:\Hyper-V\VirtualMachines\GastosIA" -ItemType Directory -Force`
4. **Propose VHDX creation** (120 GB dynamic):
   ```powershell
   New-VHD -Path "D:\Hyper-V\VirtualMachines\GastosIA\GastosIA.vhdx" -SizeBytes 120GB -Dynamic
   ```
5. **Wait for "AUTORIZADO".**
6. Execute, then validate: `Get-VHD -Path "D:\Hyper-V\VirtualMachines\GastosIA\GastosIA.vhdx" | Format-List Path, Size, FileSize`

### Step 4: Create VM with 16 GB RAM / 4 vCPU
1. **Propose VM creation:**
   ```powershell
   New-VM -Name "GastosIA" `
     -MemoryStartupBytes 16GB `
     -VHDPath "D:\Hyper-V\VirtualMachines\GastosIA\GastosIA.vhdx" `
     -Generation 2 `
     -SwitchName "GastosIA-External"
   Set-VM -Name "GastosIA" -ProcessorCount 4
   Set-VM -Name "GastosIA" -StaticMemory
   ```
2. **Wait for "AUTORIZADO".**
3. Execute, then validate: `Get-VM -Name "GastosIA" | Format-List Name, State, MemoryStartup, ProcessorCount, Generation`
4. Confirm static memory and generation 2.

### Step 5: Download Ubuntu Server LTS ISO
1. Check if ISO already exists at `D:\Hyper-V\ISOs\ubuntu-server-lts.iso`.
2. If not, **propose download URL and destination.** Wait for "AUTORIZADO".
3. Download and validate SHA-256 against official Ubuntu hashes.
4. Attach ISO: `Add-VMDvdDrive -VMName "GastosIA" -Path "D:\Hyper-V\ISOs\ubuntu-server-lts.iso"`
5. Validate: `Get-VMDvdDrive -VMName "GastosIA"`

### Step 6: Configure static IP in Ubuntu (192.168.100.75)
Before any changes, validate the network:

1. **Network validation commands (run on host first, output required):**
   ```powershell
   # Show current IP config on Ethernet
   Get-NetIPAddress -InterfaceAlias "Ethernet*" -AddressFamily IPv4 | Format-List InterfaceAlias, IPAddress, PrefixLength

   # Show default gateway
   Get-NetRoute -DestinationPrefix "0.0.0.0/0" | Format-List DestinationPrefix, NextHop, InterfaceAlias

   # Show DNS servers
   Get-DnsClientServerAddress -InterfaceAlias "Ethernet*" | Format-List InterfaceAlias, ServerAddresses
   ```
2. **Validate proposed IP 192.168.100.75:**
   - Confirm subnet: `192.168.100.0/24` or similar.
   - Confirm gateway IP from output above.
   - Ping `192.168.100.75` to verify it's free.
   - Check ARP table: `arp -a | Select-String "192.168.100"`
   - Confirm it is OUTSIDE the DHCP range (consult with user if DHCP is active).
3. **Present full network analysis + proposed static config. Wait for "AUTORIZADO".**
4. During Ubuntu unattended install, pass static IP configuration via autoinstall.yaml or configure manually post-install.
5. After Ubuntu boots, validate from Ubuntu itself:
   ```bash
   ip addr show
   ip route show default
   ping -c 2 <gateway>
   ```

### Step 7: Install and configure Ubuntu Server unattended
1. Create `autoinstall.yaml` for Ubuntu Server LTS with:
   - English keyboard, UTC timezone.
   - Static IP configuration (from Step 6).
   - SSH server installed and enabled.
   - User `gastos-admin` created with SSH key or password.
   - Disk: use entire VHDX, LVM layout.
2. Serve `autoinstall.yaml` or embed in ISO copy.
3. Start VM: `Start-VM -Name "GastosIA"`
4. Connect to console or SSH after boot.
5. Validate: `ssh gastos-admin@192.168.100.75` works.

### Step 8: Install Caddy and configure HTTPS for gastos.local
1. Install Caddy on Ubuntu:
   ```bash
   sudo apt update && sudo apt install -y caddy
   ```
2. Create `/etc/caddy/Caddyfile`:
   ```caddy
   gastos.local {
       reverse_proxy localhost:8000
   }
   ```
3. **For self-signed cert, Caddy will auto-generate an internal certificate for `.local` domains.** No external CA needed.
4. Validate Caddy:
   ```bash
   sudo systemctl enable caddy --now
   sudo systemctl status caddy
   curl -k https://gastos.local
   ```
5. **Propose certificate trust script** for client machines. Wait for "AUTORIZADO" before generating/exporting the cert.

### Step 9: Install and configure Ollama as systemd service
1. Install Ollama:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```
2. Verify service:
   ```bash
   sudo systemctl status ollama
   ```
3. Pull model (Qwen3-VL:4b):
   ```bash
   ollama pull qwen3-vl:4b
   ```
4. Validate:
   ```bash
   ollama list
   ```
5. Ensure Ollama is bound to localhost only (default). Do not expose to network:
   ```bash
   grep -r "OLLAMA_HOST" /etc/systemd/system/ollama.service || echo "Using default (localhost only)"
   ```

### Step 10: Mount SMB shares via CIFS
1. Install cifs-utils:
   ```bash
   sudo apt install -y cifs-utils
   ```
2. Create mount points:
   ```bash
   sudo mkdir -p /mnt/smb/Ruben /mnt/smb/Esme
   ```
3. Create credentials file (outside repo, 0600):
   ```bash
   sudo mkdir -p /etc/gastos-ia
   sudo touch /etc/gastos-ia/smb-credentials
   sudo chmod 600 /etc/gastos-ia/smb-credentials
   ```
   Content (placeholder values only):
   ```text
   username=GASTOSIA_SMB_USERNAME
   password=GASTOSIA_SMB_PASSWORD
   ```
4. **Propose /etc/fstab entries.** Wait for "AUTORIZADO":
   ```text
   //SERVIDOR/GastosIA/Ruben  /mnt/smb/Ruben  cifs  credentials=/etc/gastos-ia/smb-credentials,iocharset=utf8,vers=3.0,nofail,x-systemd.automount  0  0
   //SERVIDOR/GastosIA/Esme   /mnt/smb/Esme   cifs  credentials=/etc/gastos-ia/smb-credentials,iocharset=utf8,vers=3.0,nofail,x-systemd.automount  0  0
   ```
5. Execute:
   ```bash
   sudo mount -a
   ```
6. Validate:
   ```bash
   mount | grep cifs
   ls /mnt/smb/Ruben/pendientes
   ls /mnt/smb/Esme/pendientes
   ```

### Step 11: Configure environment file
1. Create `/etc/gastos-ia/` if not already present.
2. Create `/etc/gastos-ia/gastos-ia.env` with placeholder structure (no real values):
   ```ini
   GASTOSIA_APP_ENV=production
   GASTOSIA_DATABASE_HOST=
   GASTOSIA_DATABASE_PORT=5432
   GASTOSIA_DATABASE_NAME=gastos_ia
   GASTOSIA_DATABASE_USER=gastos_app
   GASTOSIA_DATABASE_PASSWORD=
   GASTOSIA_SESSION_SECRET=
   GASTOSIA_SMB_USERNAME=
   GASTOSIA_SMB_PASSWORD=
   GASTOSIA_GOOGLE_CREDENTIALS_PATH=
   GASTOSIA_GOOGLE_SPREADSHEET_ID=
   ```
3. Set permissions:
   ```bash
   sudo chown root:root /etc/gastos-ia/gastos-ia.env
   sudo chmod 600 /etc/gastos-ia/gastos-ia.env
   ```
4. Validate: `ls -la /etc/gastos-ia/gastos-ia.env` shows `-rw------- 1 root root`.

### Step 12: Create systemd service for FastAPI
1. Create `/etc/systemd/system/gastos-ia.service`:
   ```ini
   [Unit]
   Description=Gastos IA FastAPI Application
   Requires=network-online.target postgresql.service
   After=network-online.target postgresql.service

   [Service]
   Type=simple
   User=gastos-admin
   Group=gastos-admin
   WorkingDirectory=/opt/gastos-ia
   EnvironmentFile=/etc/gastos-ia/gastos-ia.env
   ExecStart=/opt/gastos-ia/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
   Restart=always
   RestartSec=5
   LimitNOFILE=65536

   [Install]
   WantedBy=multi-user.target
   ```
2. Enable and validate (service won't start until app is deployed by `skill-installer`):
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable gastos-ia
   ```

### Step 13: Configure VM auto-start with host
1. **Propose auto-start configuration.** Wait for "AUTORIZADO":
   ```powershell
   Set-VM -Name "GastosIA" -AutomaticStartAction Start -AutomaticStartDelay 0
   Set-VM -Name "GastosIA" -AutomaticStopAction ShutDown
   ```
2. Execute on host.
3. Validate:
   ```powershell
   Get-VM -Name "GastosIA" | Format-List Name, AutomaticStartAction, AutomaticStopAction
   ```

## Authorization
This skill deals with production infrastructure. Every step marked with "AUTORIZADO" requires:
1. Clear description of the proposed change with rationale.
2. Actual validation command output shown in context.
3. User explicitly types "AUTORIZADO" (case-insensitive, must be exact).
4. After execution, validate the change worked and show the output.

The agent MUST NOT execute any infrastructure change without this authorization.

## Artifacts
- `evidence/fase4/validacion-hyperv.json` + `.md`
- `evidence/fase4/configuracion-red.json` + `.md`
- `evidence/fase4/creacion-vm.json` + `.md`
- `evidence/fase4/configuracion-caddy.json` + `.md`
- `evidence/fase4/configuracion-ollama.json` + `.md`
- `evidence/fase4/montaje-smb.json` + `.md`
- `evidence/fase4/archivo-entorno.json` + `.md`
- `evidence/fase4/servicio-systemd.json` + `.md`
- `evidence/fase4/inicio-automatico.json` + `.md`

Each JSON artifact follows `harness/config/schemas/evidence.schema.json`.
Each MD artifact follows `harness/config/schemas/evidence-markdown.schema.md`.

## Quality Criteria
- Hyper-V role confirmed enabled.
- VM created with correct specs (16 GB RAM, 4 vCPU, 120 GB VHDX, Gen 2).
- External virtual switch created and management OS retains connectivity.
- Ubuntu boots and is reachable via SSH.
- Static IP 192.168.100.75 confirmed free and configured.
- Caddy serves HTTPS at https://gastos.local (self-signed cert).
- Ollama installed, running, and `qwen3-vl:4b` model available.
- SMB shares mounted at `/mnt/smb/Ruben` and `/mnt/smb/Esme` and accessible.
- Environment file at `/etc/gastos-ia/gastos-ia.env` with `0600` permissions, owned by `root:root`.
- Systemd service `gastos-ia.service` created, enabled, with `EnvironmentFile` injection.
- VM set to auto-start with host.

## Edge Cases
- **Hyper-V not enabled:** Guide user to enable it via Windows Features, may require reboot. Document the `Enable-WindowsOptionalFeature` approach.
- **IP 192.168.100.75 in use:** Run `Test-Connection`, check ARP table. If occupied, propose an alternative in the same subnet and validate it similarly.
- **DHCP range overlap:** Ask user for DHCP scope (or check router). If the static IP falls inside DHCP range, warn about potential conflicts. Offer to configure a DHCP reservation or choose an IP outside the range.
- **SMB mount failure:** Verify SMB version compatibility (try `vers=3.0`, `vers=2.1`, `vers=2.0`). Check credentials and server reachability. Validate DNS resolution of `SERVIDOR`.
- **Caddy cert issues with `.local` domain:** Caddy will use its internal CA for `.local`. Ensure client machines trust it (separate script). If `.local` resolution fails, test with `https://192.168.100.75` and configure hosts file as fallback.
- **VM won't boot:** Check secure boot settings (Generation 2). Disable secure boot if Ubuntu ISO doesn't support it. Also try `Set-VMFirmware -VMName "GastosIA" -EnableSecureBoot Off`.
- **Ollama pull fails (offline):** Pre-download the model on a machine with internet, transfer it to the VM.

## References
- PRD sections: 6 (Infraestructura), 6.1 (Máquina virtual), 6.2 (Red), 6.3 (HTTPS local), 19 (Variables de entorno), 19.4 (Servicios), 23 (Instalación), 24 (Inicio automático).
- `skill-fase4-instalador` (orchestrator that invokes this skill).
- `skill-installer` (runs after this skill, deploys the application).
- `skill-git-safety` (for commits after completing this skill).
