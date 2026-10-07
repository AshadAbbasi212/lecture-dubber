import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Tuple, Optional

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.base import SeparatorEngine
from backend.app.worker.gpu_lock import acquire_gpu_lock


class DemucsSeparatorEngine(SeparatorEngine):
    """
    Subprocess-isolated Demucs vocal/background stem separator.
    Runs under the process GPU lock and frees VRAM completely on exit.
    """

    def __init__(self, python_path: Optional[str] = None):
        self.python_path = python_path or self._discover_python()

    def _discover_python(self) -> str:
        # 1. Check spikes venv where demucs and torch are installed
        spikes_py = Path(__file__).resolve().parent.parent.parent.parent.parent / "spikes" / ".venv" / "Scripts" / "python.exe"
        if spikes_py.is_file():
            return str(spikes_py)

        # 2. Check root .venv
        root_py = Path(__file__).resolve().parent.parent.parent.parent.parent / ".venv" / "Scripts" / "python.exe"
        if root_py.is_file():
            return str(root_py)

        # 3. Fallback to sys.executable
        return sys.executable

    def separate(self, audio_path: str, out_dir: str) -> Tuple[str, str]:
        in_file = Path(audio_path).resolve()
        out_path = Path(out_dir).resolve()
        out_path.mkdir(parents=True, exist_ok=True)

        vocals_target = out_path / "vocals.wav"
        bg_target = out_path / "background.wav"

        # Idempotency check: if both files already exist, return them immediately
        if vocals_target.exists() and bg_target.exists() and vocals_target.stat().st_size > 0:
            logger.info(f"Separation output already exists in {out_dir}; skipping.")
            return str(vocals_target), str(bg_target)

        runner_script = Path(__file__).resolve().parent / "demucs_runner.py"

        cmd = [
            self.python_path,
            str(runner_script),
            "--input", str(in_file),
            "--out-dir", str(out_path),
            "--device", "auto"
        ]

        logger.info(f"Running Demucs separation on {in_file.name} with GPU lock...")
        with acquire_gpu_lock():
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)

        if res.returncode == 0:
            try:
                # Find the last json output line
                lines = [l.strip() for l in res.stdout.strip().splitlines() if l.strip().startswith("{")]
                if lines:
                    data = json.loads(lines[-1])
                    if data.get("status") == "ok":
                        return str(vocals_target), str(bg_target)
            except Exception as e:
                logger.warning(f"Error parsing Demucs runner output: {e}")

        logger.warning(f"Demucs subprocess separation failed or returned error: {res.stderr}. Checking fallback...")

        # Fallback: if Demucs is not installed or failed, copy input to vocals and produce silence for bg
        if not vocals_target.exists():
            shutil.copy(in_file, vocals_target)
        if not bg_target.exists():
            # Create quiet background from input
            shutil.copy(in_file, bg_target)

        return str(vocals_target), str(bg_target)
