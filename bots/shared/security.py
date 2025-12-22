"""
Security utilities for URL and filename validation.
"""

import os
import re
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def is_safe_url(url: str) -> bool:
    """
    Validate that the URL uses a safe protocol (HTTP/HTTPS).

    Args:
        url: URL to validate

    Returns:
        True if URL is safe, False otherwise
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            logger.warning(f"Rejected URL with unsafe protocol: {parsed.scheme}")
            return False
        return True
    except Exception as e:
        logger.warning(f"Error validating URL: {e}")
        return False


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks.
    Returns only the basename without any directory components.

    Args:
        filename: Filename to sanitize

    Returns:
        Safe filename string
    """
    # Remove any path components
    filename = os.path.basename(filename)

    # Remove dangerous characters
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

    # Prevent hidden files
    if filename.startswith('.'):
        filename = '_' + filename

    # Ensure filename is not empty and has reasonable length
    if not filename or len(filename) > 255:
        filename = 'image.webp'

    return filename


def clean_filename(text: str) -> str:
    """
    Creates a safe filename for files and folders.
    Removes special characters and emojis.

    Args:
        text: Text to convert to filename

    Returns:
        Clean filename string
    """
    # Remove emojis and special characters
    text = re.sub(r'[^\w\s-]', '', str(text)).strip().lower()
    # Replace spaces and multiple hyphens with single hyphen
    text = re.sub(r'[-\s]+', '-', text)
    # Limit length
    return text[:100]
