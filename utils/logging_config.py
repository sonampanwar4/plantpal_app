import logging
import logging.config
import os
from datetime import datetime
from colorist import Color

class ColorFormatter(logging.Formatter):
    LEVEL_COLORS = {
        logging.DEBUG: Color.YELLOW,
        logging.INFO: Color.GREEN,
        logging.WARNING: Color.YELLOW,
        logging.ERROR: Color.RED,
        logging.CRITICAL: Color.RED + Color.YELLOW,
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.LEVEL_COLORS.get(record.levelno, Color.WHITE)
        message = super().format(record)
        return f"{color}{message}{Color.OFF}"

# Define logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,  # Preserve Uvicorn/FastAPI loggers
    "formatters": {
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "simple": {
            "format": "%(levelname)s: %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",  # Capture all levels for console
            "formatter": "detailed",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",  # File logs INFO and above to save space
            "formatter": "detailed",
            "filename": f"logs/plantpal_{datetime.now().strftime('%Y%m%d')}.log",
            "maxBytes": 10485760,  # 10MB per file
            "backupCount": 5  # Keep 5 backup files
        }
    },
    "loggers": {
        "plantpal": {
            "level": "DEBUG",  # Capture all levels for your app
            "handlers": ["console", "file"],
            "propagate": False  # Prevent double-logging
        },
        "uvicorn": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False
        },
        "uvicorn.access": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False
        }
    }
}


def setup_logging():
    """Initialize logging configuration and ensure log directory exists."""
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)

    # Apply logging configuration
    logging.config.dictConfig(LOGGING_CONFIG)

    # Apply colored formatter to console handlers only
    color_formatter = ColorFormatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "%Y-%m-%d %H:%M:%S"
    )

    for handler in logging.getLogger().handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setFormatter(color_formatter)

    # Apply to specific loggers too (important for uvicorn)
    for logger_name in ("plantpal", "uvicorn", "uvicorn.access"):
        logger = logging.getLogger(logger_name)
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setFormatter(color_formatter)
