# start-frontend.ps1
# Starts the Vite dev server via WSL and exposes port 3000 to your local network.
# Place this script inside the frontend project folder, then run as Administrator:
#   powershell -ExecutionPolicy Bypass -File ".\start-frontend.ps1"

$PORT = 3000
$RULE_NAME = "OSRS Flip Frontend"
$BACKEND_PORT = 8000

# Resolve project dir from script location
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Definition
$WIN_PATH = (Resolve-Path $SCRIPT_DIR).Path

# Convert Windows path to WSL path (e.g. D:\foo\bar -> /mnt/d/foo/bar)
$driveLetter = $WIN_PATH.Substring(0, 1).ToLower()
$remainder = $WIN_PATH.Substring(2).Replace('\', '/')
$FRONTEND_WSL_PATH = "/mnt/$driveLetter$remainder"

$WSL_IP = (wsl hostname -I).Trim().Split(" ")[0]
$WIN_HOST_IP = (wsl bash -c "ip route show default" | Select-String -Pattern 'via ([\d.]+)').Matches[0].Groups[1].Value

Write-Host ""
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "  OSRS Flip - Frontend Dev Server" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "WSL IP:       $WSL_IP" -ForegroundColor Cyan
Write-Host "Win host IP:  $WIN_HOST_IP" -ForegroundColor Cyan
Write-Host "API target:   http://$($WIN_HOST_IP):$($BACKEND_PORT)" -ForegroundColor Cyan
Write-Host "Port:         $PORT" -ForegroundColor Cyan

# Get Windows IP(s) for display
$winIPs = Get-NetIPAddress -AddressFamily IPv4 | 
    Where-Object { $_.IPAddress -ne "127.0.0.1" -and $_.PrefixOrigin -ne "WellKnown" } |
    Select-Object -ExpandProperty IPAddress

Write-Host ""
Write-Host "Access from your phone:" -ForegroundColor Green
foreach ($ip in $winIPs) {
    Write-Host "  http://${ip}:${PORT}" -ForegroundColor Green
}
Write-Host ""

# --- Add firewall rule (idempotent) ---
$existingRule = netsh advfirewall firewall show rule name=$RULE_NAME 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Adding firewall rule for port $PORT..." -ForegroundColor Gray
    netsh advfirewall firewall add rule name=$RULE_NAME dir=in action=allow protocol=TCP localport=$PORT | Out-Null
    Write-Host "Firewall rule added." -ForegroundColor DarkGray
} else {
    Write-Host "Firewall rule already exists." -ForegroundColor DarkGray
}

# --- Port forward WSL -> Windows ---
Write-Host "Setting up port forwarding..." -ForegroundColor Gray
netsh interface portproxy delete v4tov4 listenport=$PORT listenaddress=0.0.0.0 2>$null | Out-Null
netsh interface portproxy add v4tov4 listenport=$PORT listenaddress=0.0.0.0 connectport=$PORT connectaddress=$WSL_IP
Write-Host "  Port proxy: 0.0.0.0:$PORT -> WSL $WSL_IP`:$PORT" -ForegroundColor DarkGray

Write-Host ""
Write-Host "Starting Vite dev server via WSL... (Ctrl+C to stop)" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

# --- Start the server, clean up on exit ---
try {
    $CMD = "cd '$FRONTEND_WSL_PATH' && VITE_API_TARGET=http://127.0.0.1:$($BACKEND_PORT) npm run dev"
    Write-Host "Running: $CMD" -ForegroundColor DarkGray
    wsl bash -ic $CMD
}
finally {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "  Shutting down..." -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow

    # Remove port proxy
    Write-Host "Removing port forwarding..." -ForegroundColor Gray
    netsh interface portproxy delete v4tov4 listenport=$PORT listenaddress=0.0.0.0 2>$null | Out-Null
    Write-Host "  Port proxy removed." -ForegroundColor DarkGray

    # Remove firewall rule
    Write-Host "Removing firewall rule..." -ForegroundColor Gray
    netsh advfirewall firewall delete rule name=$RULE_NAME 2>$null | Out-Null
    Write-Host "  Firewall rule removed." -ForegroundColor DarkGray

    Write-Host ""
    Write-Host "Cleanup complete. Goodbye!" -ForegroundColor Green
    Write-Host ""
}