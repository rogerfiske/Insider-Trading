# run_agent.ps1 -- run a named Insider agent manually.
#
# Usage:
#   .\scripts\run_agent.ps1 janet
#   .\scripts\run_agent.ps1 sophie
#   .\scripts\run_agent.ps1 eddie
#
# PowerShell 5.1 compatible.

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$AgentName
)

$ErrorActionPreference = "Stop"

# -- Validate agent name -------------------------------------------------------
$AllowedAgents = @("eddie", "maggie", "frank", "maya", "janet", "sophie", "ross")
$AgentLower = $AgentName.ToLower()

if ($AllowedAgents -notcontains $AgentLower) {
    Write-Error "Unknown agent: '$AgentName'. Allowed: $($AllowedAgents -join ', ')"
    exit 1
}

# -- Detect repo root (this script lives in scripts/) -------------------------
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$ScriptPath = Join-Path (Join-Path $Root "agents") "$AgentLower.py"

if (-not (Test-Path $ScriptPath)) {
    Write-Error "Agent script not found: $ScriptPath"
    exit 1
}

# -- Detect Python (PS 5.1 safe) ----------------------------------------------
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    $Python = $VenvPython
} else {
    $PythonCmd = Get-Command py -ErrorAction SilentlyContinue
    if (-not $PythonCmd) {
        $PythonCmd = Get-Command python -ErrorAction SilentlyContinue
    }
    if (-not $PythonCmd) {
        Write-Error "Python not found. Install Python 3.10+ or create .venv first."
        exit 1
    }
    $Python = $PythonCmd.Source
}

# -- Run the agent -------------------------------------------------------------
Write-Host "Running agent: $AgentLower"
Write-Host "Python: $Python"
Write-Host "Script: $ScriptPath"
Write-Host "---"

& $Python $ScriptPath
$exitCode = $LASTEXITCODE
if ($exitCode -ne 0) {
    Write-Warning "Agent '$AgentLower' exited with code $exitCode"
}
exit $exitCode
