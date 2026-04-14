# Backend Start Scripts - Usage Guide

## 📋 Overview

You now have **two options** for starting your FastAPI backend server:

1. **start-backend.ps1** - PowerShell script that runs everything in WSL
2. **start-backend.sh** - Native bash script for WSL

Both scripts work with your WSL-based Python venv!

---

## 🚀 Option 1: PowerShell Script (Recommended for your workflow)

**File:** `start-backend.ps1`

### Features
✅ Runs from Windows PowerShell  
✅ Executes everything in WSL (uses your WSL venv)  
✅ Automatically converts Windows paths to WSL paths  
✅ Manages Windows firewall rules  
✅ Shows network-accessible URLs  
✅ Auto-creates WSL venv if missing  

### Usage

```powershell
# Run as Administrator from project directory
powershell -ExecutionPolicy Bypass -File ".\start-backend.ps1"
```

Or simply double-click the script if execution policy is enabled.

### What It Does

1. **Checks WSL** - Verifies WSL is available
2. **Path Conversion** - Converts `D:\Documents\...` to `/mnt/d/Documents/...`
3. **WSL Venv Check** - Ensures venv exists in WSL
4. **Dependencies** - Installs if needed
5. **Firewall** - Adds Windows firewall rule for port 8000
6. **Server** - Starts uvicorn in WSL
7. **Cleanup** - Removes firewall rule on exit

### Output Example

```
========================================
  OSRS Flip - Backend API Server (WSL)
========================================

Port:         8000

API accessible at:
  http://192.168.1.100:8000
  http://192.168.1.100:8000/docs  (Swagger UI)

Checking WSL availability...
WSL is available.
Checking WSL venv...
WSL venv exists.
Firewall rule already exists.

Starting FastAPI server in WSL... (Ctrl+C to stop)
========================================

INFO:     Will watch for changes in these directories: ['/mnt/d/Documents/Programming/flipping-calculator-api']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

## 🐧 Option 2: Native Bash Script

**File:** `start-backend.sh`

### Features
✅ Runs natively in WSL  
✅ No Windows dependencies  
✅ Lighter weight  
✅ Better for WSL-only workflows  

### Usage

```bash
# Make executable (first time only)
chmod +x start-backend.sh

# Run from WSL
./start-backend.sh
```

### What It Does

1. **Venv Check** - Creates if missing
2. **Dependencies** - Installs if needed
3. **Server** - Starts uvicorn
4. **Cleanup** - Deactivates venv on exit

---

## 🔄 Path Conversion (PowerShell Script)

The PowerShell script automatically converts paths:

| Windows Path | WSL Path |
|-------------|----------|
| `D:\Documents\Programming\flipping-calculator-api` | `/mnt/d/Documents/Programming/flipping-calculator-api` |
| `C:\Users\jason\Projects\api` | `/mnt/c/Users/jason/Projects/api` |

This means you can keep your project on any Windows drive and the script will work!

---

## 🛠️ Troubleshooting

### PowerShell Script Issues

**Problem:** "WSL is not available"
```powershell
# Install WSL
wsl --install

# Or update WSL
wsl --update
```

**Problem:** "Failed to create venv in WSL"
```bash
# In WSL, install Python
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

**Problem:** Firewall rule not working
```powershell
# Run PowerShell as Administrator
Right-click PowerShell → Run as Administrator
```

### Bash Script Issues

**Problem:** "Permission denied"
```bash
# Make executable
chmod +x start-backend.sh
```

**Problem:** "python3 not found"
```bash
# Install Python
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

---

## 🎯 Which One Should You Use?

### Use **start-backend.ps1** if:
- ✅ You're used to running PowerShell scripts
- ✅ You want automatic firewall management
- ✅ You want to see network-accessible URLs
- ✅ You prefer double-clicking to start server

### Use **start-backend.sh** if:
- ✅ You work primarily in WSL terminal
- ✅ You don't need firewall automation
- ✅ You prefer bash scripts
- ✅ You want faster startup (no path conversion)

---

## 📝 Integration with Existing Workflow

### Your Current Setup
You've been using `start-backend.ps1` to start the server from PowerShell.

### What Changed
- ✅ Your venv is now in WSL
- ✅ New `start-backend.ps1` runs everything in WSL
- ✅ Same user experience, different backend

### Migration Steps
1. Replace old `start-backend.ps1` with the new WSL-compatible version
2. Delete old Windows venv: `Remove-Item -Recurse -Force venv`
3. Run new script - it will auto-create WSL venv on first run
4. Everything works as before! 🎉

---

## 🔥 Pro Tips

### Tip 1: Create Alias (PowerShell)
Add to your PowerShell profile:
```powershell
function Start-FlipBackend {
    Set-Location "D:\Documents\Programming\flipping-calculator-api"
    .\start-backend.ps1
}

# Usage: Just type 'Start-FlipBackend' from anywhere
```

### Tip 2: Create Alias (Bash)
Add to `~/.bashrc`:
```bash
alias flip-api='cd /mnt/d/Documents/Programming/flipping-calculator-api && ./start-backend.sh'

# Usage: Just type 'flip-api' from anywhere in WSL
```

### Tip 3: Background Mode (WSL)
Run server in background:
```bash
./start-backend.sh > server.log 2>&1 &
```

Stop with:
```bash
pkill -f uvicorn
```

---

## ✅ Summary

Both scripts now work with your WSL-based Python environment:

- **PowerShell script** - Bridges Windows → WSL seamlessly
- **Bash script** - Native WSL experience

Choose based on your workflow preference. The PowerShell script is recommended for your current setup since you're used to running `.ps1` files! 🚀
