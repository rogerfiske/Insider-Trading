# init_project_windows.ps1 -- prepare local folders and guide the user.
#
# Creates runtime directories, copies .env.example if .env is missing,
# and prints setup instructions. Does NOT create .env with real secrets,
# install dependencies, or register scheduled tasks.
#
# Usage:
#   .\scripts\init_project_windows.ps1
#
# PowerShell 5.1 compatible.

$ErrorActionPreference = "Stop"

# -- Detect repo root (this script lives in scripts/) -------------------------
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host ""
Write-Host "Insider Routines -- Project Initialization"
Write-Host "==========================================="
Write-Host "Repo root: $Root"
Write-Host ""

# -- 1. Create runtime directories --------------------------------------------
Write-Host "1. Creating runtime directories..."

$dirs = @(
    (Join-Path $Root ".state"),
    (Join-Path $Root ".state\logs"),
    (Join-Path $Root "config")
)

foreach ($d in $dirs) {
    if (-not (Test-Path $d)) {
        New-Item -ItemType Directory -Path $d -Force | Out-Null
        Write-Host "   Created: $d"
    } else {
        Write-Host "   Exists:  $d"
    }
}

# -- 2. Check for .env --------------------------------------------------------
Write-Host ""
Write-Host "2. Checking .env..."

$envFile = Join-Path $Root ".env"
$envExample = Join-Path $Root ".env.example"

if (Test-Path $envFile) {
    Write-Host "   .env already exists. Skipping copy."
} else {
    if (Test-Path $envExample) {
        Copy-Item $envExample $envFile
        Write-Host "   Copied .env.example -> .env (placeholder values only)"
        Write-Host ""
        Write-Host "   >>> IMPORTANT: Open .env and fill in your real credentials. <<<"
        Write-Host "   >>> Do NOT commit .env to Git. It is gitignored.            <<<"
    } else {
        Write-Host "   WARNING: .env.example not found. Cannot create .env template."
    }
}

# -- 3. Check Python -----------------------------------------------------------
Write-Host ""
Write-Host "3. Checking Python..."

$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    $pyVer = & $VenvPython --version 2>&1
    Write-Host "   Venv Python found: $VenvPython ($pyVer)"
} else {
    $PyCmd = Get-Command py -ErrorAction SilentlyContinue
    if ($PyCmd) {
        $pyVer = & py --version 2>&1
        Write-Host "   System Python found: $($PyCmd.Source) ($pyVer)"
    } else {
        $PythonCmd = Get-Command python -ErrorAction SilentlyContinue
        if ($PythonCmd) {
            $pyVer = & python --version 2>&1
            Write-Host "   System Python found: $($PythonCmd.Source) ($pyVer)"
        } else {
            Write-Host "   WARNING: Python not found. Install Python 3.11+ first."
        }
    }
}

# -- 4. Next steps -------------------------------------------------------------
Write-Host ""
Write-Host "==========================================="
Write-Host "Next Steps"
Write-Host "==========================================="
Write-Host ""
Write-Host "  1. Create a virtual environment:"
Write-Host "       py -m venv .venv"
Write-Host "       .\.venv\Scripts\Activate.ps1"
Write-Host ""
Write-Host "  2. Install dependencies:"
Write-Host "       pip install -r requirements.txt"
Write-Host ""
Write-Host "  3. Edit .env with your real credentials:"
Write-Host "       - ANTHROPIC_API_KEY   (required)"
Write-Host "       - GMAIL_USER          (required for alerts)"
Write-Host "       - GMAIL_APP_PASSWORD  (required for alerts)"
Write-Host "       - GMAIL_TO            (optional, defaults to GMAIL_USER)"
Write-Host "       - TELEGRAM_BOT_TOKEN  (optional)"
Write-Host "       - TELEGRAM_CHAT_ID    (optional)"
Write-Host ""
Write-Host "  4. Run smoke test:"
Write-Host "       .\scripts\smoke_test_windows.ps1"
Write-Host ""
Write-Host "  5. Test a single agent (dry-run):"
Write-Host "       .\scripts\run_agent.ps1 eddie"
Write-Host ""
Write-Host "  NOTE: Ross defaults to dry-run mode (ROSS_DRY_RUN=true)."
Write-Host "        Set ROSS_DRY_RUN=false in .env to enable real delivery."
Write-Host ""
