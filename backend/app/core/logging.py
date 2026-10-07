import logging
import sys
from typing import Any, Dict


def setup_logging(level: str = "INFO") -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Avoid duplicate handlers if setup_logging called multiple times
    if root_logger.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


logger = logging.getLogger("lecture_dubber")
