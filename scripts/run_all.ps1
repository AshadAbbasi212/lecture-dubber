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

$ApiOutLog = Join-Path $LogsDir "api.out.log"
$ApiErrLog = Join-Path $LogsDir "api.err.log"
$WorkerOutLog = Join-Path $LogsDir "worker.out.log"
$WorkerErrLog = Join-Path $LogsDir "worker.err.log"

# Clean up stale processes on ports 8000 and 3000
foreach ($p in @(8000, 3000)) {
    try {
        $conns = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue
        foreach ($c in $conns) {
            $pidToKill = $c.OwningProcess
            if ($pidToKill -gt 0 -and $pidToKill -ne $PID) {
                Write-Host "Releasing port $p (stopping orphaned process PID $pidToKill)..." -ForegroundColor Yellow
                Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
                cmd.exe /c "taskkill /F /PID $pidToKill /T 2>nul" | Out-Null
            }
        }
    } catch {}
}
Start-Sleep -Milliseconds 1000

# Launch 1: FastAPI Backend Server
Write-Host "[1/3] Launching FastAPI Backend on port 8000..." -ForegroundColor Green
$ApiProcess = Start-Process -FilePath $PythonExe `
    -ArgumentList "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000" `
    -WorkingDirectory $WorkspaceRoot `
    -RedirectStandardOutput $ApiOutLog `
    -RedirectStandardError $ApiErrLog `
    -PassThru

Start-Sleep -Milliseconds 800

# Launch 2: Queue Worker
Write-Host "[2/3] Launching Background Queue Worker..." -ForegroundColor Green
$WorkerProcess = Start-Process -FilePath $PythonExe `
    -ArgumentList "-m", "backend.app.worker.worker" `
    -WorkingDirectory $WorkspaceRoot `
    -RedirectStandardOutput $WorkerOutLog `
    -RedirectStandardError $WorkerErrLog `
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
    # Wait until user interrupts or any service actually stops listening
    Start-Sleep -Seconds 3
    while ($true) {
        $apiPort = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
        if (-not $apiPort -and $ApiProcess.HasExited) {
            Start-Sleep -Seconds 3
            $apiPort = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
            if (-not $apiPort -and $ApiProcess.HasExited) {
                Write-Host "`n[ALERT] API server (port 8000) is no longer listening." -ForegroundColor Red
                break
            }
        }
        if ($WorkerProcess.HasExited) {
            Start-Sleep -Seconds 3
            if ($WorkerProcess.HasExited) {
                Write-Host "`n[ALERT] Worker process exited unexpectedly (ExitCode: $($WorkerProcess.ExitCode))" -ForegroundColor Red
                break
            }
        }
        $fePort = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue
        if (-not $fePort -and $FrontendProcess.HasExited) {
            Start-Sleep -Seconds 3
            $fePort = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue
            if (-not $fePort -and $FrontendProcess.HasExited) {
                Write-Host "`n[ALERT] Frontend dev server (port 3000) is no longer listening." -ForegroundColor Red
                break
            }
        }
        Start-Sleep -Seconds 5
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
