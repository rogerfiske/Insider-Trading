# schedule_windows.ps1 -- register the 7 Insider agents with Windows Task Scheduler.
#
# Creates 7 scheduled tasks under the \InsiderRoutines\ folder.
# Idempotent: re-running removes existing tasks and recreates them.
#
# Logs land in <repo_root>\.state\logs\.
#
# PowerShell 5.1 compatible -- no null-conditional (?.) syntax.
# Do not run this script until CP04+ authorizes it.

$ErrorActionPreference = "Stop"

# -- Detect repo root (this script lives in install/) -------------------------
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Agents = Join-Path $Root "agents"
$Logs = Join-Path (Join-Path $Root ".state") "logs"
$Folder = "\InsiderRoutines"

# -- Detect Python (PS 5.1 safe) ----------------------------------------------
$PythonCmd = Get-Command py -ErrorAction SilentlyContinue
if (-not $PythonCmd) {
    $PythonCmd = Get-Command python -ErrorAction SilentlyContinue
}
if (-not $PythonCmd) {
    Write-Error "Python not found on PATH. Install Python 3.10+ first (https://www.python.org/downloads/)."
    exit 1
}
$Python = $PythonCmd.Source

# Prefer venv Python if it exists
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    $Python = $VenvPython
}

# -- Ensure log directory exists -----------------------------------------------
New-Item -ItemType Directory -Force -Path $Logs | Out-Null

function Register-InsiderTask {
    param(
        [string]$Name,
        [string]$Script,
        [Parameter(Mandatory=$false)]
        [Microsoft.Management.Infrastructure.CimInstance]$Trigger,
        [Parameter(Mandatory=$false)]
        [Microsoft.Management.Infrastructure.CimInstance[]]$Triggers
    )

    $taskPath = "$Folder\"
    $taskName = "Insider-$Name"

    # Remove if it exists.
    $existing = Get-ScheduledTask -TaskName $taskName -TaskPath $taskPath -ErrorAction SilentlyContinue
    if ($existing) {
        Unregister-ScheduledTask -TaskName $taskName -TaskPath $taskPath -Confirm:$false
    }

    $action = New-ScheduledTaskAction `
        -Execute $Python `
        -Argument "`"$(Join-Path $Agents $Script)`"" `
        -WorkingDirectory $Root

    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

    # Support both single trigger and multiple triggers
    if ($Triggers) {
        Register-ScheduledTask `
            -TaskName $taskName `
            -TaskPath $taskPath `
            -Action $action `
            -Trigger $Triggers `
            -Settings $settings `
            -Description "Insider Routines - $Name" | Out-Null
    } else {
        Register-ScheduledTask `
            -TaskName $taskName `
            -TaskPath $taskPath `
            -Action $action `
            -Trigger $Trigger `
            -Settings $settings `
            -Description "Insider Routines - $Name" | Out-Null
    }

    Write-Host "  OK   $taskPath$taskName"
}

Write-Host "Registering Insider agents with Task Scheduler..."

# Eddie -- daily 06:00
Register-InsiderTask -Name "eddie" -Script "eddie.py" `
    -Trigger (New-ScheduledTaskTrigger -Daily -At 06:00)

# Maggie -- weekly Sunday 19:00
Register-InsiderTask -Name "maggie" -Script "maggie.py" `
    -Trigger (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 19:00)

# Frank -- weekly Monday 08:00
Register-InsiderTask -Name "frank" -Script "frank.py" `
    -Trigger (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 08:00)

# Maya -- daily 12:00 (original design: every 6 hours; conservative for initial install)
Register-InsiderTask -Name "maya" -Script "maya.py" `
    -Trigger (New-ScheduledTaskTrigger -Daily -At 12:00)

# Janet -- daily 17:00
Register-InsiderTask -Name "janet" -Script "janet.py" `
    -Trigger (New-ScheduledTaskTrigger -Daily -At 17:00)

# Sophie -- daily 18:00 (original design: every 30 min; conservative for initial install)
Register-InsiderTask -Name "sophie" -Script "sophie.py" `
    -Trigger (New-ScheduledTaskTrigger -Daily -At 18:00)

# Ross -- morning startup schedule (CP20D)
# Trigger 1: Weekday 08:00 fallback (primary for non-admin install)
# Trigger 2: At user logon with 3-minute delay (requires admin - see note below)
# Removed: Previous 18:30 trigger (for initial morning rollout)
#
# NOTE: Logon triggers require administrator privileges to register.
# To add the logon trigger after this script runs, open PowerShell as Administrator and run:
#   $task = Get-ScheduledTask -TaskName "Insider-ross" -TaskPath "\InsiderRoutines\"
#   $logonTrigger = New-ScheduledTaskTrigger -AtLogon
#   $logonTrigger.Delay = "PT3M"
#   $task.Triggers += $logonTrigger
#   $task | Set-ScheduledTask
$rossFallbackTrigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At 08:00

Register-InsiderTask -Name "ross" -Script "ross.py" `
    -Trigger $rossFallbackTrigger

Write-Host ""
Write-Host "NOTE: Ross logon trigger requires admin privileges."
Write-Host "To add logon trigger, run PowerShell as Administrator and execute:"
Write-Host "  `$task = Get-ScheduledTask -TaskName 'Insider-ross' -TaskPath '\InsiderRoutines\'"
Write-Host "  `$logonTrigger = New-ScheduledTaskTrigger -AtLogon"
Write-Host "  `$logonTrigger.Delay = 'PT3M'"
Write-Host "  `$task.Triggers += `$logonTrigger"
Write-Host "  `$task | Set-ScheduledTask"

Write-Host ""
Write-Host "All 7 agents registered. Logs -> $Logs"
Write-Host "Inspect: Get-ScheduledTask -TaskPath '$Folder\'"
Write-Host "Uninstall: powershell -File `"$(Join-Path $Root 'install\uninstall_windows.ps1')`""
