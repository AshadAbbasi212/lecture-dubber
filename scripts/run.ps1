# scripts/run.ps1
# Shortcut wrapper forwarding directly to scripts/run_all.ps1
$RunAll = Join-Path $PSScriptRoot "run_all.ps1"
& $RunAll @args
