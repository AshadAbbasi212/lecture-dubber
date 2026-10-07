# scripts/run_tests.ps1
# CI-style test runner for Lecture Dubber
# Runs backend unit, API, and E2E integration test suites followed by frontend typecheck/build.

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Lecture Dubber - CI Test Suite Runner" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
Set-Location $WorkspaceRoot

# 1. Check Python virtual environment
$PythonExe = Join-Path $WorkspaceRoot ".venv\Scripts\python.exe"
$PytestExe = Join-Path $WorkspaceRoot ".venv\Scripts\pytest.exe"

if (-not (Test-Path $PytestExe)) {
    Write-Host "[ERROR] Virtual environment pytest not found at $PytestExe" -ForegroundColor Red
    Write-Host "Please run scripts/setup_windows.ps1 first." -ForegroundColor Yellow
    exit 1
}

# 2. Run Backend Tests
Write-Host "`n[STEP 1/2] Running Backend Test Suite (Unit, API, E2E)..." -ForegroundColor Yellow
$BackendStartTime = Get-Date

try {
    & $PytestExe backend/tests -v
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n[FAIL] Backend tests failed with exit code $LASTEXITCODE." -ForegroundColor Red
        exit $LASTEXITCODE
    }
}
catch {
    Write-Host "`n[FAIL] An error occurred executing pytest: $_" -ForegroundColor Red
    exit 1
}

$BackendDuration = ((Get-Date) - $BackendStartTime).TotalSeconds
Write-Host "[PASS] Backend test suite passed cleanly ($([math]::Round($BackendDuration, 1))s)." -ForegroundColor Green

# 3. Run Frontend Typecheck & Build
Write-Host "`n[STEP 2/2] Running Frontend Typecheck & Build (Next.js)..." -ForegroundColor Yellow
$FrontendStartTime = Get-Date
$FrontendDir = Join-Path $WorkspaceRoot "frontend"

if (Test-Path $FrontendDir) {
    Push-Location $FrontendDir
    try {
        & npm run build
        if ($LASTEXITCODE -ne 0) {
            Write-Host "`n[FAIL] Frontend build failed with exit code $LASTEXITCODE." -ForegroundColor Red
            exit $LASTEXITCODE
        }
    }
    catch {
        Write-Host "`n[FAIL] An error occurred during frontend build: $_" -ForegroundColor Red
        exit 1
    }
    finally {
        Pop-Location
    }
    $FrontendDuration = ((Get-Date) - $FrontendStartTime).TotalSeconds
    Write-Host "[PASS] Frontend Next.js build passed cleanly ($([math]::Round($FrontendDuration, 1))s)." -ForegroundColor Green
} else {
    Write-Host "[SKIP] Frontend directory not found at $FrontendDir." -ForegroundColor Gray
}

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host " ALL CI TESTS PASSED: Backend & Frontend Healthy" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
exit 0
