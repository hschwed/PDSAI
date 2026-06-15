from config.config import Config
import logging
import os

config = Config()

# Ensure the logging directory exists
LOG_FILE = config.log_file
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Configure logging only once
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode='w', encoding="utf-8"),
        logging.StreamHandler(),
    ]
)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
