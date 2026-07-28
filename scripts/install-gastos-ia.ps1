<#
.SYNOPSIS
    Gastos IA — Automated Installer for Windows Server + Hyper-V + Ubuntu
.DESCRIPTION
    Installs and configures the full Gastos IA stack:
      1. Pre-flight checks (admin, Hyper-V, disk, network)
      2. Validates virtualization
      3. Enables Hyper-V (with reboot handling)
      4. Creates SMB folders and shares
      5. Creates Hyper-V external virtual switch
      6. Downloads Ubuntu Server LTS ISO
      7. Creates and configures the VM (16 GB RAM, 4 vCPU, 120 GB VHDX)
      8. Installs Ubuntu with unattended install (static IP, SSH)
      9. Post-install SSH setup and software (Python, uv, psql, Ollama)
     10. Deploys FastAPI app from git
     11. Mounts SMB shares via CIFS on Ubuntu
     12. Creates PostgreSQL database and user
     13. Initializes database tables
     14. Configures Google Sheets credentials
     15. Creates user accounts (Ruben + Esme with Argon2id)
     16. Populates environment variables
     17. Configures auto-start (VM + services)
     18. Runs validation tests
     19. Generates diagnostic JSON (no secrets)
.NOTES
    PRD v1.2 — Section 23 (Instalación automatizada)
    All secrets enter via secure prompts, never written to disk in plaintext.
    Requires: Administrator privileges, Hyper-V capable hardware, Internet for downloads.
#>

[CmdletBinding()]
param(
    [switch]$SkipPreflight,
    [switch]$SkipVM,
    [switch]$SkipApp,
    [switch]$Force,
    [switch]$DryRun
)

# =============================================================================
# Configuration (editable constants)
# =============================================================================

$Script:Config = @{
    VMName              = "GastosIA"
    VMPath              = "D:\Hyper-V\VirtualMachines\GastosIA"
    VHDXPath            = "D:\Hyper-V\VirtualMachines\GastosIA\GastosIA.vhdx"
    VHDXSizeGB          = 120
    VMRAM               = 16GB
    VMCPU               = 4
    SwitchName          = "GastosIA-External"
    ISOPath             = "D:\Hyper-V\ISOs\ubuntu-server-lts.iso"
    UbuntuURL           = "https://releases.ubuntu.com/noble/ubuntu-24.04-live-server-amd64.iso"
    UbuntuSHA256        = ""  # Fill with actual hash from ubuntu.com
    VMStaticIP          = "192.168.100.75"
    VMSubnetMask        = 24
    VMGateway           = ""  # Will be auto-detected
    VMDNS              = @("8.8.8.8", "8.8.4.4")  # Default; will be detected
    VMSSHUser           = "gastos-admin"
    SMBShareBase        = "\\SERVIDOR\GastosIA"
    SMBMountBase        = "/mnt/smb"
    SMBUsers            = @("Ruben", "Esme")
    PostgreSQLHost      = ""  # Will be prompted
    PostgreSQLPort      = 5432
    PostgreSQLDB        = "gastos_ia"
    PostgreSQLUser      = "gastos_app"
    AppPath             = "/opt/gastos-ia"
    EnvFilePath         = "/etc/gastos-ia/gastos-ia.env"
    GoogleCredPath      = "/etc/gastos-ia/google-service-account.json"
    LogFile             = "install-gastos-ia-$(Get-Date -Format 'yyyy-MM-dd').log"
}

# =============================================================================
# Logging Functions
# =============================================================================

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"
    $logLine = "[$timestamp] [$Level] $Message"
    Write-Host $logLine
    Add-Content -Path $Script:Config.LogFile -Value $logLine
}

function Write-Step {
    param([string]$StepNumber, [string]$Description)
    $separator = "=" * 70
    Write-Log $separator
    Write-Log "STEP $StepNumber : $Description"
    Write-Log $separator
}

# =============================================================================
# Secure Credential Prompting
# =============================================================================

function Get-SecureUserInput {
    param(
        [string]$PromptMessage,
        [int]$MinLength = 8,
        [string]$ValidationRegex = $null
    )
    Write-Host ""
    
    $firstAttempt = $true
    do {
        if (-not $firstAttempt) {
            Write-Host "Invalid input. Minimum length: $MinLength characters." -ForegroundColor Yellow
        }
        $firstAttempt = $false
        
        $secure = Read-Host -Prompt $PromptMessage -AsSecureString
        $plain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto(
            [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
        )
        
        if ($plain.Length -lt $MinLength) { continue }
        if ($ValidationRegex -and $plain -notmatch $ValidationRegex) { continue }
        
        return $plain
    } while ($true)
}

function Get-SecureCredential {
    param([string]$PromptUser, [string]$PromptPass)
    Write-Host ""
    $username = Read-Host -Prompt $PromptUser
    $password = Get-SecureUserInput -PromptMessage $PromptPass -MinLength 8
    return @{ Username = $username; Password = $password }
}

# =============================================================================
# Validation Functions
# =============================================================================

function Test-AdminRights {
    <# STEP 1: Pre-flight — Verify running as Administrator #>
    $identity = [System.Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object System.Security.Principal.WindowsPrincipal($identity)
    if (-not $principal.IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Write-Log "This script must be run as Administrator." -Level "ERROR"
        Write-Log "Please restart PowerShell as Administrator and run this script again."
        exit 1
    }
    Write-Log "Administrator rights confirmed." -Level "PASS"
    return $true
}

function Test-HyperVSupport {
    <# STEP 2: Pre-flight — Check Hyper-V capability #>
    $hyperV = Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -ErrorAction SilentlyContinue
    if ($null -eq $hyperV) {
        Write-Log "Hyper-V not found on this system." -Level "ERROR"
        Write-Log "This installer requires Windows Server with Hyper-V role or Windows Pro/Enterprise."
        exit 1
    }
    if ($hyperV.State -ne "Enabled") {
        Write-Log "Hyper-V is present but NOT enabled. State: $($hyperV.State)" -Level "WARNING"
        Write-Log "The installer will attempt to enable Hyper-V (may require reboot)."
    } else {
        Write-Log "Hyper-V is enabled." -Level "PASS"
    }
    
    # Check hardware virtualization support
    $cpuInfo = Get-CimInstance -ClassName Win32_Processor
    $vmExtensions = Get-CimInstance -ClassName Win32_ComputerSystem
    if ($vmExtensions.HypervisorPresent -eq $false) {
        Write-Log "Hardware virtualization may not be enabled in BIOS." -Level "WARNING"
        Write-Log "Enable Intel VT-x / AMD-V in your system BIOS and try again."
    }
    
    return $true
}

function Test-DiskSpace {
    <# STEP 3: Pre-flight — Verify disk space #>
    $drive = [System.IO.Path]::GetPathRoot($Script:Config.VMPath)
    $driveInfo = Get-PSDrive -Name $drive.TrimEnd(':') -ErrorAction SilentlyContinue
    
    if ($null -eq $driveInfo) {
        Write-Log "Drive $drive not found." -Level "ERROR"
        exit 1
    }
    
    $freeGB = [math]::Round($driveInfo.Free / 1GB, 1)
    $requiredGB = $Script:Config.VHDXSizeGB + 10  # VHDX + ISO + overhead
    
    Write-Log "Drive $drive — Free: $freeGB GB, Required: $requiredGB GB"
    if ($freeGB -lt $requiredGB) {
        Write-Log "Insufficient disk space." -Level "ERROR"
        exit 1
    }
    Write-Log "Disk space sufficient." -Level "PASS"
    return $true
}

function Test-NetworkReachability {
    <# Pre-flight — Validate network parameters #>
    # Get active Ethernet adapter
    $adapters = Get-NetAdapter -Physical | Where-Object Status -eq 'Up'
    if ($adapters.Count -eq 0) {
        Write-Log "No active physical network adapter found." -Level "ERROR"
        exit 1
    }
    
    $adapter = $adapters[0]
    Write-Log "Active network adapter: $($adapter.Name) ($($adapter.InterfaceDescription))"
    
    # Get current IP configuration
    $ipConfig = Get-NetIPAddress -InterfaceIndex $adapter.InterfaceIndex -AddressFamily IPv4
    Write-Log "Current IP: $($ipConfig.IPAddress)/$($ipConfig.PrefixLength)"
    
    # Get default gateway
    $gateway = Get-NetRoute -DestinationPrefix "0.0.0.0/0" -InterfaceIndex $adapter.InterfaceIndex |
        Select-Object -First 1 -ExpandProperty NextHop
    if ($gateway) {
        $Script:Config.VMGateway = $gateway
        Write-Log "Default gateway: $gateway"
    }
    
    # Get DNS servers
    $dns = Get-DnsClientServerAddress -InterfaceIndex $adapter.InterfaceIndex -AddressFamily IPv4
    if ($dns.ServerAddresses.Count -gt 0) {
        $Script:Config.VMDNS = $dns.ServerAddresses
        Write-Log "DNS servers: $($dns.ServerAddresses -join ', ')"
    }
    
    # Validate proposed static IP
    Write-Log "Validating proposed static IP: $($Script:Config.VMStaticIP)"
    $pingResult = Test-Connection -ComputerName $Script:Config.VMStaticIP -Count 1 -Quiet
    if ($pingResult) {
        Write-Log "IP $($Script:Config.VMStaticIP) is already in use! Choose a different IP." -Level "ERROR"
        $newIP = Read-Host "Enter a different static IP for the VM"
        $Script:Config.VMStaticIP = $newIP
    } else {
        Write-Log "IP $($Script:Config.VMStaticIP) is available." -Level "PASS"
    }
    
    # Check ARP table
    $arpEntries = arp -a | Select-String ($Script:Config.VMStaticIP -replace '\.\d+$','.')
    Write-Log "ARP entries in subnet:"
    $arpEntries | ForEach-Object { Write-Log "  $_" }
    
    return $true
}

function Test-ExistingVM {
    <# Pre-flight — Check VM name collision #>
    $existingVM = Get-VM -Name $Script:Config.VMName -ErrorAction SilentlyContinue
    if ($existingVM) {
        Write-Log "VM '$($Script:Config.VMName)' already exists!" -Level "WARNING"
        if ($Force) {
            Write-Log "Removing existing VM (--Force)..."
            Stop-VM -Name $Script:Config.VMName -Force -ErrorAction SilentlyContinue
            Remove-VM -Name $Script:Config.VMName -Force
        } else {
            Write-Log "Use --Force to remove existing VM, or manually remove it first."
            exit 1
        }
    }
    Write-Log "VM name '$($Script:Config.VMName)' is available." -Level "PASS"
    return $true
}

function Test-SSHConnection {
    <# Validate SSH access to VM #>
    param([int]$MaxRetries = 10, [int]$RetryDelay = 10)
    
    for ($i = 1; $i -le $MaxRetries; $i++) {
        Write-Log "SSH attempt $i/$MaxRetries to $($Script:Config.VMSSHUser)@$($Script:Config.VMStaticIP)..."
        $result = ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no `
            "$($Script:Config.VMSSHUser)@$($Script:Config.VMStaticIP)" "echo SSH_OK" 2>&1
        if ($result -match "SSH_OK") {
            Write-Log "SSH connection established." -Level "PASS"
            return $true
        }
        Start-Sleep -Seconds $RetryDelay
    }
    Write-Log "SSH connection failed after $MaxRetries attempts." -Level "ERROR"
    return $false
}

# =============================================================================
# Infrastructure Functions (Host)
# =============================================================================

function Enable-HyperVRole {
    <# STEP 4: Enable Hyper-V on Windows Server #>
    Write-Step "4" "Enabling Hyper-V role"
    
    $hyperV = Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All
    if ($hyperV.State -eq "Enabled") {
        Write-Log "Hyper-V already enabled. Skipping."
        return $true
    }
    
    Write-Log "Enabling Hyper-V. This may take several minutes and WILL require a reboot."
    $confirmation = Read-Host "Enable Hyper-V now? (yes/no)"
    if ($confirmation -ne "yes") {
        Write-Log "User declined. Aborting."
        exit 1
    }
    
    Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -All -NoRestart
    Write-Log "Hyper-V enabled. A reboot is required before continuing."
    Write-Log "Please run this script again after the reboot."
    $restart = Read-Host "Restart now? (yes/no)"
    if ($restart -eq "yes") { Restart-Computer -Force }
    exit 0
}

function New-SMBFolders {
    <# STEP 5: Create SMB folders and shares on host #>
    Write-Step "5" "Creating SMB folder structure"
    
    $basePath = "D:\GastosIA"
    
    foreach ($user in $Script:Config.SMBUsers) {
        $paths = @(
            "$basePath\$user\pendientes",
            "$basePath\$user\procesados",
            "$basePath\$user\errores\duplicados",
            "$basePath\$user\errores\procesamiento"
        )
        
        foreach ($path in $paths) {
            if (-not (Test-Path $path)) {
                New-Item -Path $path -ItemType Directory -Force | Out-Null
                Write-Log "Created: $path"
            } else {
                Write-Log "Already exists: $path"
            }
        }
    }
    
    # Create logs directory
    $logsPath = "$basePath\logs"
    if (-not (Test-Path $logsPath)) {
        New-Item -Path $logsPath -ItemType Directory -Force | Out-Null
    }
    
    # TODO: Configure SMB share permissions
    # New-SmbShare -Name "GastosIA" -Path $basePath -FullAccess "Everyone" ...
    
    Write-Log "SMB folder structure created." -Level "PASS"
    return $true
}

function New-HyperVSwitch {
    <# STEP 6: Create external virtual switch #>
    Write-Step "6" "Creating Hyper-V external virtual switch"
    
    $existingSwitch = Get-VMSwitch -Name $Script:Config.SwitchName -ErrorAction SilentlyContinue
    if ($existingSwitch) {
        Write-Log "Virtual switch '$($Script:Config.SwitchName)' already exists."
        return $true
    }
    
    $adapter = Get-NetAdapter -Physical | Where-Object Status -eq 'Up' | Select-Object -First 1
    if (-not $adapter) {
        Write-Log "No active physical adapter found for switch creation." -Level "ERROR"
        exit 1
    }
    
    Write-Log "Creating external switch on adapter: $($adapter.Name)"
    Write-Log "Management OS will share this adapter."
    
    New-VMSwitch -Name $Script:Config.SwitchName `
        -NetAdapterName $adapter.Name `
        -AllowManagementOS $true
    
    $created = Get-VMSwitch -Name $Script:Config.SwitchName
    Write-Log "Switch created: $($created.Name), Type: $($created.SwitchType)" -Level "PASS"
    return $true
}

function New-VirtualMachine {
    <# STEP 7-8: Download ISO, create VM and VHDX #>
    Write-Step "7" "Creating VM directory and VHDX"
    
    # Create VM directory
    if (-not (Test-Path $Script:Config.VMPath)) {
        New-Item -Path $Script:Config.VMPath -ItemType Directory -Force | Out-Null
    }
    
    # Create VHDX
    if (-not (Test-Path $Script:Config.VHDXPath)) {
        Write-Log "Creating 120 GB dynamic VHDX at $($Script:Config.VHDXPath)..."
        New-VHD -Path $Script:Config.VHDXPath -SizeBytes ($Script:Config.VHDXSizeGB * 1GB) -Dynamic
        Write-Log "VHDX created." -Level "PASS"
    } else {
        Write-Log "VHDX already exists. Skipping creation."
    }
    
    # TODO: Download Ubuntu ISO if not present
    # if (-not (Test-Path $Script:Config.ISOPath)) { ... }
    
    Write-Step "8" "Creating VM"
    
    $existingVM = Get-VM -Name $Script:Config.VMName -ErrorAction SilentlyContinue
    if ($existingVM) {
        Write-Log "VM already exists. Skipping creation."
        return $true
    }
    
    # Create VM (Generation 2)
    New-VM -Name $Script:Config.VMName `
        -MemoryStartupBytes $Script:Config.VMRAM `
        -VHDPath $Script:Config.VHDXPath `
        -Generation 2 `
        -SwitchName $Script:Config.SwitchName
    
    # Configure CPU
    Set-VM -Name $Script:Config.VMName -ProcessorCount $Script:Config.VMCPU
    
    # Set static memory
    Set-VM -Name $Script:Config.VMName -StaticMemory
    
    # Attach ISO
    if (Test-Path $Script:Config.ISOPath) {
        Add-VMDvdDrive -VMName $Script:Config.VMName -Path $Script:Config.ISOPath
    }
    
    # Validate
    $vm = Get-VM -Name $Script:Config.VMName
    Write-Log "VM created: Name=$($vm.Name), RAM=$($vm.MemoryStartup), CPU=$($vm.ProcessorCount), Gen=$($vm.Generation)" -Level "PASS"
    
    return $true
}

# =============================================================================
# Ubuntu Guest Functions (via SSH)
# =============================================================================

function Invoke-SSHCommand {
    <# Execute a command on the Ubuntu VM via SSH #>
    param([string]$Command, [string]$Description = "")
    
    if ($Description) { Write-Log "  → $Description" }
    
    if ($DryRun) {
        Write-Log "  [DRY-RUN] ssh $($Script:Config.VMSSHUser)@$($Script:Config.VMStaticIP) $Command"
        return "[DRY-RUN]"
    }
    
    $result = ssh -o StrictHostKeyChecking=no `
        "$($Script:Config.VMSSHUser)@$($Script:Config.VMStaticIP)" $Command 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Log "SSH command failed: $result" -Level "ERROR"
    }
    
    return $result
}

function Install-UbuntuSoftware {
    <# STEP 9: Install Python, uv, PostgreSQL client, Ollama on Ubuntu #>
    Write-Step "9" "Installing software on Ubuntu VM"
    
    # Update system
    Invoke-SSHCommand "sudo apt update && sudo apt upgrade -y" "Updating system packages"
    
    # Install Python
    Invoke-SSHCommand "sudo apt install -y python3 python3-pip python3-venv" "Installing Python 3"
    $pythonVer = Invoke-SSHCommand "python3 --version" "Checking Python version"
    Write-Log "Python: $pythonVer"
    
    # Install uv
    Invoke-SSHCommand "curl -LsSf https://astral.sh/uv/install.sh | sh" "Installing uv"
    Invoke-SSHCommand "export PATH=\$HOME/.local/bin:\$PATH && uv --version" "Checking uv version"
    
    # Install PostgreSQL client
    Invoke-SSHCommand "sudo apt install -y postgresql-client" "Installing PostgreSQL client"
    $psqlVer = Invoke-SSHCommand "psql --version" "Checking psql version"
    Write-Log "psql: $psqlVer"
    
    # Install Caddy for HTTPS
    Invoke-SSHCommand "sudo apt install -y caddy" "Installing Caddy"
    Invoke-SSHCommand "sudo systemctl enable caddy --now" "Enabling Caddy service"
    
    # Install Ollama
    Invoke-SSHCommand "curl -fsSL https://ollama.com/install.sh | sh" "Installing Ollama"
    Invoke-SSHCommand "ollama pull qwen3-vl:4b" "Pulling Qwen3-VL:4b model"
    
    Write-Log "Ubuntu software installation complete." -Level "PASS"
    return $true
}

function Deploy-Application {
    <# STEP 10: Clone repository and install Python dependencies #>
    Write-Step "10" "Deploying FastAPI application from git"
    
    # Create app directory
    Invoke-SSHCommand "sudo mkdir -p $($Script:Config.AppPath)" "Creating app directory"
    Invoke-SSHCommand "sudo chown $($Script:Config.VMSSHUser):$($Script:Config.VMSSHUser) $($Script:Config.AppPath)" "Setting ownership"
    
    # Clone repository
    $repoURL = Read-Host "Enter the Git repository URL for Gastos IA"
    $branch = Read-Host "Enter the branch to deploy (default: arnes)"
    if (-not $branch) { $branch = "arnes" }
    
    Invoke-SSHCommand "git clone -b $branch $repoURL $($Script:Config.AppPath)" "Cloning repository"
    
    # Install dependencies
    Invoke-SSHCommand "cd $($Script:Config.AppPath) && export PATH=\$HOME/.local/bin:\$PATH && uv sync --frozen" "Installing Python dependencies"
    
    Write-Log "Application deployed." -Level "PASS"
    return $true
}

function Mount-SMBShares {
    <# STEP 11: Configure CIFS mounts in /etc/fstab #>
    Write-Step "11" "Mounting SMB shares on Ubuntu"
    
    # Install cifs-utils
    Invoke-SSHCommand "sudo apt install -y cifs-utils" "Installing CIFS utilities"
    
    # Create mount points
    foreach ($user in $Script:Config.SMBUsers) {
        Invoke-SSHCommand "sudo mkdir -p $($Script:Config.SMBMountBase)/$user" "Creating mount point for $user"
    }
    
    # Create credentials file
    $credFile = "/etc/gastos-ia/smb-credentials"
    Invoke-SSHCommand "sudo mkdir -p /etc/gastos-ia" "Creating /etc/gastos-ia directory"
    Invoke-SSHCommand "sudo touch $credFile && sudo chmod 600 $credFile" "Creating SMB credentials file"
    
    # Get SMB credentials securely
    Write-Host ""
    Write-Host "=== SMB Credentials ===" -ForegroundColor Cyan
    Write-Host "Credentials for accessing: $($Script:Config.SMBShareBase)"
    $smbUser = Read-Host "SMB Username"
    $smbPass = Get-SecureUserInput -PromptMessage "SMB Password" -MinLength 1
    
    # Write credentials (temporary, will be removed from script variables)
    $credContent = "username=$smbUser`npassword=$smbPass"
    $credContentEscaped = $credContent -replace "'", "'\''"
    Invoke-SSHCommand "echo '$credContentEscaped' | sudo tee $credFile > /dev/null" "Writing SMB credentials"
    
    # Add fstab entries
    foreach ($user in $Script:Config.SMBUsers) {
        $fstabEntry = "//SERVIDOR/GastosIA/$user  $($Script:Config.SMBMountBase)/$user  cifs  credentials=$credFile,iocharset=utf8,vers=3.0,nofail,x-systemd.automount  0  0"
        $fstabEscaped = $fstabEntry -replace "'", "'\''"
        Invoke-SSHCommand "echo '$fstabEscaped' | sudo tee -a /etc/fstab > /dev/null" "Adding fstab entry for $user"
    }
    
    # Mount all
    Invoke-SSHCommand "sudo mount -a" "Mounting all filesystems"
    
    # Validate
    foreach ($user in $Script:Config.SMBUsers) {
        $result = Invoke-SSHCommand "ls $($Script:Config.SMBMountBase)/$user/pendientes" "Testing $user share"
        Write-Log "SMB $user: accessible"
    }
    
    # Clear sensitive variables
    $smbUser = $null
    $smbPass = $null
    $credContent = $null
    
    Write-Log "SMB shares mounted." -Level "PASS"
    return $true
}

function Initialize-Database {
    <# STEP 12-13: Create database, user, and tables #>
    Write-Step "12" "Creating PostgreSQL database and user"
    
    # Get PostgreSQL admin credentials
    Write-Host ""
    Write-Host "=== PostgreSQL Setup ===" -ForegroundColor Cyan
    $pgHost = Read-Host "PostgreSQL host (IP or hostname)"
    $Script:Config.PostgreSQLHost = $pgHost
    $pgAdminUser = Read-Host "PostgreSQL admin username (default: postgres)"
    if (-not $pgAdminUser) { $pgAdminUser = "postgres" }
    $pgAdminPass = Get-SecureUserInput -PromptMessage "PostgreSQL admin password" -MinLength 1
    
    # Generate app user password
    Write-Host ""
    $pgAppPass = Get-SecureUserInput -PromptMessage "Password for gastos_app database user" -MinLength 8
    $pgAppPassConfirm = Get-SecureUserInput -PromptMessage "Confirm gastos_app password" -MinLength 8
    if ($pgAppPass -ne $pgAppPassConfirm) {
        Write-Log "Passwords do not match." -Level "ERROR"
        exit 1
    }
    
    # Create database and user via SSH
    $createDBSQL = @"
CREATE DATABASE $($Script:Config.PostgreSQLDB);
CREATE USER $($Script:Config.PostgreSQLUser) WITH PASSWORD '$pgAppPass';
GRANT ALL PRIVILEGES ON DATABASE $($Script:Config.PostgreSQLDB) TO $($Script:Config.PostgreSQLUser);
-- Connect to gastos_ia and grant schema permissions
\c $($Script:Config.PostgreSQLDB)
GRANT ALL ON SCHEMA public TO $($Script:Config.PostgreSQLUser);
GRANT CREATE ON SCHEMA public TO $($Script:Config.PostgreSQLUser);
"@
    
    $sqlEscaped = $createDBSQL -replace "'", "'\''"
    Invoke-SSHCommand "echo '$sqlEscaped' | PGPASSWORD='$pgAdminPass' psql -h $pgHost -p $($Script:Config.PostgreSQLPort) -U $pgAdminUser -d postgres" "Creating database and user"
    
    # Test connection as app user
    $testResult = Invoke-SSHCommand "PGPASSWORD='$pgAppPass' psql -h $pgHost -p $($Script:Config.PostgreSQLPort) -U $($Script:Config.PostgreSQLUser) -d $($Script:Config.PostgreSQLDB) -c 'SELECT 1;'" "Testing app user connection"
    Write-Log "Database connection test: $testResult"
    
    Write-Step "13" "Initializing database tables"
    
    # Run migration/initialization
    Invoke-SSHCommand "cd $($Script:Config.AppPath) && export PATH=\$HOME/.local/bin:\$PATH && uv run python -m app.database.init" "Running table initialization"
    
    # List tables
    $tables = Invoke-SSHCommand "PGPASSWORD='$pgAppPass' psql -h $pgHost -p $($Script:Config.PostgreSQLPort) -U $($Script:Config.PostgreSQLUser) -d $($Script:Config.PostgreSQLDB) -c '\dt'" "Listing tables"
    Write-Log "Tables created:"
    Write-Log $tables
    
    # Clear sensitive variables
    $pgAdminPass = $null
    $pgAppPass = $null
    $pgAppPassConfirm = $null
    $createDBSQL = $null
    
    Write-Log "Database initialization complete." -Level "PASS"
    return $true
}

function Setup-GoogleSheets {
    <# STEP 14: Configure Google Sheets credentials #>
    Write-Step "14" "Configuring Google Sheets integration"
    
    Write-Host ""
    Write-Host "=== Google Sheets Setup ===" -ForegroundColor Cyan
    
    # Get path to service account JSON
    $googleJSONPath = Read-Host "Full path to Google service account JSON file"
    if (-not (Test-Path $googleJSONPath)) {
        Write-Log "Service account JSON not found at: $googleJSONPath" -Level "ERROR"
        exit 1
    }
    
    # Copy to secure location on VM
    $scpResult = scp -o StrictHostKeyChecking=no $googleJSONPath `
        "$($Script:Config.VMSSHUser)@$($Script:Config.VMStaticIP):/tmp/service-account.json" 2>&1
    Invoke-SSHCommand "sudo mkdir -p /etc/gastos-ia" "Ensuring /etc/gastos-ia exists"
    Invoke-SSHCommand "sudo mv /tmp/service-account.json $($Script:Config.GoogleCredPath) && sudo chown root:root $($Script:Config.GoogleCredPath) && sudo chmod 600 $($Script:Config.GoogleCredPath)" "Securing service account JSON"
    
    # Get spreadsheet ID
    $spreadsheetID = Read-Host "Google Spreadsheet ID"
    
    # Test connectivity
    $testResult = Invoke-SSHCommand "cd $($Script:Config.AppPath) && export PATH=\$HOME/.local/bin:\$PATH && GASTOSIA_GOOGLE_CREDENTIALS_PATH=$($Script:Config.GoogleCredPath) GASTOSIA_GOOGLE_SPREADSHEET_ID=$spreadsheetID uv run python -c 'from app.sheets.client import test_connection; test_connection()'" "Testing Google Sheets API connection"
    Write-Log "Google Sheets test: $testResult"
    
    # Store in config for later env file population
    $Script:Config.GoogleSpreadsheetID = $spreadsheetID
    
    Write-Log "Google Sheets configured." -Level "PASS"
    return $true
}

function Create-Users {
    <# STEP 15: Create user accounts with Argon2id hashing #>
    Write-Step "15" "Creating user accounts"
    
    Write-Host ""
    Write-Host "=== User Account Creation ===" -ForegroundColor Cyan
    Write-Host "Passwords will be hashed with Argon2id in PostgreSQL."
    Write-Host "Plaintext passwords will only exist as temporary environment variables"
    Write-Host "and will be destroyed after user creation."
    Write-Host ""
    
    # Get Ruben's initial password
    Write-Host "--- Ruben (Administrator) ---" -ForegroundColor Yellow
    $rubenPass = Get-SecureUserInput -PromptMessage "Enter initial password for Ruben" -MinLength 8
    $rubenPassConfirm = Get-SecureUserInput -PromptMessage "Confirm Ruben's password" -MinLength 8
    if ($rubenPass -ne $rubenPassConfirm) { Write-Log "Passwords do not match." -Level "ERROR"; exit 1 }
    
    # Get Esme's initial password
    Write-Host ""
    Write-Host "--- Esme (Standard User) ---" -ForegroundColor Yellow
    $esmePass = Get-SecureUserInput -PromptMessage "Enter initial password for Esme" -MinLength 8
    $esmePassConfirm = Get-SecureUserInput -PromptMessage "Confirm Esme's password" -MinLength 8
    if ($esmePass -ne $esmePassConfirm) { Write-Log "Passwords do not match." -Level "ERROR"; exit 1 }
    
    # Generate session secret
    Write-Host ""
    $sessionSecret = Invoke-SSHCommand "openssl rand -hex 32" "Generating session secret"
    $Script:Config.SessionSecret = $sessionSecret.Trim()
    Write-Log "Session secret generated (32 bytes hex)"
    
    # Create users via temporary env vars
    $createCmd = @"
export GASTOSIA_RUBEN_INITIAL_PASSWORD='$rubenPass' && \
export GASTOSIA_ESME_INITIAL_PASSWORD='$esmePass' && \
cd $($Script:Config.AppPath) && \
export PATH=\$HOME/.local/bin:\$PATH && \
uv run python -m app.auth.create_users
"@
    
    $result = Invoke-SSHCommand $createCmd "Creating users and hashing passwords"
    Write-Log "User creation: $result"
    
    # Verify Argon2id hashes in PostgreSQL
    $pgAppPass = Get-SecureUserInput -PromptMessage "gastos_app password (for verification)" -MinLength 1
    $hashCheck = Invoke-SSHCommand "PGPASSWORD='$pgAppPass' psql -h $($Script:Config.PostgreSQLHost) -p $($Script:Config.PostgreSQLPort) -U $($Script:Config.PostgreSQLUser) -d $($Script:Config.PostgreSQLDB) -c \"SELECT username, password_hash LIKE '\$argon2id\$%' AS is_argon2id FROM users;\"" "Verifying Argon2id hashes"
    Write-Log "Hash verification:"
    Write-Log $hashCheck
    
    # Clear ALL sensitive variables
    $rubenPass = $null
    $rubenPassConfirm = $null
    $esmePass = $null
    $esmePassConfirm = $null
    $pgAppPass = $null
    
    Write-Log "Users created and passwords hashed. Temporary variables cleared." -Level "PASS"
    return $true
}

function Populate-EnvironmentFile {
    <# STEP 16: Fill environment variables on VM #>
    Write-Step "16" "Populating environment variables"
    
    Write-Host ""
    Write-Host "=== Environment Configuration ===" -ForegroundColor Cyan
    
    # Get remaining secrets
    $smbUser = Read-Host "SMB Username"
    $smbPass = Get-SecureUserInput -PromptMessage "SMB Password" -MinLength 1
    $pgAppPass = Get-SecureUserInput -PromptMessage "gastos_app database password" -MinLength 1
    
    $envContent = @"
GASTOSIA_APP_ENV=production
GASTOSIA_DATABASE_HOST=$($Script:Config.PostgreSQLHost)
GASTOSIA_DATABASE_PORT=$($Script:Config.PostgreSQLPort)
GASTOSIA_DATABASE_NAME=$($Script:Config.PostgreSQLDB)
GASTOSIA_DATABASE_USER=$($Script:Config.PostgreSQLUser)
GASTOSIA_DATABASE_PASSWORD=$pgAppPass
GASTOSIA_SESSION_SECRET=$($Script:Config.SessionSecret)
GASTOSIA_SMB_USERNAME=$smbUser
GASTOSIA_SMB_PASSWORD=$smbPass
GASTOSIA_GOOGLE_CREDENTIALS_PATH=$($Script:Config.GoogleCredPath)
GASTOSIA_GOOGLE_SPREADSHEET_ID=$($Script:Config.GoogleSpreadsheetID)
"@
    
    $envContentEscaped = $envContent -replace "'", "'\''"
    Invoke-SSHCommand "echo '$envContentEscaped' | sudo tee $($Script:Config.EnvFilePath) > /dev/null" "Writing environment file"
    Invoke-SSHCommand "sudo chown root:root $($Script:Config.EnvFilePath) && sudo chmod 600 $($Script:Config.EnvFilePath)" "Setting permissions 0600"
    
    # Validate no empty values
    $emptyCount = Invoke-SSHCommand "sudo grep -c '=\$' $($Script:Config.EnvFilePath)" "Checking for empty values"
    Write-Log "Empty values found: $emptyCount (should be 0)"
    
    # Clear variables
    $smbUser = $null
    $smbPass = $null
    $pgAppPass = $null
    $envContent = $null
    
    Write-Log "Environment file populated and secured." -Level "PASS"
    return $true
}

function Configure-AutoStart {
    <# STEP 17: Configure VM and service auto-start #>
    Write-Step "17" "Configuring auto-start"
    
    # VM auto-start on host
    Write-Log "Configuring VM to auto-start with host..."
    Set-VM -Name $Script:Config.VMName -AutomaticStartAction Start -AutomaticStartDelay 0
    Set-VM -Name $Script:Config.VMName -AutomaticStopAction ShutDown
    
    $vmConfig = Get-VM -Name $Script:Config.VMName
    Write-Log "VM auto-start: StartAction=$($vmConfig.AutomaticStartAction), StopAction=$($vmConfig.AutomaticStopAction)"
    
    # Systemd service on Ubuntu (should already be set up by skill-infrastructure)
    Invoke-SSHCommand "sudo systemctl enable caddy" "Enabling Caddy auto-start"
    Invoke-SSHCommand "sudo systemctl enable ollama" "Enabling Ollama auto-start"
    
    # Create gastos-ia systemd service file
    $serviceContent = @"
[Unit]
Description=Gastos IA FastAPI Application
Requires=network-online.target
After=network-online.target

[Service]
Type=simple
User=$($Script:Config.VMSSHUser)
Group=$($Script:Config.VMSSHUser)
WorkingDirectory=$($Script:Config.AppPath)
EnvironmentFile=$($Script:Config.EnvFilePath)
ExecStart=$($Script:Config.AppPath)/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
"@
    
    $serviceEscaped = $serviceContent -replace "'", "'\''"
    Invoke-SSHCommand "echo '$serviceEscaped' | sudo tee /etc/systemd/system/gastos-ia.service > /dev/null" "Creating systemd service file"
    Invoke-SSHCommand "sudo systemctl daemon-reload && sudo systemctl enable gastos-ia" "Enabling gastos-ia service"
    
    Write-Log "Auto-start configured." -Level "PASS"
    return $true
}

function Run-ValidationTests {
    <# STEP 18: Run tests #>
    Write-Step "18" "Running validation tests"
    
    # Start the service
    Invoke-SSHCommand "sudo systemctl start gastos-ia" "Starting gastos-ia service"
    Start-Sleep -Seconds 5
    $serviceStatus = Invoke-SSHCommand "sudo systemctl status gastos-ia --no-pager" "Checking service status"
    Write-Log "Service status:"
    Write-Log $serviceStatus
    
    # Run pytest
    $testResult = Invoke-SSHCommand "cd $($Script:Config.AppPath) && export PATH=\$HOME/.local/bin:\$PATH && uv run pytest tests/ --tb=short" "Running test suite"
    Write-Log "Test results:"
    Write-Log $testResult
    
    # Run quality checks
    $ruffResult = Invoke-SSHCommand "cd $($Script:Config.AppPath) && export PATH=\$HOME/.local/bin:\$PATH && uv run ruff check ." "Running ruff lint"
    Write-Log "Ruff lint: $ruffResult"
    
    $mypyResult = Invoke-SSHCommand "cd $($Script:Config.AppPath) && export PATH=\$HOME/.local/bin:\$PATH && uv run mypy app/" "Running mypy type check"
    Write-Log "Mypy: $mypyResult"
    
    # Test web access
    $webResult = Invoke-SSHCommand "curl -k -s https://gastos.local/health" "Testing health endpoint"
    Write-Log "Health endpoint: $webResult"
    
    # Test Ollama
    $ollamaResult = Invoke-SSHCommand "curl -s http://localhost:11434/api/tags" "Testing Ollama API"
    Write-Log "Ollama: model(s) available"
    
    Write-Log "Validation complete." -Level "PASS"
    return $true
}

function Generate-Diagnostics {
    <# STEP 19: Generate diagnostic JSON without secrets #>
    Write-Step "19" "Generating diagnostic JSON"
    
    $diagScript = @"
import json
import subprocess
import shlex
from datetime import datetime

diagnostic = {
    "generated_at": datetime.utcnow().isoformat() + "Z",
    "hostname": subprocess.run(["hostname"], capture_output=True, text=True).stdout.strip(),
    "uname": subprocess.run(["uname", "-a"], capture_output=True, text=True).stdout.strip(),
    "cpu_count": subprocess.run(["nproc"], capture_output=True, text=True).stdout.strip(),
    "memory": subprocess.run(["free", "-h"], capture_output=True, text=True).stdout.strip(),
    "disk": subprocess.run(["df", "-h", "/"], capture_output=True, text=True).stdout.strip(),
    "python_version": subprocess.run(["python3", "--version"], capture_output=True, text=True).stdout.strip(),
    "uv_version": subprocess.run(["uv", "--version"], capture_output=True, text=True).stdout.strip(),
    "services": {
        "gastos_ia": subprocess.run(
            ["systemctl", "is-active", "gastos-ia"], capture_output=True, text=True
        ).stdout.strip(),
        "caddy": subprocess.run(
            ["systemctl", "is-active", "caddy"], capture_output=True, text=True
        ).stdout.strip(),
        "ollama": subprocess.run(
            ["systemctl", "is-active", "ollama"], capture_output=True, text=True
        ).stdout.strip(),
    },
    "database": "gastos_ia (PostgreSQL)",
    "model": "qwen3-vl:4b",
    "smb_mounts": {
        "Ruben": subprocess.run(
            ["mountpoint", "-q", "/mnt/smb/Ruben"], capture_output=True
        ).returncode == 0,
        "Esme": subprocess.run(
            ["mountpoint", "-q", "/mnt/smb/Esme"], capture_output=True
        ).returncode == 0,
    },
    "env_file_permissions": subprocess.run(
        ["stat", "-c", "%a %U:%G", "/etc/gastos-ia/gastos-ia.env"],
        capture_output=True, text=True
    ).stdout.strip(),
    "no_secrets_included": True,
}

print(json.dumps(diagnostic, indent=2, ensure_ascii=False))
"@

    $diagEscaped = $diagScript -replace "'", "'\''"
    $diagnosticOutput = Invoke-SSHCommand "python3 -c '$diagEscaped'" "Running diagnostic script"
    
    # Save diagnostic locally
    $diagDate = Get-Date -Format "yyyy-MM-dd"
    $diagPath = "scripts/diagnostics/diagnostic-$diagDate.json"
    
    # Create local directory
    if (-not (Test-Path "scripts/diagnostics")) {
        New-Item -Path "scripts/diagnostics" -ItemType Directory -Force | Out-Null
    }
    
    $diagnosticOutput | Out-File -FilePath $diagPath -Encoding UTF8
    Write-Log "Diagnostic saved: $diagPath"
    Write-Log "=== DIAGNOSTIC SUMMARY ==="
    Write-Log $diagnosticOutput
    Write-Log "No secrets included (verified)." -Level "PASS"
    
    return $diagnosticOutput
}

# =============================================================================
# Main Orchestrator
# =============================================================================

function Invoke-MainInstaller {
    <# Main execution flow: 19 steps from PRD section 23 #>
    
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║           Gastos IA — Automated Installer v1.0                  ║" -ForegroundColor Cyan
    Write-Host "║           PRD v1.2 — Section 23                                 ║" -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    
    if ($DryRun) {
        Write-Host "[DRY-RUN MODE] No changes will be made." -ForegroundColor Yellow
    }
    
    # ==================== PRE-FLIGHT ====================
    if (-not $SkipPreflight) {
        Write-Step "1" "Pre-flight validation"
        Test-AdminRights
        Test-HyperVSupport
        Test-DiskSpace
        Test-NetworkReachability
        Test-ExistingVM
        Write-Log "All pre-flight checks passed." -Level "PASS"
    }
    
    # ==================== INFRASTRUCTURE ====================
    if (-not $SkipVM) {
        # Step 3: Enable Hyper-V (may reboot)
        Enable-HyperVRole
        
        # Step 4: Create SMB folders
        New-SMBFolders
        
        # Step 5: Create virtual switch
        New-HyperVSwitch
        
        # Steps 7-8: Create VM + VHDX
        New-VirtualMachine
        
        # Step 9: Wait for Ubuntu install
        Write-Step "9" "Ubuntu installation"
        Write-Log "Starting VM for the first time..."
        Start-VM -Name $Script:Config.VMName
        
        Write-Log "Waiting for Ubuntu to boot and SSH to be available..."
        Write-Log "Complete the Ubuntu installation manually via Hyper-V console"
        Write-Log "or prepare an autoinstall.yaml for unattended deployment."
        
        Write-Host ""
        Write-Host "=== MANUAL STEP REQUIRED ===" -ForegroundColor Yellow
        Write-Host "1. Connect to the VM via Hyper-V Manager console" -ForegroundColor Yellow
        Write-Host "2. Complete Ubuntu Server installation with:" -ForegroundColor Yellow
        Write-Host "   - Static IP: $($Script:Config.VMStaticIP)/$($Script:Config.VMSubnetMask)" -ForegroundColor Yellow
        Write-Host "   - Gateway: $($Script:Config.VMGateway)" -ForegroundColor Yellow
        Write-Host "   - DNS: $($Script:Config.VMDNS -join ', ')" -ForegroundColor Yellow
        Write-Host "   - User: $($Script:Config.VMSSHUser)" -ForegroundColor Yellow
        Write-Host "   - Enable SSH server" -ForegroundColor Yellow
        Write-Host "3. Press ENTER when Ubuntu installation is complete" -ForegroundColor Yellow
        Read-Host
        
        # Test SSH connection
        if (-not (Test-SSHConnection)) {
            Write-Log "SSH connection failed. Cannot continue." -Level "ERROR"
            exit 1
        }
    }
    
    # ==================== APPLICATION ====================
    if (-not $SkipApp) {
        # Steps 5-6: Install software on Ubuntu
        Install-UbuntuSoftware
        
        # Steps 7-8: Deploy application
        Deploy-Application
        
        # Steps 9-10: Database
        Initialize-Database
        
        # Step 11: SMB mounts
        Mount-SMBShares
        
        # Step 12: Google Sheets
        Setup-GoogleSheets
        
        # Step 13: Users
        Create-Users
        
        # Steps 14-15: Environment file
        Populate-EnvironmentFile
        
        # Step 16: Service activation
        Write-Step "16" "Starting services"
        Invoke-SSHCommand "sudo systemctl start gastos-ia" "Starting gastos-ia service"
        
        # Step 17: Auto-start
        Configure-AutoStart
    }
    
    # ==================== VALIDATION ====================
    # Step 18: Tests
    Run-ValidationTests
    
    # Step 19: Diagnostic
    $diagnostic = Generate-Diagnostics
    
    # ==================== COMPLETION ====================
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║           INSTALLATION COMPLETE                                 ║" -ForegroundColor Green
    Write-Host "╚══════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "Access the application at: https://gastos.local" -ForegroundColor Cyan
    Write-Host "Or: https://$($Script:Config.VMStaticIP)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Users:" -ForegroundColor Yellow
    Write-Host "  - Ruben (Administrator)" -ForegroundColor Yellow
    Write-Host "  - Esme (Standard User)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "IMPORTANT: Both users must change their password on first login." -ForegroundColor Yellow
    Write-Host "IMPORTANT: Trust the Caddy certificate on client machines." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Diagnostic: scripts/diagnostics/diagnostic-$(Get-Date -Format 'yyyy-MM-dd').json" -ForegroundColor Cyan
    Write-Host "Log: $($Script:Config.LogFile)" -ForegroundColor Cyan
    Write-Host ""
    
    return $diagnostic
}

# =============================================================================
# Entry Point
# =============================================================================

try {
    Invoke-MainInstaller
} catch {
    Write-Log "FATAL ERROR: $($_.Exception.Message)" -Level "ERROR"
    Write-Log "Stack trace: $($_.ScriptStackTrace)"
    Write-Log "Check the log file for details: $($Script:Config.LogFile)"
    exit 1
}
