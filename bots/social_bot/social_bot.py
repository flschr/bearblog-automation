"""
Social media bot for automating posts from RSS feeds to Bluesky and Mastodon.
"""

import feedparser
import hashlib
import json
import os
import re
import logging
import tempfile
import time
from datetime import datetime, timezone
from typing import Optional, Dict, List, Set, Any
from pathlib import Path
from bs4 import BeautifulSoup
from atproto import Client, client_utils, models
from mastodon import Mastodon

# Import shared utilities
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared import (
    CONFIG,
    AuthenticationError,
    ConfigurationError,
    REQUEST_TIMEOUT,
    MAX_IMAGE_SIZE,
    is_safe_url,
    create_session,
    FileLock,
)

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- CONFIG ---
MASTODON_INSTANCE = CONFIG['social']['mastodon_instance']

# --- CONSTANTS ---
PLATFORM_BLUESKY = "bluesky"
PLATFORM_MASTODON = "mastodon"

BASE_DIR = Path(__file__).parent.absolute()
REPO_ROOT = Path(__file__).parent.parent.parent.absolute()
POSTED_FILE = BASE_DIR / 'posted_articles.txt'
LOCK_FILE = BASE_DIR / 'posted_articles.txt.lock'
CONFIG_FILE = BASE_DIR / 'config.json'
FEED_CACHE_FILE = BASE_DIR / 'feed_cache.json'
MAPPINGS_FILE = REPO_ROOT / 'mappings.json'
MAPPINGS_LOCK = REPO_ROOT / 'mappings.json.lock'
RETRY_QUEUE_FILE = BASE_DIR / 'retry_queue.json'
RETRY_QUEUE_LOCK = BASE_DIR / 'retry_queue.json.lock'

# Create session with connection pooling
session = create_session('feed2social/2.0')

# Import retry queue (after constants are defined)
from retry_queue import RetryQueue


def load_feed_cache() -> Dict[str, Dict[str, str]]:
    """
    Load feed cache containing ETag and Last-Modified headers.
    Returns a dict mapping feed URLs to their cache headers.
    """
    if not FEED_CACHE_FILE.exists():
        return {}

    try:
        with open(FEED_CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Error loading feed cache: {e}")
        return {}


def save_feed_cache(cache: Dict[str, Dict[str, str]]) -> None:
    """Save feed cache to disk."""
    try:
        with open(FEED_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving feed cache: {e}")


def load_social_mappings() -> Dict[str, Dict[str, str]]:
    """
    Load article URL to social media post URL mappings.
    Returns a dict: {article_url: {"mastodon": toot_url, "bluesky": post_url}}
    """
    if not MAPPINGS_FILE.exists():
        return {}

    try:
        with FileLock(MAPPINGS_LOCK):
            with open(MAPPINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Error loading social mappings: {e}")
        return {}


def save_social_mapping(article_url: str, mastodon_url: Optional[str] = None,
                        bluesky_url: Optional[str] = None) -> None:
    """
    Save the mapping from an article URL to its social media post URLs.
    Merges with existing mappings. New entries are prepended to keep newest on top.
    """
    if not mastodon_url and not bluesky_url:
        return

    try:
        with FileLock(MAPPINGS_LOCK):
            # Load existing mappings
            mappings = {}
            if MAPPINGS_FILE.exists():
                try:
                    with open(MAPPINGS_FILE, 'r', encoding='utf-8') as f:
                        mappings = json.load(f)
                except Exception:
                    mappings = {}

            # Build the entry for this article
            entry = mappings.get(article_url, {})
            if mastodon_url:
                entry["mastodon"] = mastodon_url
            if bluesky_url:
                entry["bluesky"] = bluesky_url

            # Prepend new entry to keep newest URLs on top
            # Remove existing entry first (if any), then add at the beginning
            if article_url in mappings:
                del mappings[article_url]
            new_mappings = {article_url: entry}
            new_mappings.update(mappings)

            # Save updated mappings
            with open(MAPPINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(new_mappings, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved social mapping for: {article_url}")
    except Exception as e:
        logger.error(f"Error saving social mapping: {e}")


def check_feed_changed(feed_url: str, cache: Dict[str, Dict[str, str]]) -> tuple[bool, Dict[str, str]]:
    """
    Check if a feed has changed using HEAD request with ETag/Last-Modified.

    Returns:
        (has_changed, new_headers): Tuple of boolean and dict with new cache headers
    """
    try:
        response = session.head(feed_url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        response.raise_for_status()

        new_headers = {
            'etag': response.headers.get('ETag', ''),
            'last-modified': response.headers.get('Last-Modified', '')
        }

        if feed_url not in cache:
            logger.info(f"No cache for {feed_url}, will fetch")
            return True, new_headers

        cached_headers = cache[feed_url]

        if new_headers['etag'] and cached_headers.get('etag'):
            if new_headers['etag'] == cached_headers['etag']:
                logger.info(f"Feed unchanged (ETag match): {feed_url}")
                return False, new_headers

        if new_headers['last-modified'] and cached_headers.get('last-modified'):
            if new_headers['last-modified'] == cached_headers['last-modified']:
                logger.info(f"Feed unchanged (Last-Modified match): {feed_url}")
                return False, new_headers

        logger.info(f"Feed changed or no cache headers: {feed_url}")
        return True, new_headers

    except Exception as e:
        logger.warning(f"Error checking feed headers for {feed_url}: {e}")
        return True, {}


def load_posted_articles() -> Set[str]:
    """
    Load all posted article URLs into memory for fast lookup.
    Returns a set for O(1) lookup time.
    """
    if not POSTED_FILE.exists():
        return set()

    try:
        with FileLock(LOCK_FILE):
            with open(POSTED_FILE, 'r', encoding='utf-8') as f:
                return {line.strip() for line in f if line.strip()}
    except Exception as e:
        logger.error(f"Error loading posted articles: {e}")
        return set()


def is_posted(link: str, posted_cache: Set[str]) -> bool:
    """Check if the given URL is already recorded in the posted cache."""
    return link in posted_cache


def get_article_age_days(entry: Any) -> Optional[int]:
    """
    Calculate the age of an article in days based on its published date.
    Returns None if the published date cannot be determined.
    """
    if not hasattr(entry, 'published_parsed') or entry.published_parsed is None:
        return None

    try:
        published_dt = datetime.fromtimestamp(
            time.mktime(entry.published_parsed),
            tz=timezone.utc
        )
        now = datetime.now(timezone.utc)
        age = now - published_dt
        return age.days
    except Exception as e:
        logger.warning(f"Error calculating article age: {e}")
        return None


def is_article_too_old(entry: Any, max_age_days: int) -> tuple[bool, Optional[int]]:
    """
    Check if an article exceeds the maximum age limit.

    Args:
        entry: The feed entry to check
        max_age_days: Maximum allowed age in days (0 = no limit)

    Returns:
        (is_too_old, age_days): Tuple of boolean and the article's age in days
    """
    if max_age_days <= 0:
        return False, None

    age_days = get_article_age_days(entry)
    if age_days is None:
        # If we can't determine the age, allow the article
        return False, None

    return age_days > max_age_days, age_days


def mark_as_posted(link: str) -> None:
    """Add a URL to the posted.txt file (prepends to keep newest on top)."""
    try:
        with FileLock(LOCK_FILE):
            existing_lines = []
            if POSTED_FILE.exists():
                with open(POSTED_FILE, 'r', encoding='utf-8') as f:
                    existing_lines = f.readlines()

            with open(POSTED_FILE, 'w', encoding='utf-8') as f:
                f.write(link + '\n')
                f.writelines(existing_lines)

        logger.info(f"Marked as posted (prepended): {link}")
    except Exception as e:
        logger.error(f"Error marking as posted: {e}")
        raise


def get_html_content(entry: Any) -> str:
    """Extract text from HTML, remove images, and clean up redundant whitespace."""
    try:
        html = entry.content[0].value if hasattr(entry, 'content') else entry.get('summary', '')
        soup = BeautifulSoup(html, "html.parser")

        for img in soup.find_all('img'):
            img.decompose()

        text = soup.get_text(separator=' ')
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()
    except Exception as e:
        logger.warning(f"Error extracting HTML content: {e}")
        return ""


def get_first_image_data(entry: Any) -> Optional[Dict[str, str]]:
    """Extract the first image URL and its alt text from the post."""
    try:
        html = entry.content[0].value if hasattr(entry, 'content') else entry.get('summary', '')
        soup = BeautifulSoup(html, "html.parser")
        img = soup.find('img')

        if img and img.get('src'):
            img_url = img.get('src')

            if not is_safe_url(img_url):
                return None

            return {
                "url": img_url,
                "alt": img.get('alt', '')[:400]
            }
        return None
    except Exception as e:
        logger.warning(f"Error extracting image data: {e}")
        return None


def download_image(img_url: str) -> Optional[str]:
    """
    Download an image to a temporary file while respecting size limits.
    Returns the path to the temporary file, or None on failure.
    """
    try:
        if not is_safe_url(img_url):
            logger.warning(f"Rejected unsafe image URL: {img_url}")
            return None

        temp_file = tempfile.NamedTemporaryFile(
            mode='wb',
            suffix='.jpg',
            delete=False,
            dir=BASE_DIR
        )

        try:
            r = session.get(img_url, timeout=REQUEST_TIMEOUT, stream=True)
            r.raise_for_status()

            content_length = int(r.headers.get('content-length', 0))
            if content_length > MAX_IMAGE_SIZE:
                logger.warning(f"Image too large: {content_length} bytes")
                temp_file.close()
                os.unlink(temp_file.name)
                return None

            total_downloaded = 0
            for chunk in r.iter_content(chunk_size=8192):
                total_downloaded += len(chunk)
                if total_downloaded > MAX_IMAGE_SIZE:
                    logger.warning(f"Image download exceeded size limit")
                    temp_file.close()
                    os.unlink(temp_file.name)
                    return None
                temp_file.write(chunk)

            temp_file.close()
            return temp_file.name

        except Exception as e:
            temp_file.close()
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            raise

    except Exception as e:
        logger.warning(f"Error downloading image from {img_url}: {e}")
        return None


def get_og_metadata(url: str) -> Optional[Dict[str, Optional[str]]]:
    """Fetch Open Graph metadata (title, description, image) for a given link."""
    try:
        r = session.get(url, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, 'html.parser')

        title_tag = soup.find("meta", property="og:title")
        desc_tag = soup.find("meta", property="og:description")
        img_tag = soup.find("meta", property="og:image")

        return {
            "title": title_tag["content"] if title_tag else "Blog post",
            "description": desc_tag["content"] if desc_tag else "",
            "image_url": img_tag["content"] if img_tag else None
        }
    except Exception as e:
        logger.warning(f"Error fetching OG metadata from {url}: {e}")
        return None


def submit_to_indexnow(url: str) -> None:
    """Submit the URL to IndexNow for faster search engine indexing."""
    key = os.getenv('INDEXNOW_KEY')
    if not key:
        return

    payload = {
        "host": "fischr.org",
        "key": key,
        "urlList": [url]
    }

    try:
        response = session.post(
            "https://www.bing.com/indexnow",
            json=payload,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        logger.info(f"IndexNow success for {url}")
    except Exception as e:
        logger.warning(f"IndexNow request failed: {e}")


def submit_to_web_archive(url: str) -> None:
    """
    Submit the URL to the Internet Archive (web.archive.org) for archival.
    Creates a permanent snapshot of the content using the Save Page Now API.
    """
    # Check if web archive integration is enabled
    if not CONFIG.get('web_archive', {}).get('enabled', False):
        return

    try:
        # Internet Archive Save Page Now API endpoint
        # Using the simple GET method which doesn't require authentication
        archive_url = f"https://web.archive.org/save/{url}"

        response = session.get(
            archive_url,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True
        )
        response.raise_for_status()
        logger.info(f"Web Archive submission success for {url}")
    except Exception as e:
        logger.warning(f"Web Archive submission failed for {url}: {e}")


BLUESKY_MAX_LENGTH = 300  # Bluesky's limit in graphemes


def truncate_text_for_bluesky(text: str, max_length: int = BLUESKY_MAX_LENGTH) -> str:
    """
    Truncate text to fit Bluesky's character limit.
    Tries to break at word boundaries and adds ellipsis if truncated.
    """
    if len(text) <= max_length:
        return text

    # Reserve space for ellipsis
    truncated = text[:max_length - 1]

    # Try to break at last space to avoid cutting words
    last_space = truncated.rfind(' ')
    if last_space > max_length // 2:  # Only break at space if it's not too early
        truncated = truncated[:last_space]

    return truncated.rstrip() + '…'


def post_to_bluesky(text: str, img_path: Optional[str], alt_text: str, link: Optional[str] = None) -> Optional[str]:
    """
    Post rich text to Bluesky with link card preview.
    Returns the URL of the created post, or None on failure.
    """
    handle = os.getenv('BSKY_HANDLE')
    password = os.getenv('BSKY_PW')

    if not handle or not password:
        raise AuthenticationError("BSKY_HANDLE or BSKY_PW environment variables not set")

    try:
        client = Client()
        profile = client.login(handle, password)

        # Truncate text to fit Bluesky's 300 character limit
        text = truncate_text_for_bluesky(text)

        tb = client_utils.TextBuilder()

        words = text.split(' ')
        for i, word in enumerate(words):
            if word.startswith('#') and len(word) > 1:
                tag_name = word[1:].rstrip('.,!?')
                tb.tag(word, tag_name)
            elif word.startswith('http'):
                tb.link(word, word)
            else:
                tb.text(word)

            if i < len(words) - 1:
                tb.text(' ')

        embed = None

        # Prioritize direct image upload over link cards when img_path is provided
        if img_path and os.path.exists(img_path):
            try:
                with open(img_path, 'rb') as f:
                    upload = client.upload_blob(f.read())
                    embed = models.AppBskyEmbedImages.Main(
                        images=[models.AppBskyEmbedImages.Image(
                            alt=alt_text or "",
                            image=upload.blob
                        )]
                    )
                logger.info("Uploaded direct image to Bluesky")
            except Exception as e:
                logger.error(f"Error uploading image to Bluesky: {e}")

        # Only create link card if no direct image was uploaded
        if embed is None and link:
            try:
                og_data = get_og_metadata(link)
                if og_data:
                    thumb_blob = None
                    if og_data.get('image_url'):
                        og_img_path = download_image(og_data['image_url'])
                        if og_img_path and os.path.exists(og_img_path):
                            try:
                                # Bluesky limit for link card images is ~1MB
                                file_size = os.path.getsize(og_img_path)
                                if file_size > 950_000:  # ~950KB to stay safely under limit
                                    logger.warning(
                                        f"OG image too large for Bluesky ({file_size/1_000_000:.2f}MB), "
                                        f"creating link card without thumbnail"
                                    )
                                else:
                                    with open(og_img_path, 'rb') as f:
                                        thumb_blob = client.upload_blob(f.read()).blob
                            except Exception as e:
                                logger.warning(f"Error uploading OG image: {e}")
                            finally:
                                if og_img_path and os.path.exists(og_img_path):
                                    try:
                                        os.unlink(og_img_path)
                                    except Exception as e:
                                        logger.warning(f"Error removing OG image file: {e}")

                    embed = models.AppBskyEmbedExternal.Main(
                        external=models.AppBskyEmbedExternal.External(
                            title=og_data.get('title', 'Blog post')[:300],
                            description=og_data.get('description', '')[:1000],
                            uri=link,
                            thumb=thumb_blob
                        )
                    )
                    logger.info("Created external link card embed for Bluesky")
            except Exception as e:
                logger.warning(f"Error creating external embed: {e}")

        response = client.send_post(text=tb, embed=embed)

        # Construct the Bluesky post URL from the response
        # Format: https://bsky.app/profile/{handle}/post/{rkey}
        post_url = None
        if response and hasattr(response, 'uri'):
            # URI format: at://did:plc:xxx/app.bsky.feed.post/rkey
            uri_parts = response.uri.split('/')
            if len(uri_parts) >= 5:
                rkey = uri_parts[-1]
                post_url = f"https://bsky.app/profile/{handle}/post/{rkey}"

        logger.info(f"Bluesky post success: {post_url}")
        return post_url

    except Exception as e:
        logger.error(f"Error posting to Bluesky: {e}")
        raise


def post_to_mastodon(text: str, img_path: Optional[str], alt_text: str) -> Optional[str]:
    """
    Post plain text status with optional media to Mastodon.
    Returns the URL of the created toot, or None on failure.
    """
    token = os.getenv('MASTO_TOKEN')

    if not token:
        raise AuthenticationError("MASTO_TOKEN environment variable not set")

    try:
        mastodon = Mastodon(
            access_token=token,
            api_base_url=MASTODON_INSTANCE
        )

        media_ids = []
        if img_path and os.path.exists(img_path):
            try:
                media = mastodon.media_post(img_path, description=alt_text or "")
                media_ids.append(media['id'])
            except Exception as e:
                logger.error(f"Error uploading image to Mastodon: {e}")

        status = mastodon.status_post(
            status=text[:500],
            media_ids=media_ids if media_ids else None
        )

        toot_url = status.get('url') if status else None
        logger.info(f"Mastodon post success: {toot_url}")
        return toot_url

    except Exception as e:
        logger.error(f"Error posting to Mastodon: {e}")
        raise


def validate_config(config: List[Dict[str, Any]]) -> None:
    """Validate configuration structure and required fields."""
    required_fields = ['url', 'template', 'targets']

    for i, cfg in enumerate(config):
        for field in required_fields:
            if field not in cfg:
                raise ConfigurationError(
                    f"Config entry {i} missing required field: {field}"
                )

        if not isinstance(cfg['targets'], list):
            raise ConfigurationError(
                f"Config entry {i}: 'targets' must be a list"
            )

        valid_targets = {PLATFORM_BLUESKY, PLATFORM_MASTODON}
        for target in cfg['targets']:
            if target not in valid_targets:
                raise ConfigurationError(
                    f"Config entry {i}: invalid target '{target}'. "
                    f"Must be one of {valid_targets}"
                )


def validate_credentials(config: List[Dict[str, Any]]) -> None:
    """Validate that required credentials are present for configured platforms."""
    required_platforms = set()

    for cfg in config:
        required_platforms.update(cfg.get('targets', []))

    if PLATFORM_BLUESKY in required_platforms:
        if not os.getenv('BSKY_HANDLE') or not os.getenv('BSKY_PW'):
            raise AuthenticationError(
                "Bluesky credentials missing: BSKY_HANDLE and BSKY_PW required"
            )

    if PLATFORM_MASTODON in required_platforms:
        if not os.getenv('MASTO_TOKEN'):
            raise AuthenticationError(
                "Mastodon credentials missing: MASTO_TOKEN required"
            )


def get_entry_tags(entry: Any) -> str:
    """Extract tags/categories and hashtags from an entry for matching."""
    content_html = (
        entry.content[0].value if hasattr(entry, 'content')
        else entry.get('summary', '')
    )

    found_hashtags = " ".join(re.findall(r'#\w+', content_html))

    rss_categories = ""
    if hasattr(entry, 'tags'):
        rss_categories = " ".join([
            tag.term for tag in entry.tags if hasattr(tag, 'term')
        ])

    return (entry.title + " " + found_hashtags + " " + rss_categories).lower()


def entry_matches_config(entry: Any, cfg: Dict[str, Any], check_string: str) -> tuple[bool, str]:
    """
    Check if an entry matches a config's include/exclude rules.
    Returns (matches, reason) tuple.
    """
    # Check exclusions first
    for word in cfg.get('exclude', []):
        if word.lower() in check_string:
            return False, f"excluded by '{word}'"

    # Check inclusions (if specified)
    if cfg.get('include'):
        matching_include = None
        for word in cfg['include']:
            if word.lower() in check_string:
                matching_include = word
                break
        if not matching_include:
            return False, f"missing required tag from {cfg.get('include')}"

    return True, "matched"


def get_matching_report(
    entry: Any,
    check_string: str,
    config: List[Dict[str, Any]],
    feed_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate a detailed report explaining why an entry didn't match any config.
    """
    # Extract RSS categories as a list
    rss_tags = []
    if hasattr(entry, 'tags'):
        rss_tags = [tag.term for tag in entry.tags if hasattr(tag, 'term')]

    report = {
        "article": {
            "title": entry.title,
            "link": entry.link,
            "published": getattr(entry, 'published', 'unknown'),
        },
        "detected_tags": rss_tags,
        "check_string": check_string,
        "config_results": []
    }

    for cfg in config:
        config_name = cfg.get('name', cfg['url'])
        feed_url = cfg['url']

        # Check if entry is in this config's feed
        if feed_url not in feed_data:
            report["config_results"].append({
                "config": config_name,
                "result": "skipped",
                "reason": "feed was not fetched (unchanged)"
            })
            continue

        feed = feed_data[feed_url]
        entry_in_feed = any(
            hasattr(e, 'link') and e.link == entry.link
            for e in feed.entries
        )

        if not entry_in_feed:
            report["config_results"].append({
                "config": config_name,
                "result": "skipped",
                "reason": "article not in this feed"
            })
            continue

        matches, reason = entry_matches_config(entry, cfg, check_string)
        report["config_results"].append({
            "config": config_name,
            "include_filter": cfg.get('include', []),
            "exclude_filter": cfg.get('exclude', []),
            "result": "matched" if matches else "no match",
            "reason": reason
        })

    return report


UNMATCHED_REPORT_FILE = BASE_DIR / 'unmatched_articles.json'


def save_unmatched_report(reports: List[Dict[str, Any]]) -> None:
    """Save unmatched articles report to JSON file for GitHub Issue creation."""
    try:
        with open(UNMATCHED_REPORT_FILE, 'w', encoding='utf-8') as f:
            json.dump(reports, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved unmatched report to {UNMATCHED_REPORT_FILE}")
    except Exception as e:
        logger.error(f"Error saving unmatched report: {e}")


def post_entry(entry: Any, cfg: Dict[str, Any], posted_cache: Set[str]) -> bool:
    """
    Post a single feed entry using the given config with transaction-like semantics.

    This function uses locking and fresh re-checks to prevent race conditions
    and duplicate posts. If posting fails on some platforms, the article is
    added to the retry queue for automatic retry.

    Returns tuple: (any_success: bool, failure_info: Optional[Dict])
    """
    logger.info(f"Processing: {entry.title} (matched config: {cfg.get('name', 'unnamed')})")

    # Transaction variables
    transaction_id = f"{entry.link}:{os.getpid()}"
    lock_acquired = False
    img_path = None

    try:
        # PHASE 1: Acquire lock for this article
        # This prevents concurrent processes from posting the same article
        lock_key = hashlib.sha256(entry.link.encode("utf-8")).hexdigest()
        article_lock_path = LOCK_FILE.parent / f"{lock_key}.posting.lock"
        article_lock = FileLock(article_lock_path, timeout=60.0)

        logger.debug(f"[{transaction_id}] Acquiring posting lock...")
        article_lock.acquire()
        lock_acquired = True
        logger.debug(f"[{transaction_id}] Lock acquired")

        # PHASE 2: Fresh re-check - reload posted_articles.txt from disk
        # This catches articles posted by concurrent processes
        fresh_posted_cache = load_posted_articles()
        if entry.link in fresh_posted_cache:
            logger.info(
                f"[{transaction_id}] Article already posted by another process, skipping"
            )
            return False, None

        # PHASE 3: Prepare post content
        img_data = None
        alt_text = ""

        if cfg.get('include_images'):
            img_data = get_first_image_data(entry)
            if img_data:
                img_path = download_image(img_data['url'])
                alt_text = img_data.get('alt', '')

        clean_content = get_html_content(entry)
        msg = cfg['template'].format(
            title=entry.title,
            link=entry.link,
            content=clean_content
        )

        # PHASE 4: Post to all platforms
        bluesky_url = None
        mastodon_url = None
        any_success = False
        failed_platforms = []

        logger.info(f"[{transaction_id}] Posting to platforms: {cfg.get('targets', [])}")

        if PLATFORM_BLUESKY in cfg.get('targets', []):
            try:
                bluesky_url = post_to_bluesky(msg, img_path, alt_text, link=entry.link)
                if bluesky_url:
                    any_success = True
                    logger.info(f"[{transaction_id}] ✓ Bluesky success")
                else:
                    failed_platforms.append({"platform": "bluesky", "error": "Post returned None"})
            except Exception as e:
                error_msg = str(e)
                logger.error(f"[{transaction_id}] ✗ Bluesky failed: {error_msg}")
                failed_platforms.append({"platform": "bluesky", "error": error_msg})

        if PLATFORM_MASTODON in cfg.get('targets', []):
            try:
                mastodon_url = post_to_mastodon(msg, img_path, alt_text)
                if mastodon_url:
                    any_success = True
                    logger.info(f"[{transaction_id}] ✓ Mastodon success")
                else:
                    failed_platforms.append({"platform": "mastodon", "error": "Post returned None"})
            except Exception as e:
                error_msg = str(e)
                logger.error(f"[{transaction_id}] ✗ Mastodon failed: {error_msg}")
                failed_platforms.append({"platform": "mastodon", "error": error_msg})

        # PHASE 5: Handle results
        if not any_success:
            # Complete failure - don't mark as posted, don't add to retry queue
            logger.error(f"[{transaction_id}] All platforms failed, not marking as posted")
            return False, None

        # At least one platform succeeded
        successful_platforms = []
        if bluesky_url:
            successful_platforms.append("bluesky")
        if mastodon_url:
            successful_platforms.append("mastodon")

        # PHASE 6: Save results atomically
        try:
            # Save social mapping
            save_social_mapping(entry.link, mastodon_url=mastodon_url, bluesky_url=bluesky_url)

            # Submit to external services (best effort, don't fail if these fail)
            try:
                submit_to_indexnow(entry.link)
            except Exception as e:
                logger.warning(f"[{transaction_id}] IndexNow submission failed: {e}")

            try:
                submit_to_web_archive(entry.link)
            except Exception as e:
                logger.warning(f"[{transaction_id}] Web Archive submission failed: {e}")

            # Mark as posted (critical - must succeed)
            mark_as_posted(entry.link)
            posted_cache.add(entry.link)

            logger.info(f"[{transaction_id}] Article marked as posted")

        except Exception as e:
            logger.error(f"[{transaction_id}] Failed to save results: {e}")
            # This is serious - we posted but couldn't record it
            # Return success to avoid retry, but log error
            return True, None

        # PHASE 7: Handle partial failures
        if failed_platforms:
            logger.warning(
                f"[{transaction_id}] Partial failure - succeeded: {successful_platforms}, "
                f"failed: {[p['platform'] for p in failed_platforms]}"
            )

            return True, {
                "article": {"title": entry.title, "link": entry.link},
                "failed_platforms": failed_platforms,
                "successful_platforms": successful_platforms
            }

        # Complete success
        logger.info(f"[{transaction_id}] Complete success on all platforms")
        return True, None

    except Exception as e:
        logger.error(f"[{transaction_id}] Unexpected error in post_entry: {e}")
        return False, None

    finally:
        # CLEANUP: Always release lock and clean up resources
        if lock_acquired:
            try:
                article_lock.release()
                logger.debug(f"[{transaction_id}] Lock released")
            except Exception as e:
                logger.warning(f"[{transaction_id}] Error releasing lock: {e}")

        # Clean up temporary image file
        if img_path and os.path.exists(img_path):
            try:
                os.unlink(img_path)
            except Exception as e:
                logger.warning(f"[{transaction_id}] Error removing temporary file: {e}")


def run() -> None:
    """Main execution logic to parse feeds and post new entries based on configuration."""
    logger.info("=== Social Bot Start ===")

    try:
        if not CONFIG_FILE.exists():
            raise ConfigurationError(f"Config file not found: {CONFIG_FILE}")

        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)

        validate_config(config)
        validate_credentials(config)

        posted_cache = load_posted_articles()
        posted_file_count = len(posted_cache)
        social_mappings = load_social_mappings()
        if social_mappings:
            posted_cache.update(social_mappings.keys())
        logger.info(
            "Loaded %s previously posted articles (%s from posted file, %s from mappings)",
            len(posted_cache),
            posted_file_count,
            len(social_mappings)
        )

        # Load max article age setting (0 = no limit)
        max_article_age_days = CONFIG.get('social', {}).get('max_article_age_days', 0)
        if max_article_age_days > 0:
            logger.info(f"Article age limit: {max_article_age_days} days")

        feed_cache = load_feed_cache()
        cache_updated = False

        # Step 1: Collect all unique feed URLs and fetch each once
        unique_feed_urls = set(cfg['url'] for cfg in config)
        feed_data: Dict[str, Any] = {}  # URL -> parsed feed
        feeds_fetched = 0
        feeds_skipped = 0

        for feed_url in unique_feed_urls:
            try:
                has_changed, new_headers = check_feed_changed(feed_url, feed_cache)

                if not has_changed:
                    logger.info(f"Skipping unchanged feed: {feed_url}")
                    feeds_skipped += 1
                    continue

                logger.info(f"Fetching feed: {feed_url}")
                response = session.get(feed_url, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()

                feed = feedparser.parse(response.content)

                if feed.bozo:
                    logger.warning(f"Feed parsing warning for {feed_url}: {feed.bozo_exception}")

                feed_data[feed_url] = feed
                feeds_fetched += 1
                logger.info(f"Found {len(feed.entries)} entries in feed")

                # Store new headers for potential cache update after processing
                # We'll only update the cache after successfully posting all new entries
                # This prevents the bug where cache is updated but posting fails,
                # causing the feed to be skipped on subsequent runs
                if new_headers:
                    new_entries = [
                        e for e in feed.entries
                        if hasattr(e, 'link') and e.link not in posted_cache
                    ]
                    if new_entries:
                        # Store pending headers - will be applied after successful processing
                        feed_data[feed_url + '_pending_headers'] = new_headers
                        logger.info(f"Found {len(new_entries)} new entries (cache update pending)")
                    else:
                        # No new entries - safe to update cache immediately
                        feed_cache[feed_url] = new_headers
                        cache_updated = True
                        logger.info(
                            f"Cache updated: no new entries in feed"
                        )

            except Exception as e:
                logger.error(f"Error fetching feed {feed_url}: {e}")
                continue

        # Step 2: Collect all unique entries from fetched feeds
        all_entries: Dict[str, Any] = {}  # URL -> entry (deduplicated)
        for feed_url, feed in feed_data.items():
            # Skip pending headers entries (they are dicts, not feed objects)
            if feed_url.endswith('_pending_headers'):
                continue
            for entry in feed.entries:
                if hasattr(entry, 'link') and entry.link:
                    if entry.link not in all_entries:
                        all_entries[entry.link] = entry

        logger.info(f"Collected {len(all_entries)} unique entries from {feeds_fetched} feeds")

        # Step 3: Process each entry against all configs
        total_processed = 0
        unmatched_entries = []
        partial_failures = []  # Track articles that failed on some platforms

        for entry_url, entry in all_entries.items():
            # Skip already posted
            if is_posted(entry_url, posted_cache):
                continue

            # Skip articles that are too old (prevents re-posting when URLs change)
            if max_article_age_days > 0:
                is_too_old, age_days = is_article_too_old(entry, max_article_age_days)
                if is_too_old:
                    logger.info(
                        f"Skipping old article ({age_days} days old, max {max_article_age_days}): "
                        f"{entry.title}"
                    )
                    continue

            # Get tags once for this entry
            check_string = get_entry_tags(entry)

            # Try to find a matching config
            matched_config = None
            for cfg in config:
                # Only consider configs that use a feed containing this entry
                if cfg['url'] in feed_data:
                    feed = feed_data[cfg['url']]
                    entry_in_feed = any(
                        hasattr(e, 'link') and e.link == entry_url
                        for e in feed.entries
                    )
                    if entry_in_feed:
                        matches, _ = entry_matches_config(entry, cfg, check_string)
                        if matches:
                            matched_config = cfg
                            break

            if matched_config:
                success, failure_info = post_entry(entry, matched_config, posted_cache)
                if success:
                    total_processed += 1
                if failure_info:
                    partial_failures.append(failure_info)
            else:
                # No matching config found - generate detailed report
                report = get_matching_report(entry, check_string, config, feed_data)
                unmatched_entries.append(report)

        # Step 4: Handle unmatched entries
        if unmatched_entries:
            # Save detailed report for GitHub Issue
            save_unmatched_report(unmatched_entries)

            # Log warnings with GitHub Actions annotation format
            for report in unmatched_entries:
                article = report["article"]
                tags = report["detected_tags"]
                print(f"::warning::No matching config for: {article['title']} ({article['link']}) - Tags: {tags}")
                logger.warning(f"No matching config for: {article['title']} ({article['link']})")

        # Step 4b: Handle partial failures (posted to some platforms but not all)
        if partial_failures:
            # Initialize retry queue with config
            retry_queue = RetryQueue(RETRY_QUEUE_FILE, RETRY_QUEUE_LOCK, CONFIG)

            # Add each partial failure to retry queue
            for failure in partial_failures:
                article = failure["article"]
                failed_platforms = failure["failed_platforms"]
                succeeded_platforms = failure["successful_platforms"]

                try:
                    retry_queue.add_to_queue(
                        article_url=article["link"],
                        article_title=article["title"],
                        failed_platforms=failed_platforms,
                        successful_platforms=succeeded_platforms
                    )
                    logger.info(
                        f"Added to retry queue: {article['title']} - "
                        f"will retry {[p['platform'] for p in failed_platforms]}"
                    )
                except Exception as e:
                    logger.error(f"Failed to add {article['title']} to retry queue: {e}")

                # Log warnings with GitHub Actions annotation format
                failed = [p["platform"] for p in failed_platforms]
                succeeded = succeeded_platforms
                print(f"::warning::Partial failure for: {article['title']} - Failed: {failed}, Succeeded: {succeeded}")
                logger.warning(f"Partial failure for: {article['title']} ({article['link']}) - Failed: {failed}")

            # Also save report for immediate GitHub Issue (legacy behavior)
            partial_failures_file = BASE_DIR / 'partial_failures.json'
            try:
                with open(partial_failures_file, 'w', encoding='utf-8') as f:
                    json.dump(partial_failures, f, indent=2, ensure_ascii=False)
                logger.info(f"Saved partial failures report to {partial_failures_file}")
            except Exception as e:
                logger.error(f"Error saving partial failures report: {e}")

        # Step 5: Update cache for feeds where all new entries were successfully processed
        # Only update cache if no unposted entries remain (prevents skipping failed posts)
        for feed_url in list(feed_data.keys()):
            pending_key = feed_url + '_pending_headers'
            if pending_key in feed_data:
                pending_headers = feed_data[pending_key]
                feed = feed_data.get(feed_url)
                if feed:
                    # Check if any entries from this feed are still unposted
                    unposted_entries = [
                        e for e in feed.entries
                        if hasattr(e, 'link') and e.link not in posted_cache
                    ]
                    # Filter out entries that are too old (they won't be posted anyway)
                    if max_article_age_days > 0:
                        unposted_entries = [
                            e for e in unposted_entries
                            if not is_article_too_old(e, max_article_age_days)[0]
                        ]

                    if not unposted_entries:
                        # All entries processed - safe to update cache
                        feed_cache[feed_url] = pending_headers
                        cache_updated = True
                        logger.info(f"Cache updated for {feed_url}: all entries processed")
                    else:
                        # Some entries still unposted - don't update cache
                        # This ensures the feed will be re-fetched on the next run
                        logger.warning(
                            f"Cache NOT updated for {feed_url}: "
                            f"{len(unposted_entries)} entries still unposted"
                        )

        if cache_updated:
            save_feed_cache(feed_cache)
            logger.info("Feed cache saved")

        logger.info(
            f"=== Social Bot End === "
            f"(Fetched {feeds_fetched} feeds, skipped {feeds_skipped} unchanged, "
            f"processed {total_processed}/{len(all_entries)} entries, "
            f"{len(unmatched_entries)} unmatched)"
        )

    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        raise
    except AuthenticationError as e:
        logger.error(f"Authentication error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in main execution: {e}")
        raise


if __name__ == "__main__":
    run()
