# scripts/setup_windows.ps1
# One-command Windows setup script for Lecture Dubber
# Prepares Python virtual environment, dependencies, database, directories, and frontend.

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Lecture Dubber - Windows Setup & Environment Init" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
Set-Location $WorkspaceRoot

# 1. Prerequisite Checks
Write-Host "`n[STEP 1/6] Checking System Prerequisites..." -ForegroundColor Yellow

# Python check
$PythonCmd = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonCmd = "py -3.11"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCmd = "python"
} else {
    Write-Host "[ERROR] Python 3.10+ not found in PATH." -ForegroundColor Red
    Write-Host "Please install Python 3.11 via winget: winget install Python.Python.3.11" -ForegroundColor Yellow
    exit 1
}
Write-Host "Found Python interpreter: $PythonCmd" -ForegroundColor Green

# Node.js check
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Node.js not found in PATH." -ForegroundColor Red
    Write-Host "Please install Node.js 18+ from https://nodejs.org/ or via winget: winget install OpenJS.NodeJS" -ForegroundColor Yellow
    exit 1
}
$NodeVersion = (& node -v)
Write-Host "Found Node.js: $NodeVersion" -ForegroundColor Green

# FFmpeg check
$FFmpegCmd = "ffmpeg"
$WingetFFmpeg = "C:\Users\David\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-essentials_build\bin\ffmpeg.exe"

if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
    Write-Host "Found FFmpeg in PATH" -ForegroundColor Green
} elseif (Test-Path $WingetFFmpeg) {
    Write-Host "Found FFmpeg at Gyan winget location: $WingetFFmpeg" -ForegroundColor Green
} else {
    Write-Host "[WARNING] FFmpeg not found in standard paths. Installing via winget..." -ForegroundColor Yellow
    winget install Gyan.FFmpeg.Essentials --silent --accept-package-agreements --accept-source-agreements
}

# 2. Virtual Environment Creation
Write-Host "`n[STEP 2/6] Configuring Python Virtual Environment (.venv)..." -ForegroundColor Yellow
$VenvDir = Join-Path $WorkspaceRoot ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$VenvPip = Join-Path $VenvDir "Scripts\pip.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating new virtual environment at $VenvDir..." -ForegroundColor Gray
    if ($PythonCmd -eq "py -3.11") {
        & py -3.11 -m venv .venv
    } else {
        & python -m venv .venv
    }
}
Write-Host "Virtual environment ready at $VenvDir" -ForegroundColor Green

# 3. Installing Backend Dependencies
Write-Host "`n[STEP 3/6] Installing Backend Python Dependencies..." -ForegroundColor Yellow
& $VenvPython -m pip install --upgrade pip setuptools wheel --quiet
& $VenvPip install -r backend/requirements.txt --quiet
Write-Host "Backend dependencies installed successfully." -ForegroundColor Green

# 4. Storage & Environment Configuration
Write-Host "`n[STEP 4/6] Initializing Storage Directories & Configuration..." -ForegroundColor Yellow
$StorageDirs = @(
    (Join-Path $WorkspaceRoot "storage"),
    (Join-Path $WorkspaceRoot "storage\uploads"),
    (Join-Path $WorkspaceRoot "storage\jobs"),
    (Join-Path $WorkspaceRoot "logs")
)
foreach ($dir in $StorageDirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

$EnvFile = Join-Path $WorkspaceRoot ".env"
$EnvExample = Join-Path $WorkspaceRoot ".env.example"
if (-not (Test-Path $EnvFile) -and (Test-Path $EnvExample)) {
    Write-Host "Generating initial .env configuration..." -ForegroundColor Gray
    $RandomKey = -join ((1..32) | ForEach-Object { '{0:x2}' -f (Get-Random -Max 256) })
    $EnvContent = Get-Content $EnvExample -Raw
    $EnvContent = $EnvContent -replace "change-me", $RandomKey
    Set-Content -Path $EnvFile -Value $EnvContent
    Write-Host "Created .env with generated secret key." -ForegroundColor Green
} else {
    Write-Host ".env configuration present." -ForegroundColor Green
}

# 5. Database Schema & Migration
Write-Host "`n[STEP 5/6] Initializing SQLite Database & Applying Migrations..." -ForegroundColor Yellow
$AlembicExe = Join-Path $VenvDir "Scripts\alembic.exe"
try {
    & $AlembicExe upgrade head
    & $VenvPython -m backend.app.db.init_db
    Write-Host "Database schema initialized successfully." -ForegroundColor Green
} catch {
    Write-Host "[WARNING] Alembic upgrade encountered an issue: $_. Running init_db fallback..." -ForegroundColor Yellow
    & $VenvPython -m backend.app.db.init_db
}

# 6. Frontend Setup
Write-Host "`n[STEP 6/6] Installing Frontend npm Dependencies..." -ForegroundColor Yellow
$FrontendDir = Join-Path $WorkspaceRoot "frontend"
if (Test-Path $FrontendDir) {
    Push-Location $FrontendDir
    try {
        & npm install --quiet
        Write-Host "Frontend packages installed." -ForegroundColor Green
    } finally {
        Pop-Location
    }
}

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host " SETUP COMPLETE! Lecture Dubber is ready for launch." -ForegroundColor Green
Write-Host " Run '.\scripts\run_all.ps1' to start the API, worker, and UI." -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Green
