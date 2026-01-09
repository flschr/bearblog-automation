"""
Broken link checker for Bear Blog backups.
"""

import json
import logging
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import urlparse

import requests
import yaml

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared import CONFIG, create_session, is_safe_url, MAX_WORKERS


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


LINK_CHECKER_CONFIG = CONFIG.get('link_checker', {})
LINK_CHECKER_ENABLED = LINK_CHECKER_CONFIG.get('enabled', True)
LINK_TIMEOUT = LINK_CHECKER_CONFIG.get('timeout_seconds', 10)
MAX_LINK_WORKERS = LINK_CHECKER_CONFIG.get('max_workers', MAX_WORKERS)
RATE_LIMIT_DELAY = LINK_CHECKER_CONFIG.get('rate_limit_delay', 0.0)
USER_AGENT = LINK_CHECKER_CONFIG.get('user_agent', 'bearblog-link-checker/1.0')

# Load excluded domains from excluded_domains.txt
EXCLUDED_DOMAINS: Set[str] = set()
EXCLUDED_DOMAINS_FILE = Path(__file__).parent / 'excluded_domains.txt'
if EXCLUDED_DOMAINS_FILE.exists():
    with open(EXCLUDED_DOMAINS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if line and not line.startswith('#'):
                EXCLUDED_DOMAINS.add(line)

# Rate limiting tracking
_rate_limit_lock = threading.Lock()
_last_request_time = 0.0

# Auto-exclusion tracking
_auto_excluded_lock = threading.Lock()
_auto_excluded_domains: Set[str] = set()
AUTO_EXCLUDED_LOG = Path(__file__).parent / 'auto_excluded_domains.json'

BLOG_CONFIG = CONFIG.get('blog', {})
BLOG_SITE_URL = BLOG_CONFIG.get('site_url', '').strip()
BACKUP_FOLDER = CONFIG.get('backup', {}).get('folder', 'blog-backup')

REPORT_FILE = Path(__file__).parent / 'broken_links.json'

# Match markdown links with angle brackets: [text](<url>) - these can contain any characters
MARKDOWN_LINK_ANGLE_RE = re.compile(r'!?\[[^\]]*]\(<([^>]+)>\)')
# Match regular markdown links with URLs (handles balanced parentheses in URL)
# Matches: [text](https://example.com/page_(info)) or [text](https://foo.com/a_(b)_(c))
MARKDOWN_LINK_RE = re.compile(r'!?\[[^\]]*]\((https?://(?:[^\s()]|\([^)]*\))+)\)')
AUTOLINK_RE = re.compile(r'<(https?://[^>]+)>')
BARE_URL_RE = re.compile(r'(https?://[^\s<>\[\]{}"\'`]+)')
FENCED_CODE_RE = re.compile(r'```.*?```', re.DOTALL)
IFRAME_RE = re.compile(r'<iframe[^>]*>.*?</iframe>', re.DOTALL | re.IGNORECASE)

TRAILING_PUNCTUATION = '.,:;!?*'


@dataclass(frozen=True)
class LinkIssue:
    article_url: str
    link_url: str
    status: str
    file_path: str


def strip_frontmatter(text: str) -> Tuple[Dict, str]:
    if text.startswith('---'):
        parts = text.split('---', 2)
        if len(parts) >= 3:
            frontmatter = yaml.safe_load(parts[1]) or {}
            return frontmatter, parts[2]
    return {}, text


def get_domain_from_url(url: str) -> Optional[str]:
    """Extract the base domain from a URL."""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return None

        # Return the domain without 'www.' prefix for consistency
        hostname_lower = hostname.lower()
        if hostname_lower.startswith('www.'):
            return hostname_lower[4:]
        return hostname_lower
    except Exception:
        return None


def is_excluded_domain(url: str) -> bool:
    """Check if URL is from an excluded domain."""
    if not EXCLUDED_DOMAINS:
        return False

    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return False

        # Check exact match and also check if it's a subdomain
        hostname_lower = hostname.lower()
        for excluded in EXCLUDED_DOMAINS:
            excluded_lower = excluded.lower()
            if hostname_lower == excluded_lower:
                return True
            # Also check if hostname ends with .excluded (subdomain)
            if hostname_lower.endswith('.' + excluded_lower):
                return True

        return False
    except Exception:
        return False


def add_domain_to_excluded(url: str, reason: str) -> None:
    """
    Add a domain to the excluded_domains.txt file and track it in auto_excluded_domains.json.
    Thread-safe implementation.

    Args:
        url: The URL that triggered the exclusion
        reason: The reason for exclusion (e.g., 'http_403', 'http_429')
    """
    domain = get_domain_from_url(url)
    if not domain:
        return

    with _auto_excluded_lock:
        # Check if we've already auto-excluded this domain in this run
        if domain in _auto_excluded_domains:
            return

        # Check if domain is already in excluded_domains.txt
        if is_excluded_domain(url):
            return

        # Add to in-memory tracking
        _auto_excluded_domains.add(domain)

        # Append to excluded_domains.txt
        try:
            with open(EXCLUDED_DOMAINS_FILE, 'a', encoding='utf-8') as f:
                f.write(f'\n# Auto-excluded due to {reason}\n{domain}\n')
            logger.info(f"Auto-excluded domain: {domain} (reason: {reason})")
        except Exception as e:
            logger.error(f"Failed to add {domain} to excluded_domains.txt: {e}")
            return

        # Add to excluded domains set for current run
        EXCLUDED_DOMAINS.add(domain)

        # Track in JSON log for issue reporting
        log_data = []
        if AUTO_EXCLUDED_LOG.exists():
            try:
                with open(AUTO_EXCLUDED_LOG, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
            except Exception:
                log_data = []

        # Add new entry
        from datetime import datetime
        log_data.append({
            'domain': domain,
            'url': url,
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })

        # Save updated log
        try:
            with open(AUTO_EXCLUDED_LOG, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to update auto-exclusion log: {e}")


def normalize_url(url: str) -> str:
    url = url.strip().strip('<>').strip()

    # Strip standard trailing punctuation
    url = url.rstrip(TRAILING_PUNCTUATION)

    # Handle closing parentheses smartly:
    # Only strip ) if there's no opening ( in the URL (unbalanced)
    while url.endswith(')'):
        if '(' in url:
            # Check if parentheses are balanced
            open_count = url.count('(')
            close_count = url.count(')')
            if open_count >= close_count:
                break
        url = url[:-1].rstrip(TRAILING_PUNCTUATION)

    return url


def extract_links(markdown: str) -> Set[str]:
    # Remove iframes first to ignore their URLs
    cleaned = IFRAME_RE.sub('', markdown)
    # Remove fenced code blocks
    cleaned = FENCED_CODE_RE.sub('', cleaned)
    urls: Set[str] = set()

    # First, extract markdown links with angle brackets: [text](<url>)
    # and remove them from the text to avoid double-matching
    for match in MARKDOWN_LINK_ANGLE_RE.findall(cleaned):
        url = normalize_url(match.split()[0])
        if url:
            urls.add(url)
    cleaned = MARKDOWN_LINK_ANGLE_RE.sub('', cleaned)

    # Then extract regular markdown links: [text](url)
    # Remove them from text after extraction
    for match in MARKDOWN_LINK_RE.findall(cleaned):
        url = normalize_url(match.split()[0])
        if url:
            urls.add(url)
    cleaned = MARKDOWN_LINK_RE.sub('', cleaned)

    # Extract autolinks: <url>
    for match in AUTOLINK_RE.findall(cleaned):
        url = normalize_url(match)
        if url:
            urls.add(url)
    cleaned = AUTOLINK_RE.sub('', cleaned)

    # Extract bare URLs from remaining text
    for match in BARE_URL_RE.findall(cleaned):
        url = normalize_url(match)
        if url:
            urls.add(url)

    return urls


def build_article_url(frontmatter: Dict) -> str:
    def clean_frontmatter_value(value: object) -> str:
        if value is None:
            return ''
        return str(value).strip()

    canonical = clean_frontmatter_value(frontmatter.get('canonical_url'))
    if canonical:
        return canonical

    alias = clean_frontmatter_value(frontmatter.get('alias'))
    slug = clean_frontmatter_value(frontmatter.get('slug'))
    path = alias or slug

    if not BLOG_SITE_URL:
        return path or 'unknown'

    if path:
        return f"{BLOG_SITE_URL.rstrip('/')}/{path.lstrip('/')}"

    return BLOG_SITE_URL


def find_markdown_files() -> Iterable[Path]:
    backup_path = Path(BACKUP_FOLDER)
    return sorted(backup_path.glob('*/index.md'))


def check_link(session: requests.Session, url: str) -> Optional[str]:
    global _last_request_time

    try:
        if not is_safe_url(url):
            return 'invalid_url'

        # Apply rate limiting
        if RATE_LIMIT_DELAY > 0:
            with _rate_limit_lock:
                current_time = time.time()
                time_since_last = current_time - _last_request_time
                if time_since_last < RATE_LIMIT_DELAY:
                    time.sleep(RATE_LIMIT_DELAY - time_since_last)
                _last_request_time = time.time()

        head_response = session.head(url, allow_redirects=True, timeout=LINK_TIMEOUT)
        status_code = head_response.status_code
        if status_code in {405}:
            head_response.close()
            get_response = session.get(url, allow_redirects=True, timeout=LINK_TIMEOUT, stream=True)
            status_code = get_response.status_code
            get_response.close()

        if status_code >= 400:
            status_str = f'http_{status_code}'

            # Auto-exclude domains with bot detection or aggressive rate limiting
            # 403: Forbidden (often bot blocking)
            # 429: Too Many Requests (rate limiting)
            # 999: LinkedIn's custom "request denied" code
            if status_code in {403, 429, 999}:
                add_domain_to_excluded(url, status_str)
            # 404: Not Found - auto-exclude for certain domains known to block bots
            # (komoot tours, Bluesky profiles, etc. return 404 for bot requests)
            elif status_code == 404:
                domain = get_domain_from_url(url)
                if domain and domain in {'komoot.com', 'bsky.app'}:
                    add_domain_to_excluded(url, status_str)

            return status_str

        return None
    except requests.RequestException as exc:
        error_class = exc.__class__.__name__
        error_str = f'error_{error_class}'

        # Auto-exclude domains that have connection issues or timeouts
        # These are often temporary issues or bot-blocking mechanisms
        # ConnectTimeout: Connection timeout
        # ConnectionError: Generic connection error
        # TooManyRedirects: Redirect loop (often bot protection)
        # ReadTimeout: Read timeout
        if error_class in {'ConnectTimeout', 'ConnectionError', 'TooManyRedirects', 'ReadTimeout'}:
            add_domain_to_excluded(url, error_str)

        return error_str


def collect_links() -> Dict[str, Dict[str, Set[str]]]:
    link_map: Dict[str, Dict[str, Set[str]]] = {}
    excluded_count = 0

    for markdown_file in find_markdown_files():
        content = markdown_file.read_text(encoding='utf-8')
        frontmatter, body = strip_frontmatter(content)
        article_url = build_article_url(frontmatter)
        links = extract_links(body)

        for link in links:
            if not link.startswith(('http://', 'https://')):
                continue

            # Skip excluded domains
            if is_excluded_domain(link):
                excluded_count += 1
                continue

            if link not in link_map:
                link_map[link] = {"articles": set(), "files": set()}
            link_map[link]["articles"].add(article_url)
            link_map[link]["files"].add(str(markdown_file))

    if excluded_count > 0:
        logger.info("Excluded %s links from excluded domains", excluded_count)

    return link_map


def run_link_checks(link_map: Dict[str, Dict[str, Set[str]]]) -> List[LinkIssue]:
    if not link_map:
        return []

    session = create_session(USER_AGENT)
    issues: List[LinkIssue] = []

    with ThreadPoolExecutor(max_workers=MAX_LINK_WORKERS) as executor:
        future_map = {
            executor.submit(check_link, session, url): url
            for url in link_map.keys()
        }

        for future in as_completed(future_map):
            url = future_map[future]
            status = future.result()
            if status:
                # Pick a representative file path (first one from the set)
                file_path = next(iter(link_map[url]["files"])) if link_map[url]["files"] else "unknown"
                # Create one issue per article, not per (article, file) combination
                for article_url in link_map[url]["articles"]:
                    issues.append(
                        LinkIssue(
                            article_url=article_url,
                            link_url=url,
                            status=status,
                            file_path=file_path,
                        )
                    )

    return issues


def save_report(issues: List[LinkIssue]) -> None:
    report_data = [
        {
            "article_url": issue.article_url,
            "link_url": issue.link_url,
            "status": issue.status,
            "file_path": issue.file_path,
        }
        for issue in issues
    ]

    if report_data:
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved broken link report to {REPORT_FILE}")
    else:
        if REPORT_FILE.exists():
            REPORT_FILE.unlink()
        logger.info("No broken links found")


def main() -> None:
    if not LINK_CHECKER_ENABLED:
        logger.info("Link checker disabled via config")
        return

    logger.info("Collecting links from blog backups...")
    link_map = collect_links()
    logger.info("Checking %s unique links", len(link_map))

    issues = run_link_checks(link_map)
    logger.info("Broken links found: %s", len(issues))
    save_report(issues)


if __name__ == '__main__':
    main()
