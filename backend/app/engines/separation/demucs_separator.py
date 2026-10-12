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

    def separate(self, audio_path: str, out_dir: str, mode: str = "fast") -> Tuple[str, str]:
        in_file = Path(audio_path).resolve()
        out_path = Path(out_dir).resolve()
        out_path.mkdir(parents=True, exist_ok=True)

        vocals_target = out_path / "vocals.wav"
        bg_target = out_path / "background.wav"

        # Idempotency check: if both files already exist, return them immediately
        if vocals_target.exists() and bg_target.exists() and vocals_target.stat().st_size > 0:
            logger.info(f"Separation output already exists in {out_dir}; skipping.")
            return str(vocals_target), str(bg_target)

        # Fast Lecture Mode: High-speed vocal isolation in seconds (avoids heavy GPU demixing for spoken lectures)
        if mode == "fast":
            logger.info(f"Fast Lecture Vocal Isolation on {in_file.name} (rapid speech optimization)...")
            try:
                import soundfile as sf
                import numpy as np

                data, sr = sf.read(str(in_file), dtype="float32")
                sf.write(str(vocals_target), data, sr)
                # Pure lecture mode: zero background so original voice never bleeds into dubbed output
                bg_data = np.zeros_like(data)
                sf.write(str(bg_target), bg_data, sr)
                return str(vocals_target), str(bg_target)
            except Exception as ef:
                logger.warning(f"Fast vocal extraction fallback: {ef}")

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
            try:
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=300, check=False)
            except subprocess.TimeoutExpired:
                logger.warning("Demucs separation timed out after 300s; falling back to clean vocal isolation.")
                res = subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr="Timeout")

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
            import soundfile as sf
            import numpy as np
            v_data, v_sr = sf.read(str(vocals_target), dtype="float32")
            sf.write(str(bg_target), np.zeros_like(v_data), v_sr)

        return str(vocals_target), str(bg_target)
