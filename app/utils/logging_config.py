import logging
from logging.handlers import RotatingFileHandler
import sys
from pathlib import Path

# Set up log file path at the project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
LOG_FILE = PROJECT_ROOT / "bot.log"

def setup_logging():
    """
    Sets up the centralized logging system.
    Logs are written to both standard output (console) and a rotating 'bot.log' file.
    """
    logger = logging.getLogger("bot")
    logger.setLevel(logging.INFO)
    
    # Prevent adding duplicate handlers if setup is called multiple times
    if logger.handlers:
        return logger
        
    # Create formatter with timestamp, level, logger name, file name, line number, and message
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] [%(filename)s:%(lineno)d]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Rotating File Handler (max 10MB per file, keep 3 backup files)
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

# Initialize the global logger instance
logger = setup_logging()
logger.info("Centralized logging system initialized.")
