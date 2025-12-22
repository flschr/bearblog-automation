"""
Shared utilities for Bear Blog automation bots.
"""

from .config import load_config, CONFIG
from .logging_setup import setup_logging, logger
from .exceptions import AuthenticationError, ConfigurationError, DownloadError
from .constants import (
    REQUEST_TIMEOUT,
    MAX_IMAGE_SIZE,
    MAX_RETRIES,
    RETRY_BACKOFF,
    MAX_WORKERS,
)
from .security import is_safe_url, sanitize_filename, clean_filename
from .http import create_session, download_file
from .tracking import FileLock

__all__ = [
    # Config
    'load_config',
    'CONFIG',
    # Logging
    'setup_logging',
    'logger',
    # Exceptions
    'AuthenticationError',
    'ConfigurationError',
    'DownloadError',
    # Constants
    'REQUEST_TIMEOUT',
    'MAX_IMAGE_SIZE',
    'MAX_RETRIES',
    'RETRY_BACKOFF',
    'MAX_WORKERS',
    # Security
    'is_safe_url',
    'sanitize_filename',
    'clean_filename',
    # HTTP
    'create_session',
    'download_file',
    # Tracking
    'FileLock',
]
