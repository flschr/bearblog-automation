"""
RSS-based blog backup automation with GitHub integration.
"""

import hashlib
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urlparse

import feedparser

# Import shared utilities
import sys

# Ensure the repository-level `bots/shared.py` module is importable when this
# script is executed directly from the workflow runner.
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'bots'))
from shared import (  # noqa: E402
    CONFIG,
    DownloadError,
    REQUEST_TIMEOUT,
    MAX_IMAGE_SIZE,
    MAX_WORKERS,
    is_safe_url,
    sanitize_filename,
    clean_filename,
    create_session,
    FileLock,
)

from concurrent.futures import ThreadPoolExecutor, as_completed

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- CONFIG ---
BACKUP_FOLDER = CONFIG.get('backup', {}).get('folder', 'blog-backup')
SITE_URL = CONFIG.get('blog', {}).get('site_url', '').rstrip('/')
FEED_URL = CONFIG.get('backup', {}).get('feed_url') or f"{SITE_URL}/feed/"

# Linked files configuration
LINKED_FILES_CONFIG = CONFIG.get('backup', {}).get('linked_files', {})
LINKED_FILES_ENABLED = LINKED_FILES_CONFIG.get('enabled', False)
LINKED_FILES_EXTENSIONS = [ext.lower() for ext in LINKED_FILES_CONFIG.get('allowed_extensions', [])]
LINKED_FILES_DOMAINS = [d.lower() for d in LINKED_FILES_CONFIG.get('allowed_domains', [])]

# Paths
BASE_DIR = Path(BACKUP_FOLDER)
TRACKING_FILE = Path("archive/bots/backup_bot/processed_articles.txt")
LOCK_FILE = Path("archive/bots/backup_bot/processed_articles.txt.lock")

# Create session with connection pooling
session = create_session('bearblog-backup-rss/3.0')


def submit_to_web_archive(url: str) -> None:
    """Submit the URL to the Internet Archive (web.archive.org)."""
    if not CONFIG.get('web_archive', {}).get('enabled', False):
        return

    try:
        response = session.post(
            "https://web.archive.org/save",
            data={"url": url},
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True
        )
        response.raise_for_status()
        logger.info(f"Web Archive submission success for {url}")
    except Exception as e:
        logger.warning(f"Web Archive submission failed for {url}: {e}")


def get_entry_content(entry) -> str:
    """Extract content from RSS entry, preferring full content fields."""
    if getattr(entry, 'content', None):
        content_list = entry.get('content', [])
        if content_list and isinstance(content_list, list):
            value = content_list[0].get('value')
            if value:
                return str(value)

    return str(entry.get('summary', '') or '')


def get_content_hash(entry) -> str:
    """Create a stable hash from entry content and metadata."""
    content = get_entry_content(entry)
    hash_parts = [
        str(entry.get('id', '')),
        str(entry.get('link', '')),
        str(entry.get('title', '')),
        str(entry.get('published', '')),
        content,
    ]
    return hashlib.sha256('|'.join(hash_parts).encode('utf-8')).hexdigest()


def load_processed_articles() -> Dict[str, str]:
    """Load processed article hashes."""
    processed = {}
    if not TRACKING_FILE.exists():
        return processed

    try:
        with FileLock(LOCK_FILE):
            with open(TRACKING_FILE, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or '|' not in line:
                        if line:
                            logger.warning(f"Invalid format in tracking file at line {line_num}")
                        continue
                    article_id, content_hash = line.split('|', 1)
                    processed[article_id] = content_hash
    except Exception as e:
        logger.error(f"Error loading processed articles: {e}")
        return {}

    return processed


def save_processed_articles(processed_articles: Dict[str, str]) -> None:
    """Persist processed articles to disk in one pass with file locking."""
    TRACKING_FILE.parent.mkdir(parents=True, exist_ok=True)
    with FileLock(LOCK_FILE):
        with open(TRACKING_FILE, 'w', encoding='utf-8') as f:
            for article_id, hash_val in processed_articles.items():
                f.write(f"{article_id}|{hash_val}\n")


def safe_yaml_string(value: str) -> str:
    """Safely escape a string for YAML frontmatter."""
    if not value:
        return '""'

    value = str(value).strip()
    needs_quoting = any(c in value for c in [':', '#', '[', ']', '{', '}', '\n', '"', "'"])

    if '\n' in value:
        lines = value.split('\n')
        return '|\n  ' + '\n  '.join(lines)
    if needs_quoting or value.lower() in ('true', 'false', 'null', 'yes', 'no'):
        value = value.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{value}"'
    return value


def strip_code_blocks(content: str) -> str:
    """Remove fenced code blocks from content before extracting URLs."""
    content = re.sub(r'```[\s\S]*?```', '', content)
    content = re.sub(r'~~~[\s\S]*?~~~', '', content)
    return content


def is_allowed_linked_file(url: str) -> bool:
    """Check if a URL points to an allowed linked file."""
    if not LINKED_FILES_ENABLED:
        return False

    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    path = parsed.path.lower()

    domain_allowed = any(allowed in domain for allowed in LINKED_FILES_DOMAINS)
    if not domain_allowed:
        return False

    extension = path.rsplit('.', 1)[-1] if '.' in path else ''
    return extension in LINKED_FILES_EXTENSIONS


def download_file_to_folder(url: str, folder: Path) -> bool:
    """Download a file to a specific folder."""
    try:
        if not is_safe_url(url):
            logger.warning(f"Skipping unsafe URL: {url}")
            return False

        url_path = urlparse(url).path
        file_name = url_path.split('/')[-1].split('?')[0] or 'file.bin'
        file_name = sanitize_filename(file_name)
        path = folder / file_name

        response = session.get(url, stream=True, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        content_length = int(response.headers.get('content-length', 0))
        if content_length > MAX_IMAGE_SIZE:
            logger.warning(f"File too large ({content_length} bytes): {url}")
            return False

        total_size = 0
        with open(path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                total_size += len(chunk)
                if total_size > MAX_IMAGE_SIZE:
                    logger.warning(f"File download exceeded size limit: {url}")
                    path.unlink(missing_ok=True)
                    return False
                f.write(chunk)

        logger.info(f"Downloaded: {file_name}")
        return True
    except Exception as e:
        logger.warning(f"Error downloading {url}: {e}")
        return False


def download_linked_files(content: str, post_dir: Path) -> None:
    """Download allowed linked files (PDFs, documents, etc.)."""
    if not LINKED_FILES_ENABLED:
        return

    clean_content = strip_code_blocks(content)
    linked_urls = set()

    markdown_links = re.findall(r'\[.*?\]\((https?://[^\)]+)\)', clean_content)
    linked_urls.update(markdown_links)

    html_links = re.findall(r'<a[^>]+href=["\']([^"\']+)["\']', clean_content, re.IGNORECASE)
    linked_urls.update(html_links)

    for url in linked_urls:
        if not is_allowed_linked_file(url):
            continue
        url_path = urlparse(url).path
        file_name = url_path.split('/')[-1].split('?')[0]
        if not file_name:
            continue
        if (post_dir / sanitize_filename(file_name)).exists():
            continue
        download_file_to_folder(url, post_dir)


def download_images_concurrent(content: str, post_dir: Path) -> None:
    """Download all images from content concurrently."""
    clean_content = strip_code_blocks(content)
    img_urls = set()

    markdown_imgs = re.findall(r'!\[.*?\]\((https?://[^\)]+)\)', clean_content)
    img_urls.update(markdown_imgs)

    html_imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', clean_content, re.IGNORECASE)
    img_urls.update(html_imgs)

    if not img_urls:
        return

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(download_file_to_folder, url, post_dir): url for url in img_urls}
        for future in as_completed(futures):
            url = futures[future]
            try:
                future.result()
            except Exception as e:
                logger.warning(f"Concurrent image download failed for {url}: {e}")


def article_id(entry) -> str:
    """Build a stable ID for tracking."""
    return str(entry.get('id') or entry.get('link') or entry.get('title') or '')


def entry_date(entry) -> str:
    """Return YYYY-MM-DD based on published/updated date if available."""
    parsed = entry.get('published_parsed') or entry.get('updated_parsed')
    if parsed:
        try:
            return datetime(*parsed[:6]).strftime('%Y-%m-%d')
        except Exception:
            pass

    date_text = str(entry.get('published') or entry.get('updated') or '')
    if date_text:
        try:
            return datetime.fromisoformat(date_text.replace('Z', '+00:00')).strftime('%Y-%m-%d')
        except Exception:
            pass

    return datetime.utcnow().strftime('%Y-%m-%d')


def entry_slug(entry) -> str:
    """Extract slug from article link, fallback to title."""
    link = str(entry.get('link', '')).strip()
    if link:
        try:
            path = urlparse(link).path.strip('/')
            if path:
                return clean_filename(path.split('/')[-1])
        except Exception:
            pass

    return clean_filename(str(entry.get('title', 'untitled')))


def fetch_feed_entries() -> list:
    """Fetch and parse RSS feed entries."""
    logger.info(f"Fetching RSS feed: {FEED_URL}")
    response = session.get(FEED_URL, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()

    feed = feedparser.parse(response.content)
    if feed.bozo and not feed.entries:
        raise DownloadError(f"Invalid RSS feed at {FEED_URL}: {feed.bozo_exception}")

    logger.info(f"RSS entries found: {len(feed.entries)}")
    return list(feed.entries)


def process_entry(entry, processed_articles: Dict[str, str]) -> str:
    """Process a single RSS entry."""
    entry_id = article_id(entry)
    if not entry_id:
        logger.warning("Skipping entry without stable ID")
        return 'skipped'

    content = get_entry_content(entry)
    content_hash = get_content_hash(entry)

    if processed_articles.get(entry_id) == content_hash:
        return 'skipped'

    folder_name = f"{entry_date(entry)}-{entry_slug(entry)}"
    post_dir = BASE_DIR / folder_name
    already_exists = post_dir.exists()
    post_dir.mkdir(parents=True, exist_ok=True)

    download_images_concurrent(content, post_dir)
    download_linked_files(content, post_dir)

    title = str(entry.get('title', ''))
    link = str(entry.get('link', ''))
    published = str(entry.get('published', '') or entry.get('updated', ''))
    tags = [tag.get('term') for tag in entry.get('tags', []) if isinstance(tag, dict) and tag.get('term')]

    with open(post_dir / 'index.md', 'w', encoding='utf-8') as f:
        f.write('---\n')
        f.write(f"title: {safe_yaml_string(title)}\n")
        f.write(f"link: {safe_yaml_string(link)}\n")
        f.write(f"published: {safe_yaml_string(published)}\n")
        f.write(f"rss_id: {safe_yaml_string(entry_id)}\n")
        f.write(f"source: rss\n")
        if tags:
            f.write('tags:\n')
            for tag in tags:
                f.write(f"  - {safe_yaml_string(str(tag))}\n")
        f.write('---\n\n')
        f.write(content)

    processed_articles[entry_id] = content_hash

    if link:
        submit_to_web_archive(link)

    return 'updated' if already_exists else 'new'


def main() -> None:
    """Main execution logic."""
    logger.info('=' * 70)
    logger.info('RSS Backup to GitHub - Starting')
    logger.info('=' * 70)

    BASE_DIR.mkdir(parents=True, exist_ok=True)
    processed_articles = load_processed_articles()
    logger.info(f"Already processed: {len(processed_articles)} entries")

    stats = {'new_or_updated': 0, 'skipped': 0, 'error': 0}

    entries = fetch_feed_entries()
    for entry in entries:
        try:
            status = process_entry(entry, processed_articles)
            if status == 'skipped':
                stats['skipped'] += 1
            else:
                stats['new_or_updated'] += 1
        except Exception as e:
            stats['error'] += 1
            logger.error(f"Error processing entry: {e}")

    save_processed_articles(processed_articles)

    logger.info('=' * 70)
    logger.info('Backup Complete!')
    logger.info(f"  New/Updated entries: {stats['new_or_updated']}")
    logger.info(f"  Skipped: {stats['skipped']}")
    logger.info(f"  Errors: {stats['error']}")
    logger.info('=' * 70)


if __name__ == '__main__':
    main()
