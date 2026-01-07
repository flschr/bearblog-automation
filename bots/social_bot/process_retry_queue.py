#!/usr/bin/env python3
"""
Process Retry Queue - Attempts to re-post articles that had partial failures.

This script is run before the main social bot to retry articles that
failed to post to some platforms on previous attempts.
"""

import sys
import logging
from pathlib import Path

# Add directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))  # For shared module
sys.path.insert(0, str(Path(__file__).parent))  # For local modules

from retry_queue import RetryQueue
from social_bot import (
    post_to_bluesky,
    post_to_mastodon,
    get_first_image_data,
    download_image,
    CONFIG_FILE,
    PLATFORM_BLUESKY,
    PLATFORM_MASTODON,
    BASE_DIR,
)
from shared import CONFIG
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

RETRY_QUEUE_FILE = BASE_DIR / 'retry_queue.json'
RETRY_QUEUE_LOCK = BASE_DIR / 'retry_queue.json.lock'


def retry_article(entry, config) -> tuple[list, list]:
    """
    Attempt to retry posting an article to pending platforms.

    Args:
        entry: RetryQueueEntry object
        config: Social bot configuration

    Returns:
        Tuple of (newly_succeeded_platforms, still_failed_platforms)
    """
    logger.info(
        f"Retrying: {entry.article_title} (attempt {entry.retry_count + 1}) - "
        f"pending platforms: {entry.pending_platforms}"
    )

    # Find the config entry for this article
    # We'll use a simple template since we don't have the full entry data
    msg = f"📝 {entry.article_title}\n{entry.article_url}"

    newly_succeeded = []
    still_failed = []

    # Try each pending platform
    for platform in entry.pending_platforms:
        try:
            if platform == PLATFORM_BLUESKY:
                url = post_to_bluesky(msg, None, "", link=entry.article_url)
                if url:
                    newly_succeeded.append(platform)
                    logger.info(f"✓ Retry succeeded for {platform}: {entry.article_title}")
                else:
                    still_failed.append({
                        'platform': platform,
                        'error': 'Post returned None'
                    })

            elif platform == PLATFORM_MASTODON:
                url = post_to_mastodon(msg, None, "")
                if url:
                    newly_succeeded.append(platform)
                    logger.info(f"✓ Retry succeeded for {platform}: {entry.article_title}")
                else:
                    still_failed.append({
                        'platform': platform,
                        'error': 'Post returned None'
                    })

        except Exception as e:
            error_msg = str(e)
            logger.error(f"✗ Retry failed for {platform}: {entry.article_title} - {error_msg}")
            still_failed.append({
                'platform': platform,
                'error': error_msg
            })

    return newly_succeeded, still_failed


def main():
    """Main entry point for retry queue processor."""
    logger.info("=== Retry Queue Processor Start ===")

    try:
        # Initialize retry queue with config
        retry_queue = RetryQueue(RETRY_QUEUE_FILE, RETRY_QUEUE_LOCK, CONFIG)

        # Get queue statistics
        stats = retry_queue.get_stats()
        logger.info(f"Queue stats: {stats}")

        # Get entries ready for retry
        ready_entries = retry_queue.get_ready_entries()

        if not ready_entries:
            logger.info("No entries ready for retry")
            return

        logger.info(f"Processing {len(ready_entries)} entries from retry queue")

        # Load config for platform credentials check
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Process each entry
        for entry in ready_entries:
            try:
                newly_succeeded, still_failed = retry_article(entry, config)

                # Update queue based on results
                retry_queue.update_after_retry(
                    entry.article_url,
                    still_failed,
                    newly_succeeded
                )

            except Exception as e:
                logger.error(f"Error processing retry for {entry.article_url}: {e}")
                # Mark as still failed without updating retry count
                # This allows it to be retried again on the next run
                continue

        # Report exhausted entries
        exhausted = retry_queue.get_exhausted_entries()
        if exhausted:
            logger.warning(
                f"Found {len(exhausted)} entries that have exhausted all retries"
            )
            for entry in exhausted:
                logger.warning(
                    f"  - {entry.article_title}: pending={entry.pending_platforms}"
                )

        logger.info("=== Retry Queue Processor End ===")

    except Exception as e:
        logger.error(f"Fatal error in retry queue processor: {e}")
        raise


if __name__ == "__main__":
    main()
