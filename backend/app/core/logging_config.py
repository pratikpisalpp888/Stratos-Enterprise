import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from app.config.settings import settings

LOGS_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

def setup_logging():
    log_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)

    file_handler = TimedRotatingFileHandler(
        filename=LOGS_DIR / "sentinelrag.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setFormatter(log_format)

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)
    
    if not root_logger.handlers:
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

setup_logging()
