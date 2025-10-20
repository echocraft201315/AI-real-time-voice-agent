import logging
import coloredlogs

# Define logging formats
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = logging.DEBUG  # Change to logging.INFO in production

# Configure root logger
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)

# Add colored logs
coloredlogs.install(level=LOG_LEVEL, fmt=LOG_FORMAT)

def get_logger(name: str) -> logging.Logger:
    """Helper to get logger by name."""
    return logging.getLogger(name)

# Create a default logger
logger = get_logger(__name__)