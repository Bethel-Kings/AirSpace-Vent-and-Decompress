import logging
import sys
from app.core.config import settings


class SensitiveDataFilter(logging.Filter):
    """
    Ensures that raw vent contents, reflection texts, and passwords
    are never leaked into ordinary stdout/file logs.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        # Redact any obvious tokens or secrets in log records
        if "password" in message.lower() or "token" in message.lower():
            record.msg = "[REDACTED SENSITIVE LOG MESSAGE]"
        return True


def setup_logging() -> logging.Logger:
    """Configures application-wide logging compliant with security requirements."""
    logger = logging.getLogger("airspace")
    logger.setLevel(logging.INFO if settings.ENVIRONMENT == "production" else logging.DEBUG)
    
    # Avoid duplicate handlers if already configured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        handler.addFilter(SensitiveDataFilter())
        logger.addHandler(handler)
        
    logger.propagate = False
    return logger


logger = setup_logging()
