# uninstall_windows.ps1 -- remove all Insider scheduled tasks.
#
# PowerShell 5.1 compatible.

$ErrorActionPreference = "SilentlyContinue"
$Folder = "\InsiderRoutines\"
foreach ($n in @("eddie", "maggie", "frank", "maya", "janet", "sophie", "ross")) {
    $name = "Insider-$n"
    $existing = Get-ScheduledTask -TaskName $name -TaskPath $Folder -ErrorAction SilentlyContinue
    if ($existing) {
        Unregister-ScheduledTask -TaskName $name -TaskPath $Folder -Confirm:$false
        Write-Host "  - removed $Folder$name"
    }
}

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Write-Host "All Insider tasks unregistered. Your scripts + state remain at $Root"
