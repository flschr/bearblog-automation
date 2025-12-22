"""
HTTP utilities with connection pooling and retry logic.
"""

import logging
import requests
from requests.adapters import HTTPAdapter, Retry
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional

from .constants import REQUEST_TIMEOUT, MAX_IMAGE_SIZE, MAX_RETRIES, RETRY_BACKOFF
from .security import is_safe_url, sanitize_filename

logger = logging.getLogger(__name__)


def create_session(user_agent: str = 'bearblog-bot/2.0') -> requests.Session:
    """
    Create a requests session with connection pooling and retry logic.

    Args:
        user_agent: User agent string for requests

    Returns:
        Configured requests.Session instance
    """
    session = requests.Session()
    session.headers.update({'User-Agent': user_agent})

    # Connection pooling with automatic retry
    adapter = HTTPAdapter(
        pool_connections=10,
        pool_maxsize=20,
        max_retries=Retry(
            total=MAX_RETRIES,
            backoff_factor=RETRY_BACKOFF,
            status_forcelist=[500, 502, 503, 504]
        )
    )
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    return session


def download_file(
    url: str,
    folder: Path,
    session: Optional[requests.Session] = None,
    max_size: int = MAX_IMAGE_SIZE,
    timeout: int = REQUEST_TIMEOUT
) -> bool:
    """
    Downloads a file with security checks and proper error handling.

    Args:
        url: URL to download from
        folder: Directory to save the file
        session: Optional requests session (creates new one if not provided)
        max_size: Maximum file size in bytes
        timeout: Request timeout in seconds

    Returns:
        True if download successful, False otherwise
    """
    try:
        # Security: Validate URL
        if not is_safe_url(url):
            logger.warning(f"Skipping unsafe URL: {url}")
            return False

        # Extract and sanitize filename
        url_path = urlparse(url).path
        file_name = url_path.split("/")[-1].split("?")[0]

        if not file_name:
            file_name = "image.webp"

        file_name = sanitize_filename(file_name)
        path = folder / file_name

        logger.info(f"Downloading: {file_name}")

        # Use provided session or create a simple request
        if session:
            response = session.get(url, stream=True, timeout=timeout)
        else:
            response = requests.get(url, stream=True, timeout=timeout)

        response.raise_for_status()

        # Check content length
        content_length = int(response.headers.get('content-length', 0))
        if content_length > max_size:
            logger.warning(f"File too large ({content_length} bytes): {url}")
            return False

        # Download with size check
        total_size = 0
        with open(path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                total_size += len(chunk)
                if total_size > max_size:
                    logger.warning(f"Download exceeded size limit: {url}")
                    path.unlink()
                    return False
                f.write(chunk)

        logger.info(f"Successfully downloaded: {file_name}")
        return True

    except requests.exceptions.RequestException as e:
        logger.warning(f"HTTP error downloading {url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error downloading {url}: {e}")
        return False
