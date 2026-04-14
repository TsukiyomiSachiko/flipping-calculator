# start-backend.ps1
# Starts the FastAPI backend in WSL with venv and exposes port 8000 to your local network.
# This script runs from PowerShell but executes everything in WSL for compatibility.
# Place this script inside the backend project folder, then run as Administrator:
#   powershell -ExecutionPolicy Bypass -File ".\start-backend.ps1"

# Resolve project dir from script location
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Definition
$PROJECT_DIR = (Resolve-Path $SCRIPT_DIR).Path

$PORT = 8000
$RULE_NAME = "OSRS Flip Backend"

Write-Host ""
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "  OSRS Flip - Backend API Server (WSL)" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "Port:         $PORT" -ForegroundColor Cyan

# Convert Windows path to WSL path
# Example: D:\Documents\Programming\flipping-calculator-api -> /mnt/d/Documents/Programming/flipping-calculator-api
function Convert-ToWSLPath {
    param([string]$WindowsPath)
    
    # Replace backslashes with forward slashes
    $path = $WindowsPath -replace '\\', '/'
    
    # Convert drive letter (e.g., D: -> /mnt/d)
    if ($path -match '^([A-Za-z]):(.*)$') {
        $drive = $matches[1].ToLower()
        $rest = $matches[2]
        return "/mnt/$drive$rest"
    }
    
    return $path
}

$WSL_PROJECT_DIR = Convert-ToWSLPath $PROJECT_DIR

# Get Windows IP(s) for display
$winIPs = Get-NetIPAddress -AddressFamily IPv4 | 
    Where-Object { $_.IPAddress -ne "127.0.0.1" -and $_.PrefixOrigin -ne "WellKnown" } |
    Select-Object -ExpandProperty IPAddress

Write-Host ""
Write-Host "API accessible at:" -ForegroundColor Green
foreach ($ip in $winIPs) {
    Write-Host "  http://${ip}:${PORT}" -ForegroundColor Green
    Write-Host "  http://${ip}:${PORT}/docs  (Swagger UI)" -ForegroundColor Green
}
Write-Host ""

# --- Check if WSL is available ---
Write-Host "Checking WSL availability..." -ForegroundColor Gray
$wslCheck = wsl --status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: WSL is not available or not installed." -ForegroundColor Red
    Write-Host "Please install WSL: wsl --install" -ForegroundColor Yellow
    exit 1
}
Write-Host "WSL is available." -ForegroundColor DarkGray

# --- Check venv in WSL ---
Write-Host "Checking WSL venv..." -ForegroundColor Gray
$venvCheck = wsl bash -c "cd '$WSL_PROJECT_DIR' && test -d venv && echo 'exists'"

if ($venvCheck -ne "exists") {
    Write-Host "WSL venv not found. Creating it..." -ForegroundColor Yellow
    Write-Host "This may take a minute..." -ForegroundColor Gray
    
    # Create venv in WSL
    wsl bash -c "cd '$WSL_PROJECT_DIR' && python3 -m venv venv"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create venv in WSL." -ForegroundColor Red
        Write-Host "Please ensure Python 3 is installed in WSL: sudo apt install python3 python3-venv" -ForegroundColor Yellow
        exit 1
    }
    
    # Install dependencies
    Write-Host "Installing dependencies in WSL venv..." -ForegroundColor Gray
    wsl bash -c "cd '$WSL_PROJECT_DIR' && source venv/bin/activate && pip install -r requirements.txt"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install dependencies." -ForegroundColor Red
        exit 1
    }
    Write-Host "Dependencies installed." -ForegroundColor DarkGray
} else {
    Write-Host "WSL venv exists." -ForegroundColor DarkGray
}

# --- Add firewall rule (idempotent) ---
$existingRule = netsh advfirewall firewall show rule name=$RULE_NAME 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Adding firewall rule for port $PORT..." -ForegroundColor Gray
    netsh advfirewall firewall add rule name=$RULE_NAME dir=in action=allow protocol=TCP localport=$PORT | Out-Null
    Write-Host "Firewall rule added." -ForegroundColor DarkGray
} else {
    Write-Host "Firewall rule already exists." -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "Starting FastAPI server in WSL... (Ctrl+C to stop)" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

# --- Start the server in WSL, clean up on exit ---
try {
    # Run uvicorn in WSL with venv activated
    # Using --host 0.0.0.0 to expose on all network interfaces
    wsl bash -c "cd '$WSL_PROJECT_DIR' && source venv/bin/activate && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port $PORT"
}
finally {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "  Shutting down..." -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow

    # Remove firewall rule
    Write-Host "Removing firewall rule..." -ForegroundColor Gray
    netsh advfirewall firewall delete rule name=$RULE_NAME 2>$null | Out-Null
    Write-Host "Firewall rule removed." -ForegroundColor DarkGray

    Write-Host ""
    Write-Host "Cleanup complete. Goodbye!" -ForegroundColor Green
    Write-Host ""
}