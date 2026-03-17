import logging
from datetime import datetime
from pathlib import Path

from config import load_config


def setup_logger(name: str = "amine-agent") -> logging.Logger:
    cfg = load_config()
    log_dir = Path(cfg["logging"]["log_dir"])
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = log_dir / f"{timestamp}.log"

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # File handler — full detail
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))

    # Console handler — info and above
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(message)s"))

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger
