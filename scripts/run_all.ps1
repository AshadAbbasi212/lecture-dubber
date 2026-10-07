# scripts/run_all.ps1
# Starts all three Lecture Dubber components:
# 1. FastAPI API server (http://localhost:8000)
# 2. Pipeline Queue Worker (Processes stages with GPU lock)
# 3. Next.js Frontend Web Application (http://localhost:3000)

$ErrorActionPreference = "Stop"

$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
Set-Location $WorkspaceRoot

$PythonExe = Join-Path $WorkspaceRoot ".venv\Scripts\python.exe"
$UvicornExe = Join-Path $WorkspaceRoot ".venv\Scripts\uvicorn.exe"

if (-not (Test-Path $PythonExe)) {
    Write-Host "[ERROR] Virtual environment not found. Please run '.\scripts\setup_windows.ps1' first." -ForegroundColor Red
    exit 1
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Starting Lecture Dubber Platform Services..." -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  API Server:  http://localhost:8000  (Docs: http://localhost:8000/docs)" -ForegroundColor Gray
Write-Host "  Frontend:    http://localhost:3000" -ForegroundColor Gray
Write-Host "  Queue Worker: Polling storage/app.db with GPU lock" -ForegroundColor Gray
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop all services." -ForegroundColor Yellow
Write-Host ""

# Ensure logs directory exists
$LogsDir = Join-Path $WorkspaceRoot "logs"
if (-not (Test-Path $LogsDir)) {
    New-Item -ItemType Directory -Path $LogsDir -Force | Out-Null
}

$ApiLog = Join-Path $LogsDir "api.log"
$WorkerLog = Join-Path $LogsDir "worker.log"

# Launch 1: FastAPI Backend Server
Write-Host "[1/3] Launching FastAPI Backend on port 8000..." -ForegroundColor Green
$ApiProcess = Start-Process -FilePath $UvicornExe `
    -ArgumentList "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload" `
    -WorkingDirectory $WorkspaceRoot `
    -PassThru

# Launch 2: Queue Worker
Write-Host "[2/3] Launching Background Queue Worker..." -ForegroundColor Green
$WorkerProcess = Start-Process -FilePath $PythonExe `
    -ArgumentList "-m", "backend.app.worker.worker" `
    -WorkingDirectory $WorkspaceRoot `
    -PassThru

# Launch 3: Frontend Web Dev Server
Write-Host "[3/3] Launching Next.js Frontend on port 3000..." -ForegroundColor Green
$FrontendDir = Join-Path $WorkspaceRoot "frontend"
$FrontendProcess = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c", "npm run dev" `
    -WorkingDirectory $FrontendDir `
    -PassThru

Write-Host "`nAll 3 services are running!" -ForegroundColor Cyan
Write-Host "PIDs -> API: $($ApiProcess.Id), Worker: $($WorkerProcess.Id), Frontend: $($FrontendProcess.Id)" -ForegroundColor Gray
Write-Host "Open http://localhost:3000 in your browser to start dubbing lectures." -ForegroundColor Green
Write-Host "Monitoring processes... Press Enter or Ctrl+C to terminate all services." -ForegroundColor Yellow

try {
    # Wait until user interrupts or any process terminates
    while ($true) {
        if ($ApiProcess.HasExited) {
            Write-Host "`n[ALERT] API process exited unexpectedly (ExitCode: $($ApiProcess.ExitCode))" -ForegroundColor Red
            break
        }
        if ($WorkerProcess.HasExited) {
            Write-Host "`n[ALERT] Worker process exited unexpectedly (ExitCode: $($WorkerProcess.ExitCode))" -ForegroundColor Red
            break
        }
        if ($FrontendProcess.HasExited) {
            Write-Host "`n[ALERT] Frontend process exited unexpectedly (ExitCode: $($FrontendProcess.ExitCode))" -ForegroundColor Red
            break
        }
        Start-Sleep -Seconds 2
    }
} finally {
    Write-Host "`nShutting down all Lecture Dubber services..." -ForegroundColor Yellow
    
    if (-not $ApiProcess.HasExited) {
        Write-Host "Stopping API server (PID $($ApiProcess.Id))..." -ForegroundColor Gray
        Stop-Process -Id $ApiProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if (-not $WorkerProcess.HasExited) {
        Write-Host "Stopping Worker (PID $($WorkerProcess.Id))..." -ForegroundColor Gray
        Stop-Process -Id $WorkerProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if (-not $FrontendProcess.HasExited) {
        Write-Host "Stopping Frontend dev server (PID $($FrontendProcess.Id))..." -ForegroundColor Gray
        Stop-Process -Id $FrontendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "All processes cleanly stopped." -ForegroundColor Green
}
