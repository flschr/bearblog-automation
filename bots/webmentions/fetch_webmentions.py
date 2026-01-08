#!/usr/bin/env python3
"""
Fetch webmentions from webmention.io and store blog-only mentions.
Excludes social media platforms (Mastodon, Bluesky) as they're already tracked in mappings.json.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set
from urllib.parse import urlparse

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared import (
    logger,
    load_config,
    FileLock,
    BotException
)

# Configuration
WEBMENTIONS_FILE = Path(__file__).parent.parent.parent / "webmentions.json"
WEBMENTION_IO_API = "https://webmention.io/api/mentions.jf2"

# Social media domains to exclude (already tracked in mappings.json)
EXCLUDED_SOCIAL_DOMAINS = {
    'mastodon.social',
    'bsky.app',
    'twitter.com',
    'x.com',
    'threads.net',
    'linkedin.com',
    'facebook.com',
    'instagram.com',
    # Add other Mastodon instances
    'fosstodon.org',
    'hachyderm.io',
    'mas.to',
    'mstdn.social',
    'infosec.exchange',
}


def is_social_media_source(source_url: str) -> bool:
    """
    Check if the source URL is from a social media platform.

    Args:
        source_url: The URL to check

    Returns:
        True if from social media, False otherwise
    """
    try:
        parsed = urlparse(source_url)
        domain = parsed.netloc.lower()

        # Remove 'www.' prefix
        if domain.startswith('www.'):
            domain = domain[4:]

        # Check against excluded domains
        if domain in EXCLUDED_SOCIAL_DOMAINS:
            return True

        # Check for Mastodon instances (contain 'mastodon' in domain)
        if 'mastodon' in domain:
            return True

        # Check for Bluesky posts (bsky.app)
        if 'bsky.app' in domain:
            return True

        return False
    except Exception as e:
        logger.warning(f"Error parsing URL {source_url}: {e}")
        return False


def fetch_webmentions(domain: str, token: str, since: str = None) -> List[Dict]:
    """
    Fetch webmentions from webmention.io API.

    Args:
        domain: The target domain to fetch mentions for
        token: webmention.io API token
        since: Optional ISO timestamp to fetch mentions since

    Returns:
        List of webmention objects
    """
    params = {
        'target': f'https://{domain}/',
        'token': token,
        'per-page': 100  # Max allowed by webmention.io
    }

    if since:
        params['since'] = since

    try:
        import requests
        response = requests.get(WEBMENTION_IO_API, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        mentions = data.get('children', [])

        logger.info(f"Fetched {len(mentions)} total mentions from webmention.io")
        return mentions

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch webmentions: {e}")
        raise BotException(f"Webmention fetch failed: {e}")


def filter_blog_mentions(mentions: List[Dict]) -> List[Dict]:
    """
    Filter mentions to include only blog posts (exclude social media).

    Args:
        mentions: List of webmention objects

    Returns:
        Filtered list containing only blog mentions
    """
    blog_mentions = []
    excluded_count = 0

    for mention in mentions:
        # Get source URL
        source_url = mention.get('url', '')

        if not source_url:
            logger.debug("Skipping mention without source URL")
            continue

        # Check if it's from social media
        if is_social_media_source(source_url):
            excluded_count += 1
            logger.debug(f"Excluding social media mention from: {source_url}")
            continue

        # This is a blog mention, keep it
        blog_mentions.append(mention)

    logger.info(f"Filtered to {len(blog_mentions)} blog mentions (excluded {excluded_count} social media)")
    return blog_mentions


def load_existing_webmentions() -> Dict:
    """
    Load existing webmentions from file.

    Returns:
        Dictionary of existing webmentions by target URL
    """
    if not WEBMENTIONS_FILE.exists():
        logger.info("No existing webmentions file found, starting fresh")
        return {}

    try:
        with FileLock(WEBMENTIONS_FILE):
            with open(WEBMENTIONS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Loaded existing webmentions for {len(data)} target URLs")
                return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse existing webmentions: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error loading webmentions: {e}")
        return {}


def save_webmentions(webmentions: Dict) -> None:
    """
    Save webmentions to file with file locking.

    Args:
        webmentions: Dictionary of webmentions to save
    """
    try:
        # Ensure parent directory exists
        WEBMENTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)

        with FileLock(WEBMENTIONS_FILE):
            with open(WEBMENTIONS_FILE, 'w', encoding='utf-8') as f:
                json.dump(webmentions, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved webmentions to {WEBMENTIONS_FILE}")
    except Exception as e:
        logger.error(f"Failed to save webmentions: {e}")
        raise BotException(f"Failed to save webmentions: {e}")


def process_mentions(mentions: List[Dict], existing_webmentions: Dict) -> Dict:
    """
    Process new mentions and merge with existing data.

    Args:
        mentions: List of new mentions from API
        existing_webmentions: Existing webmentions data

    Returns:
        Updated webmentions dictionary
    """
    new_count = 0
    updated_count = 0

    for mention in mentions:
        # Extract relevant fields
        source_url = mention.get('url', '')
        target_url = mention.get('wm-target', '')
        mention_type = mention.get('wm-property', 'mention')
        published = mention.get('published', mention.get('wm-received', ''))

        # Author information
        author = mention.get('author', {})
        author_name = author.get('name', 'Unknown')
        author_url = author.get('url', '')

        # Content
        content_obj = mention.get('content', {})
        if isinstance(content_obj, dict):
            content = content_obj.get('text', content_obj.get('html', ''))
        else:
            content = str(content_obj) if content_obj else ''

        # Summary/title
        summary = mention.get('summary', mention.get('name', ''))

        if not source_url or not target_url:
            logger.warning("Skipping mention with missing source or target URL")
            continue

        # Initialize target URL in data if not exists
        if target_url not in existing_webmentions:
            existing_webmentions[target_url] = {
                'target': target_url,
                'mentions': []
            }

        # Check if this mention already exists (by source URL)
        existing_sources = {m.get('source') for m in existing_webmentions[target_url]['mentions']}

        if source_url not in existing_sources:
            # New mention
            existing_webmentions[target_url]['mentions'].append({
                'source': source_url,
                'type': mention_type,
                'published': published,
                'author': {
                    'name': author_name,
                    'url': author_url
                },
                'title': summary,
                'content': content[:500] if content else '',  # Truncate long content
                'fetched_at': datetime.now().isoformat()
            })
            new_count += 1
            logger.info(f"New webmention: {source_url} -> {target_url}")
        else:
            # Update existing mention if needed
            updated_count += 1
            logger.debug(f"Mention already exists: {source_url}")

    logger.info(f"Processed {new_count} new mentions, {updated_count} already existed")
    return existing_webmentions


def get_last_fetch_time(existing_webmentions: Dict) -> str:
    """
    Get the timestamp of the last fetch to use as 'since' parameter.

    Args:
        existing_webmentions: Existing webmentions data

    Returns:
        ISO timestamp string or None
    """
    timestamps = []

    for target_data in existing_webmentions.values():
        for mention in target_data.get('mentions', []):
            fetched_at = mention.get('fetched_at')
            if fetched_at:
                timestamps.append(fetched_at)

    if timestamps:
        # Return the most recent timestamp
        latest = max(timestamps)
        logger.info(f"Last fetch time: {latest}")
        return latest

    return None


def main():
    """Main entry point for webmentions fetcher."""
    logger.info("=" * 60)
    logger.info("Starting webmentions fetch")
    logger.info("=" * 60)

    # Get configuration
    config = load_config()

    # Get secrets from environment
    token = os.environ.get('WEBMENTION_IO_TOKEN')
    domain = os.environ.get('BEARBLOG_DOMAIN')

    if not token:
        logger.error("WEBMENTION_IO_TOKEN environment variable not set")
        sys.exit(1)

    if not domain:
        logger.error("BEARBLOG_DOMAIN environment variable not set")
        sys.exit(1)

    logger.info(f"Fetching webmentions for domain: {domain}")

    try:
        # Load existing data
        existing_webmentions = load_existing_webmentions()

        # Get last fetch time for incremental updates
        since = get_last_fetch_time(existing_webmentions)

        # Fetch new mentions
        all_mentions = fetch_webmentions(domain, token, since=since)

        if not all_mentions:
            logger.info("No new mentions found")
            return

        # Filter to blog-only mentions (exclude social media)
        blog_mentions = filter_blog_mentions(all_mentions)

        if not blog_mentions:
            logger.info("No new blog mentions after filtering")
            return

        # Process and merge with existing data
        updated_webmentions = process_mentions(blog_mentions, existing_webmentions)

        # Save to file
        save_webmentions(updated_webmentions)

        logger.info("=" * 60)
        logger.info("Webmentions fetch completed successfully")
        logger.info("=" * 60)

    except BotException as e:
        logger.error(f"Bot error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
