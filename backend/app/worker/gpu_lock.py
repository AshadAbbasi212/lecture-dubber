import threading
from contextlib import contextmanager

# In-process thread-safe re-entrant lock for GPU access
_gpu_lock = threading.RLock()


@contextmanager
def acquire_gpu_lock(blocking: bool = True, timeout: float = -1):
    """
    Acquires the GPU lock to guarantee only one GPU-heavy stage runs at any time.
    """
    acquired = _gpu_lock.acquire(blocking=blocking, timeout=timeout)
    if not acquired:
        raise TimeoutError("Could not acquire GPU lock within timeout")
    try:
        yield
    finally:
        _gpu_lock.release()
