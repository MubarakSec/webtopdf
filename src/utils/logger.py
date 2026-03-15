import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logger(name: str = "WebToPDF") -> logging.Logger:
    """
    Sets up a robust logger that outputs to both the console and a rotating file.
    The log file is saved in the user's home directory under a .webtopdf folder.
    """
    logger = logging.getLogger(name)
    
    # Avoid adding multiple handlers if setup is called multiple times
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.DEBUG)

    # Determine log directory (e.g., ~/.webtopdf/logs)
    home_dir = Path.home()
    log_dir = home_dir / ".webtopdf" / "logs"
    
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        # Fallback to current directory if home directory is not writable
        log_dir = Path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "app.log"

    # Create Formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )

    # Rotating File Handler (Max 5MB per file, keep 3 backups)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # Add Handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# Create a default logger instance for easy import
app_logger = setup_logger()
