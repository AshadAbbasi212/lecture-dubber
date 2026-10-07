# Checks that the tools needed for Lecture Dubber are installed.
# Run: powershell -ExecutionPolicy Bypass -File scripts\check_prereqs.ps1

function Check([string]$label, [scriptblock]$test) {
    try {
        $out = (& $test 2>&1 | Select-Object -First 1)
        Write-Host ("[OK]      {0,-12} {1}" -f $label, $out) -ForegroundColor Green
    } catch {
        Write-Host ("[MISSING] {0}" -f $label) -ForegroundColor Red
    }
}

Write-Host "Lecture Dubber prerequisite check`n"
Check "git"       { git --version }
Check "python"    { python --version }
Check "py 3.11"   { py -3.11 --version }
Check "py 3.10"   { py -3.10 --version }
Check "node"      { node --version }
Check "npm"       { npm --version }
Check "ffmpeg"    { ffmpeg -version }
Check "ffprobe"   { ffprobe -version }
Check "nvidia-smi" { nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader }

Write-Host "`nNotes:"
Write-Host " - At least one of py 3.10 / 3.11 should be OK (many AI repos need it)."
Write-Host " - GPU should show 8 GB or more. Install a CUDA-enabled PyTorch build (see docs/SETUP_WINDOWS.md)."
