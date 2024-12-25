# api/logger.py
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Create logs directory if it doesn't exist
logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(logs_dir, exist_ok=True)

# Configure logger
logger = logging.getLogger('youtube_summarizer')
logger.setLevel(logging.INFO)

# Create formatters
file_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
console_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)

# File handler with rotation
log_file = os.path.join(logs_dir, f'app_{datetime.now().strftime("%Y%m%d")}.log')
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(file_formatter)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(console_formatter)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)
