"""
File tracking utilities with locking support.
"""

import logging
from pathlib import Path
from contextlib import contextmanager
from time import sleep
from typing import Generator

logger = logging.getLogger(__name__)


class FileLock:
    """
    Simple file-based lock with exponential backoff.

    Usage:
        lock = FileLock(Path("myfile.txt.lock"))
        with lock:
            # Do something with exclusive access
            pass
    """

    def __init__(self, lock_path: Path, max_retries: int = 10, initial_backoff: float = 0.5):
        """
        Initialize file lock.

        Args:
            lock_path: Path to the lock file
            max_retries: Maximum number of retry attempts
            initial_backoff: Initial backoff time in seconds
        """
        self.lock_path = lock_path
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff

    def acquire(self) -> bool:
        """
        Acquire the lock with exponential backoff.

        Returns:
            True if lock acquired, False otherwise

        Raises:
            TimeoutError: If lock cannot be acquired after max_retries
        """
        retry = 0
        backoff = self.initial_backoff

        while self.lock_path.exists() and retry < self.max_retries:
            sleep(backoff)
            backoff *= 1.5  # Exponential backoff
            retry += 1

        if self.lock_path.exists():
            raise TimeoutError(f"Could not acquire lock after {self.max_retries} retries")

        self.lock_path.touch()
        return True

    def release(self) -> None:
        """Release the lock."""
        if self.lock_path.exists():
            self.lock_path.unlink()

    def __enter__(self) -> 'FileLock':
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()


@contextmanager
def file_lock(lock_path: Path, max_retries: int = 10, initial_backoff: float = 0.5) -> Generator[None, None, None]:
    """
    Context manager for file locking with exponential backoff.

    Args:
        lock_path: Path to the lock file
        max_retries: Maximum number of retry attempts
        initial_backoff: Initial backoff time in seconds

    Yields:
        None

    Raises:
        TimeoutError: If lock cannot be acquired after max_retries
    """
    lock = FileLock(lock_path, max_retries, initial_backoff)
    try:
        lock.acquire()
        yield
    finally:
        lock.release()
