# smoke_test_windows.ps1 -- safe pre-flight checks for Insider project.
#
# Verifies project structure, Python availability, file existence,
# and basic compile safety. Does NOT require dependencies installed,
# API keys, or live network access.
#
# Usage:
#   .\scripts\smoke_test_windows.ps1
#
# PowerShell 5.1 compatible.

$ErrorActionPreference = "Stop"

$pass = 0
$fail = 0
$warn = 0

function Test-Check {
    param(
        [string]$Label,
        [bool]$Condition
    )
    if ($Condition) {
        Write-Host "  [PASS] $Label" -ForegroundColor Green
        $script:pass++
    } else {
        Write-Host "  [FAIL] $Label" -ForegroundColor Red
        $script:fail++
    }
}

function Test-Warn {
    param(
        [string]$Label,
        [string]$Message
    )
    Write-Host "  [WARN] $Label -- $Message" -ForegroundColor Yellow
    $script:warn++
}

# -- Detect repo root (this script lives in scripts/) -------------------------
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host ""
Write-Host "Insider Routines -- Smoke Test"
Write-Host "=============================="
Write-Host "Repo root: $Root"
Write-Host ""

# -- 1. Python version --------------------------------------------------------
Write-Host "1. Python"

$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$PythonExe = $null
if (Test-Path $VenvPython) {
    $PythonExe = $VenvPython
} else {
    $PyCmd = Get-Command py -ErrorAction SilentlyContinue
    if ($PyCmd) {
        $PythonExe = $PyCmd.Source
    } else {
        $PythonCmd = Get-Command python -ErrorAction SilentlyContinue
        if ($PythonCmd) {
            $PythonExe = $PythonCmd.Source
        }
    }
}

if ($PythonExe) {
    $pyVer = & $PythonExe --version 2>&1
    Test-Check "Python found: $PythonExe ($pyVer)" $true
} else {
    Test-Check "Python found" $false
}

# -- 2. Required files --------------------------------------------------------
Write-Host ""
Write-Host "2. Required files"

$requiredFiles = @(
    "requirements.txt",
    ".gitignore",
    ".env.example",
    "README.md",
    "agents\common.py",
    "agents\eddie.py",
    "agents\maggie.py",
    "agents\frank.py",
    "agents\maya.py",
    "agents\janet.py",
    "agents\sophie.py",
    "agents\ross.py",
    "install\schedule_windows.ps1",
    "install\uninstall_windows.ps1",
    "scripts\run_agent.ps1",
    "docs\source\original_prompt.md",
    "docs\source\video_transcript.txt"
)

foreach ($f in $requiredFiles) {
    $full = Join-Path $Root $f
    Test-Check $f (Test-Path $full)
}

# -- 3. .env.example exists ---------------------------------------------------
Write-Host ""
Write-Host "3. .env.example"
$envExample = Join-Path $Root ".env.example"
Test-Check ".env.example exists" (Test-Path $envExample)

# -- 4. .gitignore protects .env ----------------------------------------------
Write-Host ""
Write-Host "4. .gitignore protections"

$gitignorePath = Join-Path $Root ".gitignore"
if (Test-Path $gitignorePath) {
    $gitignoreContent = Get-Content $gitignorePath -Raw
    Test-Check ".gitignore contains .env" ($gitignoreContent -match "(?m)^\.env$")
    Test-Check ".gitignore contains .state/*" ($gitignoreContent -match "\.state")
    Test-Check ".gitignore contains .claude/" ($gitignoreContent -match "\.claude")
} else {
    Test-Check ".gitignore exists" $false
}

# -- 5. Compile check (py_compile) --------------------------------------------
Write-Host ""
Write-Host "5. Compile check (py_compile)"

if ($PythonExe) {
    $agents = @("common", "eddie", "maggie", "frank", "maya", "janet", "sophie", "ross")
    foreach ($a in $agents) {
        $agentFile = Join-Path $Root "agents\$a.py"
        if (Test-Path $agentFile) {
            try {
                $result = & $PythonExe -m py_compile $agentFile 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Test-Check "py_compile agents/$a.py" $true
                } else {
                    Test-Check "py_compile agents/$a.py" $false
                    Write-Host "           $result" -ForegroundColor Red
                }
            } catch {
                Test-Check "py_compile agents/$a.py" $false
                Write-Host "           $_" -ForegroundColor Red
            }
        } else {
            Test-Check "py_compile agents/$a.py (file missing)" $false
        }
    }
} else {
    Test-Warn "Compile check" "Python not found, skipping py_compile checks"
}

# -- 6. State directory -------------------------------------------------------
Write-Host ""
Write-Host "6. State directory"
$stateKeep = Join-Path $Root ".state\.gitkeep"
Test-Check ".state/.gitkeep exists" (Test-Path $stateKeep)

# -- Summary -------------------------------------------------------------------
Write-Host ""
Write-Host "=============================="
Write-Host "Results: $pass passed, $fail failed, $warn warnings"
if ($fail -eq 0) {
    Write-Host "Status: ALL CHECKS PASSED" -ForegroundColor Green
} else {
    Write-Host "Status: SOME CHECKS FAILED" -ForegroundColor Red
}
Write-Host ""
