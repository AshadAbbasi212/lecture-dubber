# Windows setup

Target: Windows 10/11, NVIDIA GPU with 8 GB VRAM.

## Prerequisites

1. **NVIDIA driver**: recent Game Ready or Studio driver. Check with `nvidia-smi`.
2. **Git**: `winget install Git.Git`
3. **Python 3.10 or 3.11** (many AI repos do not support newer versions yet): `winget install Python.Python.3.11`. Use the `py` launcher to create venvs, for example `py -3.11 -m venv .venv`.
4. **Node.js 20 LTS or newer**: `winget install OpenJS.NodeJS.LTS`
5. **FFmpeg**: `winget install Gyan.FFmpeg` (restart the terminal so it is on PATH). Confirm with `ffmpeg -version` and `ffprobe -version`.
6. **Microsoft C++ Build Tools**: needed to compile some Python wheels.
7. **Enable long paths** (Windows setting and `git config --global core.longpaths true`); some model repos have deep folders.
8. **PyTorch with CUDA**: install from the official PyTorch index that matches your driver (the agent will pick the right command in Phase 0 after checking pytorch.org). Do not install the CPU-only wheel.
9. Optional: **WSL2 (Ubuntu)** with GPU support, as a fallback for repos that do not run on native Windows.

## Check everything

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check_prereqs.ps1
```

## Disk and memory

Plan for at least 50 GB free for models plus working space for videos (a
60-minute lecture can produce several GB of intermediates). 16 GB of system RAM
is a practical minimum; 32 GB is more comfortable.

## Running (after the agent builds it)

The agent will add `scripts/run_dev.ps1` in Phase 7 to start the API, the worker
and the frontend together.
