"""
Shared utilities for Bear Blog automation bots.
"""

import os
import re
import logging
import yaml
import requests
from pathlib import Path
from time import sleep
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter, Retry

# --- LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# --- CONFIG ---
def load_config() -> dict:
    """Load configuration from central config.yaml file."""
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


CONFIG = load_config()


# --- CONSTANTS ---
REQUEST_TIMEOUT = 15  # seconds
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # seconds
MAX_IMAGE_SIZE = 10_000_000  # 10MB
MAX_CSV_SIZE = 50_000_000  # 50MB
MAX_WORKERS = 5  # Concurrent operations


# --- EXCEPTIONS ---
class BotException(Exception):
    """Base exception for all bot errors."""
    pass


class AuthenticationError(BotException):
    """Raised when authentication fails."""
    pass


class ConfigurationError(BotException):
    """Raised when configuration is invalid."""
    pass


class DownloadError(BotException):
    """Raised when download fails."""
    pass


# --- SECURITY ---
def is_safe_url(url: str) -> bool:
    """Validate that the URL uses a safe protocol (HTTP/HTTPS)."""
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
    """
    filename = os.path.basename(filename)
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    if filename.startswith('.'):
        filename = '_' + filename
    if not filename or len(filename) > 255:
        filename = 'image.webp'
    return filename


def clean_filename(text: str) -> str:
    """
    Creates a safe filename for files and folders.
    Removes special characters and emojis.
    """
    text = re.sub(r'[^\w\s-]', '', str(text)).strip().lower()
    text = re.sub(r'[-\s]+', '-', text)
    return text[:100]


# --- HTTP ---
def create_session(user_agent: str = 'bearblog-bot/2.0') -> requests.Session:
    """Create a requests session with connection pooling and retry logic."""
    session = requests.Session()
    session.headers.update({'User-Agent': user_agent})

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


# --- FILE LOCKING ---
class FileLock:
    """
    Atomic file-based lock using os.open with O_CREAT | O_EXCL.

    Features:
    - True atomic lock acquisition (no race conditions)
    - Stale lock detection and cleanup
    - Process ID and timestamp tracking
    - Configurable timeout with exponential backoff
    - Proper cleanup on exit

    Usage:
        with FileLock(Path('my.lock')) as lock:
            # critical section
            pass
    """

    def __init__(
        self,
        lock_path: Path,
        timeout: float = 30.0,
        stale_timeout: float = 300.0,  # 5 minutes
        initial_backoff: float = 0.1
    ):
        """
        Initialize file lock.

        Args:
            lock_path: Path to the lock file
            timeout: Maximum time to wait for lock acquisition (seconds)
            stale_timeout: Time after which a lock is considered stale (seconds)
            initial_backoff: Initial backoff time for retries (seconds)
        """
        self.lock_path = lock_path
        self.timeout = timeout
        self.stale_timeout = stale_timeout
        self.initial_backoff = initial_backoff
        self._acquired = False
        self._fd = None

    def _is_stale(self) -> bool:
        """Check if existing lock file is stale."""
        try:
            if not self.lock_path.exists():
                return False

            # Check file age
            import time
            file_age = time.time() - self.lock_path.stat().st_mtime
            if file_age > self.stale_timeout:
                logger.warning(
                    f"Detected stale lock file (age: {file_age:.1f}s > {self.stale_timeout}s): "
                    f"{self.lock_path}"
                )
                return True

            # Try to read lock metadata to check if process still exists
            try:
                lock_data = self.lock_path.read_text().strip()
                if lock_data:
                    pid = int(lock_data.split(':')[0])
                    # Check if process exists
                    try:
                        os.kill(pid, 0)  # Signal 0 just checks if process exists
                        return False  # Process exists, lock is valid
                    except (OSError, ProcessLookupError):
                        logger.warning(
                            f"Lock file references dead process {pid}: {self.lock_path}"
                        )
                        return True  # Process doesn't exist, lock is stale
            except (ValueError, IndexError, IOError):
                # Can't parse lock file, consider it stale if old enough
                pass

            return False
        except Exception as e:
            logger.warning(f"Error checking lock staleness: {e}")
            return False

    def _clean_stale_lock(self) -> bool:
        """Remove stale lock file. Returns True if cleaned, False otherwise."""
        try:
            if self._is_stale():
                self.lock_path.unlink()
                logger.info(f"Removed stale lock file: {self.lock_path}")
                return True
        except Exception as e:
            logger.warning(f"Failed to remove stale lock: {e}")
        return False

    def acquire(self) -> bool:
        """
        Acquire the lock with exponential backoff.

        Returns:
            True if lock was acquired

        Raises:
            TimeoutError: If lock could not be acquired within timeout
        """
        import time

        start_time = time.time()
        backoff = self.initial_backoff
        attempt = 0

        while True:
            try:
                # Try atomic lock creation using O_CREAT | O_EXCL
                # This is atomic at the OS level - no race condition possible
                fd = os.open(
                    str(self.lock_path),
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                    0o644
                )

                # Write lock metadata (PID and timestamp)
                lock_info = f"{os.getpid()}:{time.time():.0f}\n"
                os.write(fd, lock_info.encode())
                os.close(fd)

                self._acquired = True
                logger.debug(f"Acquired lock: {self.lock_path}")
                return True

            except FileExistsError:
                # Lock file exists - check if stale
                if self._clean_stale_lock():
                    # Stale lock was cleaned, try again immediately
                    continue

                # Check timeout
                elapsed = time.time() - start_time
                if elapsed >= self.timeout:
                    raise TimeoutError(
                        f"Could not acquire lock {self.lock_path} after {elapsed:.1f}s "
                        f"(timeout: {self.timeout}s, attempts: {attempt})"
                    )

                # Wait with exponential backoff
                sleep(min(backoff, 2.0))  # Cap backoff at 2 seconds
                backoff *= 1.5
                attempt += 1

                if attempt % 10 == 0:
                    logger.debug(
                        f"Still waiting for lock {self.lock_path} "
                        f"(elapsed: {elapsed:.1f}s, attempt: {attempt})"
                    )

            except Exception as e:
                logger.error(f"Unexpected error acquiring lock: {e}")
                raise

    def release(self) -> None:
        """Release the lock by removing the lock file."""
        if not self._acquired:
            return

        try:
            if self.lock_path.exists():
                self.lock_path.unlink()
                logger.debug(f"Released lock: {self.lock_path}")
        except Exception as e:
            logger.warning(f"Error releasing lock {self.lock_path}: {e}")
        finally:
            self._acquired = False

    def force_unlock(self) -> None:
        """Force remove lock file (use with caution!)."""
        try:
            if self.lock_path.exists():
                self.lock_path.unlink()
                logger.warning(f"Force unlocked: {self.lock_path}")
        except Exception as e:
            logger.error(f"Failed to force unlock {self.lock_path}: {e}")

    def __enter__(self) -> 'FileLock':
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()
        return False  # Don't suppress exceptions

    def __del__(self):
        """Ensure lock is released on garbage collection."""
        if self._acquired:
            self.release()
