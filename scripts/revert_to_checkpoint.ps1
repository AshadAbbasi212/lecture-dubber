# scripts/revert_to_checkpoint.ps1
# Lecture Dubber - Revert to Verified Natural-Voice Checkpoint
# Run this script anytime to discard unwanted experimental changes and restore to the verified working state.

param(
    [switch]$HardReset = $true
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir
Set-Location $RootDir

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   LECTURE DUBBER - CHECKPOINT REVERSION TOOL                        " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Target Checkpoint: 'checkpoint-verified-working' (Commit 6ac3845)"
Write-Host ""

if ($HardReset) {
    Write-Host "[1/3] Discarding uncommitted working tree changes and resetting to tag..." -ForegroundColor Yellow
    git reset --hard checkpoint-verified-working
    git clean -fd backend/ scripts/ docs/
} else {
    Write-Host "[1/3] Checking out checkpoint tag..." -ForegroundColor Yellow
    git checkout checkpoint-verified-working
}

Write-Host "[2/3] Restoring verified bilingual transcripts from storage checkpoint..." -ForegroundColor Yellow
$BackupDir = Join-Path $RootDir "storage\checkpoints\checkpoint_natural_voices"
if (Test-Path $BackupDir) {
    Copy-Item "$BackupDir\*" "$RootDir\" -Force
    Write-Host "  Transcripts restored from $BackupDir" -ForegroundColor Green
} else {
    Write-Host "  Backup directory $BackupDir not found, skipping." -ForegroundColor Gray
}

Write-Host "[3/3] Verifying neural models and media files..." -ForegroundColor Yellow
$RyanModel = Join-Path $RootDir "models\tts\piper\en_US-ryan-medium.onnx"
$LessacModel = Join-Path $RootDir "models\tts\piper\en_US-lessac-medium.onnx"

if ((Test-Path $RyanModel) -and (Test-Path $LessacModel)) {
    Write-Host "  Neural Piper models (Ryan + Lessac): Verified Present" -ForegroundColor Green
} else {
    Write-Host "  Warning: One or more Piper neural models are missing in models/tts/piper!" -ForegroundColor Red
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "REVERT COMPLETE: Successfully restored to verified working checkpoint!" -ForegroundColor Green
Write-Host "Current Git Status:" -ForegroundColor Green
git status -s
Write-Host "======================================================================" -ForegroundColor Green
