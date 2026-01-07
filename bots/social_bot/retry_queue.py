"""
Retry Queue System for managing partial posting failures.

This module handles articles that failed to post to some platforms
but succeeded on others, implementing intelligent retry logic with
exponential backoff and error categorization.
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Categories of errors for retry decisions."""
    RETRIABLE = "retriable"  # Temporary errors, worth retrying
    NON_RETRIABLE = "non_retriable"  # Permanent errors, don't retry
    UNKNOWN = "unknown"  # Unknown errors, retry with caution


# HTTP status codes that are worth retrying
RETRIABLE_STATUS_CODES = {500, 502, 503, 504, 408, 429}
NON_RETRIABLE_STATUS_CODES = {400, 401, 403, 404, 422, 451}

# Error keywords that indicate retriable errors
RETRIABLE_KEYWORDS = ["timeout", "connection", "network", "temporary", "unavailable"]


@dataclass
class PlatformFailure:
    """Represents a failed posting attempt to a specific platform."""
    platform: str
    error_message: str
    error_category: str
    timestamp: str


@dataclass
class RetryQueueEntry:
    """Represents an article in the retry queue."""
    article_url: str
    article_title: str
    pending_platforms: List[str]
    completed_platforms: List[str]
    failures: List[Dict[str, Any]]
    retry_count: int
    created_at: str
    last_attempt: str
    next_retry_after: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RetryQueueEntry':
        """Create from dictionary."""
        return cls(**data)


class RetryQueue:
    """
    Manages the retry queue for articles with partial posting failures.

    Features:
    - Configurable retry scheduling (default: 1h, 4h, 12h)
    - Error categorization (retriable vs non-retriable)
    - Automatic cleanup after max retries
    - Thread-safe operations with file locking
    """

    def __init__(self, queue_file: Path, lock_file: Path, config: Optional[Dict[str, Any]] = None):
        """
        Initialize retry queue.

        Args:
            queue_file: Path to retry queue JSON file
            lock_file: Path to lock file for queue operations
            config: Optional config dict with retry_queue settings
        """
        self.queue_file = queue_file
        self.lock_file = lock_file

        # Load retry configuration from config or use defaults
        if config and 'social' in config and 'retry_queue' in config['social']:
            retry_config = config['social']['retry_queue']
            retry_hours = retry_config.get('retry_delays_hours', [1, 4, 12])
            self.max_retries = retry_config.get('max_retries', 3)
        else:
            # Default retry schedule: 1h, 4h, 12h
            retry_hours = [1, 4, 12]
            self.max_retries = 3

        # Convert hours to timedelta objects
        # Add initial attempt (0 hours) at the beginning
        self.retry_delays = [timedelta(hours=0)]  # Immediate (first attempt)
        self.retry_delays.extend([timedelta(hours=h) for h in retry_hours])

        logger.info(
            f"Retry queue initialized: {len(self.retry_delays)-1} retry attempts, "
            f"delays: {', '.join([str(d) for d in self.retry_delays[1:]])}"
        )

    def _load_queue(self) -> Dict[str, Dict[str, Any]]:
        """Load retry queue from disk."""
        if not self.queue_file.exists():
            return {}

        try:
            with open(self.queue_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading retry queue: {e}")
            return {}

    def _save_queue(self, queue: Dict[str, Dict[str, Any]]) -> None:
        """Save retry queue to disk."""
        try:
            # Ensure directory exists
            self.queue_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.queue_file, 'w', encoding='utf-8') as f:
                json.dump(queue, f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved retry queue with {len(queue)} entries")
        except Exception as e:
            logger.error(f"Error saving retry queue: {e}")

    def categorize_error(self, error_message: str, platform: str) -> ErrorCategory:
        """
        Categorize an error to determine if it's retriable.

        Args:
            error_message: The error message to categorize
            platform: The platform that failed (for platform-specific logic)

        Returns:
            ErrorCategory indicating whether to retry
        """
        error_lower = error_message.lower()

        # Check for HTTP status codes
        for code in RETRIABLE_STATUS_CODES:
            if str(code) in error_message:
                return ErrorCategory.RETRIABLE

        for code in NON_RETRIABLE_STATUS_CODES:
            if str(code) in error_message:
                return ErrorCategory.NON_RETRIABLE

        # Check for retriable keywords
        for keyword in RETRIABLE_KEYWORDS:
            if keyword in error_lower:
                return ErrorCategory.RETRIABLE

        # Default to unknown (will retry but with caution)
        return ErrorCategory.UNKNOWN

    def add_to_queue(
        self,
        article_url: str,
        article_title: str,
        failed_platforms: List[Dict[str, str]],
        successful_platforms: List[str]
    ) -> None:
        """
        Add an article with partial failures to the retry queue.

        Args:
            article_url: URL of the article
            article_title: Title of the article
            failed_platforms: List of dicts with 'platform' and 'error' keys
            successful_platforms: List of platforms that succeeded
        """
        from bots.shared import FileLock

        with FileLock(self.lock_file):
            queue = self._load_queue()
            now = datetime.now(timezone.utc).isoformat()

            # Categorize failures
            failures = []
            pending = []

            for failure_info in failed_platforms:
                platform = failure_info['platform']
                error_msg = failure_info['error']
                category = self.categorize_error(error_msg, platform)

                failures.append({
                    'platform': platform,
                    'error_message': error_msg,
                    'error_category': category.value,
                    'timestamp': now
                })

                # Only add to pending if retriable or unknown
                if category in (ErrorCategory.RETRIABLE, ErrorCategory.UNKNOWN):
                    pending.append(platform)
                else:
                    logger.warning(
                        f"Skipping retry for {platform} due to non-retriable error: {error_msg}"
                    )

            if not pending:
                logger.info(
                    f"No retriable platforms for {article_url}, not adding to retry queue"
                )
                return

            # Calculate next retry time (1 hour from now for first retry)
            next_retry = datetime.now(timezone.utc) + self.retry_delays[1]

            entry = RetryQueueEntry(
                article_url=article_url,
                article_title=article_title,
                pending_platforms=pending,
                completed_platforms=successful_platforms,
                failures=failures,
                retry_count=0,
                created_at=now,
                last_attempt=now,
                next_retry_after=next_retry.isoformat()
            )

            queue[article_url] = entry.to_dict()
            self._save_queue(queue)

            logger.info(
                f"Added to retry queue: {article_title} - "
                f"pending: {pending}, completed: {successful_platforms}"
            )

    def get_ready_entries(self) -> List[RetryQueueEntry]:
        """
        Get entries that are ready for retry (past their next_retry_after time).

        Returns:
            List of RetryQueueEntry objects ready for retry
        """
        from bots.shared import FileLock

        with FileLock(self.lock_file):
            queue = self._load_queue()
            now = datetime.now(timezone.utc)
            ready = []

            for url, data in queue.items():
                try:
                    entry = RetryQueueEntry.from_dict(data)

                    # Check if it's time to retry
                    next_retry = datetime.fromisoformat(entry.next_retry_after)
                    if now >= next_retry:
                        ready.append(entry)

                except Exception as e:
                    logger.error(f"Error parsing queue entry for {url}: {e}")

            logger.info(f"Found {len(ready)} entries ready for retry")
            return ready

    def update_after_retry(
        self,
        article_url: str,
        still_failed_platforms: List[Dict[str, str]],
        newly_succeeded_platforms: List[str]
    ) -> None:
        """
        Update queue entry after a retry attempt.

        Args:
            article_url: URL of the article
            still_failed_platforms: Platforms that still failed
            newly_succeeded_platforms: Platforms that succeeded this time
        """
        from bots.shared import FileLock

        with FileLock(self.lock_file):
            queue = self._load_queue()

            if article_url not in queue:
                logger.warning(f"Article {article_url} not in retry queue")
                return

            entry = RetryQueueEntry.from_dict(queue[article_url])
            now = datetime.now(timezone.utc)
            entry.last_attempt = now.isoformat()
            entry.retry_count += 1

            # Update completed platforms
            entry.completed_platforms.extend(newly_succeeded_platforms)

            # Update pending platforms
            entry.pending_platforms = [
                p for p in entry.pending_platforms
                if p not in newly_succeeded_platforms
            ]

            # Add new failure records
            for failure_info in still_failed_platforms:
                platform = failure_info['platform']
                error_msg = failure_info['error']
                category = self.categorize_error(error_msg, platform)

                entry.failures.append({
                    'platform': platform,
                    'error_message': error_msg,
                    'error_category': category.value,
                    'timestamp': now.isoformat()
                })

            # Check if all platforms succeeded
            if not entry.pending_platforms:
                logger.info(
                    f"All platforms succeeded for {entry.article_title}, removing from queue"
                )
                del queue[article_url]
                self._save_queue(queue)
                return

            # Check if max retries exceeded
            if entry.retry_count >= self.max_retries:
                logger.warning(
                    f"Max retries ({self.max_retries}) exceeded for {entry.article_title}, "
                    f"still pending: {entry.pending_platforms}"
                )
                # Keep in queue but don't schedule another retry
                # Will be reported as exhausted
                entry.next_retry_after = "exhausted"
            else:
                # Schedule next retry
                delay = self.retry_delays[entry.retry_count + 1]
                next_retry = now + delay
                entry.next_retry_after = next_retry.isoformat()

                logger.info(
                    f"Scheduled retry {entry.retry_count + 1} for {entry.article_title} "
                    f"at {next_retry.isoformat()}"
                )

            queue[article_url] = entry.to_dict()
            self._save_queue(queue)

    def remove_from_queue(self, article_url: str) -> None:
        """Remove an entry from the queue."""
        from bots.shared import FileLock

        with FileLock(self.lock_file):
            queue = self._load_queue()

            if article_url in queue:
                del queue[article_url]
                self._save_queue(queue)
                logger.info(f"Removed {article_url} from retry queue")

    def get_exhausted_entries(self) -> List[RetryQueueEntry]:
        """
        Get entries that have exhausted all retries.

        Returns:
            List of RetryQueueEntry objects that have exhausted retries
        """
        from bots.shared import FileLock

        with FileLock(self.lock_file):
            queue = self._load_queue()
            exhausted = []

            for url, data in queue.items():
                try:
                    entry = RetryQueueEntry.from_dict(data)

                    if entry.next_retry_after == "exhausted":
                        exhausted.append(entry)

                except Exception as e:
                    logger.error(f"Error parsing queue entry for {url}: {e}")

            return exhausted

    def clear_exhausted(self) -> int:
        """
        Remove all exhausted entries from queue.

        Returns:
            Number of entries removed
        """
        from bots.shared import FileLock

        with FileLock(self.lock_file):
            queue = self._load_queue()
            initial_count = len(queue)

            queue = {
                url: data for url, data in queue.items()
                if data.get('next_retry_after') != 'exhausted'
            }

            removed = initial_count - len(queue)
            if removed > 0:
                self._save_queue(queue)
                logger.info(f"Cleared {removed} exhausted entries from retry queue")

            return removed

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the retry queue."""
        from bots.shared import FileLock

        with FileLock(self.lock_file):
            queue = self._load_queue()

            stats = {
                'total_entries': len(queue),
                'ready_for_retry': 0,
                'waiting': 0,
                'exhausted': 0,
                'by_platform': {}
            }

            now = datetime.now(timezone.utc)

            for data in queue.values():
                try:
                    entry = RetryQueueEntry.from_dict(data)

                    if entry.next_retry_after == 'exhausted':
                        stats['exhausted'] += 1
                    else:
                        next_retry = datetime.fromisoformat(entry.next_retry_after)
                        if now >= next_retry:
                            stats['ready_for_retry'] += 1
                        else:
                            stats['waiting'] += 1

                    # Count by platform
                    for platform in entry.pending_platforms:
                        stats['by_platform'][platform] = stats['by_platform'].get(platform, 0) + 1

                except Exception:
                    pass

            return stats
