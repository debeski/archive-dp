
# install_deps.ps1

Write-Host "Checking requirements for Archive App..." -ForegroundColor Cyan

function Check-Command ($cmd) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        return $true
    }
    return $false
}

function Run-As-Admin {
    param([string]$ScriptPath)
    if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
        Write-Warning "This script requires Administrator privileges to install software."
        Start-Process powershell.exe "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`"" -Verb RunAs
        exit
    }
}

Run-As-Admin -ScriptPath $MyInvocation.MyCommand.Path

# 1. Curl (Usually built-in on modern Windows, but check anyway)
if (-not (Check-Command "curl")) {
    Write-Host "Installing curl..." -ForegroundColor Yellow
    winget install curl.curl --accept-source-agreements --accept-package-agreements
} else {
    Write-Host "✔ curl is installed." -ForegroundColor Green
}

# 2. Docker
if (-not (Check-Command "docker")) {
    Write-Host "Installing Docker Desktop..." -ForegroundColor Yellow
    winget install Docker.DockerDesktop --accept-source-agreements --accept-package-agreements
    Write-Warning "Docker Desktop has been installed. You may need to restart your computer."
} else {
    Write-Host "✔ Docker is installed." -ForegroundColor Green
}

# 3. Sops
if (-not (Check-Command "sops")) {
    Write-Host "Installing sops..." -ForegroundColor Yellow
    # Install via scoop or direct download. Since scoop might not be there, stick to choco or manual, 
    # but winget is standard now.
    winget install output.sops --accept-source-agreements --accept-package-agreements
    if (-not $?) {
        # Fallback to direct download if winget fails finding it
        Write-Host "Winget failed for sops. Attempting direct download..."
        $url = "https://github.com/getsops/sops/releases/latest/download/sops-v3.9.0.exe" # Hardcoded latest stable for now or dynamic
        $output = "$env:SystemRoot\System32\sops.exe"
        Invoke-WebRequest -Uri $url -OutFile $output
    }
} else {
    Write-Host "✔ sops is installed." -ForegroundColor Green
}

Write-Host "Dependency check complete." -ForegroundColor Cyan
Start-Sleep -Seconds 3
