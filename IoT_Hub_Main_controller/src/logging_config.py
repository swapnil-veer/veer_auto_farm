import logging
from logging.handlers import RotatingFileHandler
import os

# Get absolute path of current file’s directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Logs directory inside src
LOG_DIR = os.path.join(BASE_DIR, "logs")
# Create logs directory if not exists

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Log file paths
SYSTEM_LOG_FILE = os.path.join(LOG_DIR, "system.log")
ERROR_LOG_FILE = os.path.join(LOG_DIR, "errors.log")

def setup_logging():
    """Configure logging for the entire project."""

    # Create logger
    logger = logging.getLogger("auto_farm")
    logger.setLevel(logging.DEBUG)  # Capture all levels

    # Formatter with timestamp, module name, level, and message
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(module)s | %(message)s')

    # Console handler (INFO and above)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Rotating File Handler for system logs
    file_handler = RotatingFileHandler(SYSTEM_LOG_FILE, maxBytes=5*1024*1024, backupCount=5)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Separate handler for ERROR logs
    error_handler = RotatingFileHandler(ERROR_LOG_FILE, maxBytes=5*1024*1024, backupCount=3)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)

    return logger

# Initialize logger
logger = setup_logging()
