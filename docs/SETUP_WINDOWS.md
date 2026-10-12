# Windows setup

Target: Windows 10/11, NVIDIA GPU with 4 GB+ VRAM (e.g., GTX 1650, RTX 3050 Laptop, Quadro M1200 or higher).

## Prerequisites

1. **NVIDIA driver**: recent Game Ready or Studio driver. Check with `nvidia-smi`.
2. **Git**: `winget install Git.Git`
3. **Python 3.10 or 3.11** (many AI repos do not support newer versions yet): `winget install Python.Python.3.11`. Use the `py` launcher to create venvs, for example `py -3.11 -m venv .venv`.
4. **Node.js 20 LTS or newer**: `winget install OpenJS.NodeJS.LTS`
5. **FFmpeg**: `winget install Gyan.FFmpeg` (restart the terminal so it is on PATH). Confirm with `ffmpeg -version` and `ffprobe -version`.
6. **Microsoft C++ Build Tools**: needed to compile some Python wheels.
7. **Enable long paths** (Windows setting and `git config --global core.longpaths true`); some model repos have deep folders.
8. **PyTorch with CUDA**: install from the official PyTorch index that matches your NVIDIA CUDA driver (e.g., CUDA 12.1: `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121`). Do not install the CPU-only wheel.
9. Optional: **WSL2 (Ubuntu)** with GPU support, as a fallback environment.

## Check Prerequisites

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check_prereqs.ps1
```

## Disk and Memory

Plan for at least 50 GB free for neural model weights and working storage for videos (a 60-minute lecture can produce several GB of intermediates). 16 GB of system RAM is recommended; 32 GB is optimal.

## Running the Platform

Run `scripts\run_all.ps1` (or `scripts\run.ps1`) to launch all services concurrently:
- FastAPI Backend (`http://localhost:8000`)
- Background Queue Worker (with GPU concurrency lock)
- Next.js Web Frontend (`http://localhost:3000`)

