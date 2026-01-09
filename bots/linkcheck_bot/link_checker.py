"""
Broken link checker for Bear Blog backups.
"""

import json
import logging
import re
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
USER_AGENT = LINK_CHECKER_CONFIG.get('user_agent', 'bearblog-link-checker/1.0')

BLOG_CONFIG = CONFIG.get('blog', {})
BLOG_SITE_URL = BLOG_CONFIG.get('site_url', '').strip()
BACKUP_FOLDER = CONFIG.get('backup', {}).get('folder', 'blog-backup')

REPORT_FILE = Path(__file__).parent / 'broken_links.json'

MARKDOWN_LINK_RE = re.compile(r'!?\[[^\]]*]\(([^)]+)\)')
AUTOLINK_RE = re.compile(r'<(https?://[^>]+)>')
BARE_URL_RE = re.compile(r'(https?://[^\s<>\[\]{}"\'`]+)')
FENCED_CODE_RE = re.compile(r'```.*?```', re.DOTALL)

TRAILING_PUNCTUATION = '.,:;!?)]}\'"'


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


def normalize_url(url: str) -> str:
    url = url.strip().strip('<>').strip()
    return url.rstrip(TRAILING_PUNCTUATION)


def extract_links(markdown: str) -> Set[str]:
    cleaned = FENCED_CODE_RE.sub('', markdown)
    urls: Set[str] = set()

    for match in MARKDOWN_LINK_RE.findall(cleaned):
        url = normalize_url(match.split()[0])
        if url:
            urls.add(url)

    for match in AUTOLINK_RE.findall(cleaned):
        url = normalize_url(match)
        if url:
            urls.add(url)

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
    try:
        if not is_safe_url(url):
            return 'invalid_url'

        head_response = session.head(url, allow_redirects=True, timeout=LINK_TIMEOUT)
        status_code = head_response.status_code
        if status_code in {405}:
            head_response.close()
            get_response = session.get(url, allow_redirects=True, timeout=LINK_TIMEOUT, stream=True)
            status_code = get_response.status_code
            get_response.close()

        if status_code >= 400:
            return f'http_{status_code}'

        return None
    except requests.RequestException as exc:
        return f'error_{exc.__class__.__name__}'


def collect_links() -> Dict[str, Dict[str, Set[str]]]:
    link_map: Dict[str, Dict[str, Set[str]]] = {}
    for markdown_file in find_markdown_files():
        content = markdown_file.read_text(encoding='utf-8')
        frontmatter, body = strip_frontmatter(content)
        article_url = build_article_url(frontmatter)
        links = extract_links(body)

        for link in links:
            if not link.startswith(('http://', 'https://')):
                continue
            if link not in link_map:
                link_map[link] = {"articles": set(), "files": set()}
            link_map[link]["articles"].add(article_url)
            link_map[link]["files"].add(str(markdown_file))

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
                for article_url in link_map[url]["articles"]:
                    for file_path in link_map[url]["files"]:
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
