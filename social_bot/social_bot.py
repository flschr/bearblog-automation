import feedparser, json, os, re, requests
from bs4 import BeautifulSoup
from atproto import Client, client_utils, models
from mastodon import Mastodon
import logging
from contextlib import contextmanager
from time import sleep

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

session = requests.Session()
session.headers.update({'User-Agent': 'feed2social/1.0'})

# --- CONSTANTS ---
MAX_IMAGE_SIZE = 5_000_000 
REQUEST_TIMEOUT = 10

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POSTED_FILE = os.path.join(BASE_DIR, 'posted_articles.txt')
LOCK_FILE = os.path.join(BASE_DIR, 'posted_articles.txt.lock')
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')

@contextmanager
def posted_file_lock():
    """Simple file lock to prevent concurrent write access to the posted file."""
    retry = 0
    while os.path.exists(LOCK_FILE) and retry < 10:
        sleep(0.5)
        retry += 1
    try:
        open(LOCK_FILE, 'w').close()
        yield
    finally:
        if os.path.exists(LOCK_FILE): os.remove(LOCK_FILE)

def is_posted(link):
    """Check if the given URL is already recorded in the posted.txt file."""
    if not os.path.exists(POSTED_FILE): return False
    with posted_file_lock():
        with open(POSTED_FILE, 'r') as f:
            return link in f.read()

def mark_as_posted(link):
    """Add a URL to the posted.txt file to avoid duplicate posts."""
    with posted_file_lock():
        with open(POSTED_FILE, 'a') as f:
            f.write(link + '\n')
    logger.info(f"Marked as posted: {link}")

def get_html_content(entry):
    """Extract text from HTML, remove images, and clean up redundant whitespace."""
    try:
        html = entry.content[0].value if hasattr(entry, 'content') else entry.get('summary', '')
        soup = BeautifulSoup(html, "html.parser")
        
        # Remove all image tags
        for img in soup.find_all('img'): 
            img.decompose()
            
        # Extract plain text with a space separator
        text = soup.get_text(separator=' ')
        
        # --- WHITESPACE CLEANING ---
        # 1. Replace multiple spaces/tabs with a single space
        text = re.sub(r'[ \t]+', ' ', text)
        # 2. Reduce multiple newlines (more than two) down to two
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()
    except: return ""

def get_first_image_data(entry):
    """Extract the first image URL and its alt text from the post."""
    try:
        html = entry.content[0].value if hasattr(entry, 'content') else entry.get('summary', '')
        soup = BeautifulSoup(html, "html.parser")
        img = soup.find('img')
        if img and img.get('src'):
            return {"url": img.get('src'), "alt": img.get('alt', '')[:400]}
        return None
    except: return None

def download_image(img_url, save_path="temp.jpg"):
    """Download an image to a temporary file while respecting size limits."""
    try:
        r = session.get(img_url, timeout=REQUEST_TIMEOUT, stream=True)
        r.raise_for_status()
        if int(r.headers.get('content-length', 0)) > MAX_IMAGE_SIZE: return None
        with open(save_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
        return save_path
    except: return None

def get_og_metadata(url):
    """Fetch Open Graph metadata (title, description, image) for a given link."""
    try:
        r = session.get(url, timeout=REQUEST_TIMEOUT)
        soup = BeautifulSoup(r.text, 'html.parser')
        t = soup.find("meta", property="og:title")
        d = soup.find("meta", property="og:description")
        i = soup.find("meta", property="og:image")
        return {
            "title": t["content"] if t else "Blog post",
            "description": d["content"] if d else "",
            "image_url": i["content"] if i else None
        }
    except: return None

def submit_to_indexnow(url):
    """Submit the URL to IndexNow for faster search engine indexing."""
    key = os.getenv('INDEXNOW_KEY')
    if not key: return
    payload = {"host": "fischr.org", "key": key, "urlList": [url]}
    try:
        session.post("https://www.bing.com/indexnow", json=payload, timeout=REQUEST_TIMEOUT)
        logger.info(f"IndexNow Success for {url}")
    except: pass

def post_to_bluesky(text, img_path, alt_text):
    """Post rich text to Bluesky, converting hashtags and links into clickable facets."""
    client = Client()
    client.login(os.getenv('BSKY_HANDLE'), os.getenv('BSKY_PW'))
    
    # TextBuilder automatically handles rich text facets (hashtags, links)
    tb = client_utils.TextBuilder()
    
    # Split text to identify tags and links for rich text processing
    words = text.split(' ')
    for i, word in enumerate(words):
        if word.startswith('#') and len(word) > 1:
            tag_name = word[1:].rstrip('.,!?')
            tb.tag(word, tag_name)
        elif word.startswith('http'):
            tb.link(word, word)
        else:
            tb.text(word)
        
        # Add space back if it's not the last word
        if i < len(words) - 1:
            tb.text(' ')

    embed = None
    if img_path and os.path.exists(img_path):
        with open(img_path, 'rb') as f:
            upload = client.upload_blob(f.read())
            embed = models.AppBskyEmbedImages.Main(
                images=[models.AppBskyEmbedImages.Image(alt=alt_text or "", image=upload.blob)]
            )
    
    client.send_post(text=tb, embed=embed)
    logger.info("BlueSky Rich Text Success")

def post_to_mastodon(text, img_path, alt_text):
    """Post plain text status with optional media to Mastodon."""
    m = Mastodon(access_token=os.getenv('MASTO_TOKEN'), api_base_url='https://mastodon.social')
    ids = []
    if img_path:
        media = m.media_post(img_path, description=alt_text or "")
        ids.append(media['id'])
    
    m.status_post(status=text[:500], media_ids=ids)
    logger.info("Mastodon Success")

def run():
    """Main execution logic to parse feeds and post new entries based on configuration."""
    logger.info("=== Bot Start ===")
    if not os.path.exists(CONFIG_FILE):
        logger.error(f"Config file not found: {CONFIG_FILE}")
        return
        
    with open(CONFIG_FILE) as f: config = json.load(f)
    for cfg in config:
        feed = feedparser.parse(session.get(cfg['url']).content)
        for entry in feed.entries:
            if is_posted(entry.link): continue
            
            # --- PRECISE FILTERING (Title, Text-Hashtags & RSS-Categories only) ---
            content_html = entry.content[0].value if hasattr(entry, 'content') else entry.get('summary', '')
            
            # Extract hashtags from text content
            found_hashtags = " ".join(re.findall(r'#\w+', content_html))
            
            # Extract categories (tags) provided by the Bear Blog RSS feed
            rss_categories = ""
            if hasattr(entry, 'tags'):
                rss_categories = " ".join([tag.term for tag in entry.tags if hasattr(tag, 'term')])
            
            # Combine metadata for inclusion/exclusion checks (excludes main post text)
            check_string = (entry.title + " " + found_hashtags + " " + rss_categories).lower()
            
            if any(w.lower() in check_string for w in cfg.get('exclude', [])):
                continue
            if cfg.get('include') and not any(w.lower() in check_string for w in cfg['include']):
                continue

            logger.info(f"Processing: {entry.title}")
            
            img_data = get_first_image_data(entry) if cfg.get('include_images') else None
            img_path = download_image(img_data['url']) if img_data else None
            alt_text = img_data['alt'] if img_data else ""
            clean_content = get_html_content(entry)
            
            # Format message using the template from config.json
            msg = cfg['template'].format(title=entry.title, link=entry.link, content=clean_content)
            
            try:
                if "bluesky" in cfg.get('targets', []): post_to_bluesky(msg, img_path, alt_text)
                if "mastodon" in cfg.get('targets', []): post_to_mastodon(msg, img_path, alt_text)
                
                submit_to_indexnow(entry.link)
                mark_as_posted(entry.link)
                
            except Exception as e: logger.error(f"Execution Error: {e}")
            finally: 
                if img_path and os.path.exists(img_path): os.remove(img_path)
    logger.info("=== Bot End ===")

if __name__ == "__main__": run()