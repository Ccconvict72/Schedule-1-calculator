"""
Centralized Logger Module

This module provides a centralized logging system with rotating file handlers
and optional console output. It's designed to provide consistent logging
throughout the application with features like:
- Separate app and error log files
- Log rotation to prevent excessive disk usage
- Optional console logging for development
- Tagged messages for better log filtering
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Determine log folder
try:
    base_dir = os.path.dirname(__file__)
except NameError:
    base_dir = os.getcwd()

LOG_DIR = os.path.join(base_dir, 'logs')
try:
    os.makedirs(LOG_DIR, exist_ok=True)
except Exception:
    LOG_DIR = None

APP_LOG_PATH = os.path.join(LOG_DIR, 'app.log') if LOG_DIR else None
ERROR_LOG_PATH = os.path.join(LOG_DIR, 'error.log') if LOG_DIR else None

logger = logging.getLogger('app_logger')
log_level = os.environ.get("APP_LOG_LEVEL", "DEBUG").upper()
logger.setLevel(getattr(logging, log_level, logging.DEBUG))
logger.propagate = False

formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')

if logger.hasHandlers():
    logger.handlers.clear()

if APP_LOG_PATH:
    general_handler = RotatingFileHandler(
        APP_LOG_PATH,
        maxBytes=1_000_000,
        backupCount=5,
        encoding='utf-8'
    )
    general_handler.setLevel(logging.DEBUG)
    general_handler.setFormatter(formatter)
    logger.addHandler(general_handler)

if ERROR_LOG_PATH:
    error_handler = RotatingFileHandler(
        ERROR_LOG_PATH,
        maxBytes=1_000_000,
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

if os.environ.get("DEV_MODE") == "1":
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

if os.environ.get("ENABLE_LOGGING", "1") != "1":
    logger.disabled = True

def _timestamped_tagged_msg(msg, tag=None):
    time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    tag_str = f"[{tag}]" if tag else ""
    return f"{tag_str} {msg}".strip()

def log_debug(msg, tag=None):
    logger.debug(_timestamped_tagged_msg(msg, tag))

def log_info(msg, tag=None):
    logger.info(_timestamped_tagged_msg(msg, tag))

def log_error(msg, tag=None):
    logger.error(_timestamped_tagged_msg(msg, tag))

def log_critical(msg, tag=None):
    logger.critical(_timestamped_tagged_msg(msg, tag))

def get_logger(name):
    return logging.getLogger(name)

def get_log_paths():
    return {'app': APP_LOG_PATH, 'error': ERROR_LOG_PATH}

def log_warning(message, tag=None):
    if tag:
        message = f"[{tag}] {message}"
    logger.warning(message)
