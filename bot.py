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

# Globale Session für bessere Performance
session = requests.Session()
session.headers.update({'User-Agent': 'feed2social/1.0'})

# Konstanten
MAX_IMAGE_SIZE = 5_000_000  # 5MB
REQUEST_TIMEOUT = 10
MAX_RETRIES = 3

@contextmanager
def posted_file_lock():
    """Context Manager für thread-sicheren Zugriff auf posted.txt"""
    lock_file = 'posted.txt.lock'
    retry = 0
    while os.path.exists(lock_file) and retry < 10:
        sleep(0.5)
        retry += 1
    try:
        open(lock_file, 'w').close()
        yield
    finally:
        if os.path.exists(lock_file):
            os.remove(lock_file)

def is_posted(link):
    if not os.path.exists('posted.txt'): return False
    with posted_file_lock():
        with open('posted.txt', 'r') as f:
            return link in f.read()

def mark_as_posted(link):
    with posted_file_lock():
        with open('posted.txt', 'a') as f:
            f.write(link + '\n')
    logger.info(f"Markiert als gepostet: {link}")

def get_html_content(entry):
    try:
        html = entry.content[0].value if hasattr(entry, 'content') else entry.get('summary', '')
        soup = BeautifulSoup(html, "html.parser")
        for img in soup.find_all('img'): img.decompose()
        return soup.get_text(separator=' ')
    except Exception as e:
        logger.error(f"Fehler beim HTML-Parsing: {e}")
        return ""

def get_first_image(entry):
    try:
        html = entry.content[0].value if hasattr(entry, 'content') else entry.get('summary', '')
        match = re.search(r'<img [^>]*src="([^"]+)"', html)
        return match.group(1) if match else None
    except Exception as e:
        logger.error(f"Fehler bei Bildextraktion: {e}")
        return None

def download_image(img_url, save_path="temp.jpg"):
    try:
        logger.info(f"Lade Bild herunter: {img_url}")
        r = session.get(img_url, timeout=REQUEST_TIMEOUT, stream=True)
        r.raise_for_status()
        content_length = int(r.headers.get('content-length', 0))
        if content_length > MAX_IMAGE_SIZE:
            logger.warning(f"Bild zu groß: {img_url}")
            return None
        if not r.headers.get('content-type', '').startswith('image/'):
            return None
        with open(save_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
        return save_path
    except Exception as e:
        logger.error(f"Bild-Download Fehler: {e}")
        return None

def get_og_metadata(url):
    try:
        logger.info(f"Hole OG-Metadata von: {url}")
        r = session.get(url, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        title = soup.find("meta", property="og:title")
        desc = soup.find("meta", property="og:description")
        img = soup.find("meta", property="og:image")
        return {
            "title": title["content"] if title else "Blogartikel",
            "description": desc["content"] if desc else "",
            "image_url": img["content"] if img else None
        }
    except Exception as e:
        logger.error(f"OG-Metadata Fehler: {e}")
        return None

# --- HIER IST DIE GEÄNDERTE FUNKTION ---
def submit_to_indexnow(url):
    """Übermittelt die URL via IndexNow (Bing/Yandex)."""
    key = os.getenv('INDEXNOW_KEY')
    if not key:
        # Auf Warning gesetzt, damit es im GitHub Log sichtbar ist
        logger.warning("INDEXNOW_KEY fehlt in den GitHub Secrets!")
        return
    
    payload = {
        "host": "fischr.org",
        "key": key,
        # keyLocation lassen wir weg, da Bing den Key über DNS prüft
        "urlList": [url]
    }
    
    try:
        # Wir senden an Bing (IndexNow Standard)
        r = session.post("https://www.bing.com/indexnow", json=payload, timeout=REQUEST_TIMEOUT)
        if r.status_code == 200:
            logger.info(f"IndexNow Submission erfolgreich: {url}")
        else:
            logger.warning(f"IndexNow Antwort von Bing: Status {r.status_code} - {r.text}")
    except Exception as e:
        logger.error(f"IndexNow Fehler für {url}: {e}")

def post_to_bluesky(text, link, img_path):
    try:
        client = Client()
        handle = os.getenv('BSKY_HANDLE')
        password = os.getenv('BSKY_PW')
        if not handle or not password: raise ValueError("Credentials fehlen")
        logger.info("Verbinde mit BlueSky...")
        client.login(handle, password)
        tb = client_utils.TextBuilder()
        if link and link in text:
            parts = text.split(link)
            tb.text(parts[0][:150])
            tb.link(link, link)
            if len(parts) > 1: tb.text(parts[1])
        else:
            tb.text(text[:290])
        embed = None
        if img_path and os.path.exists(img_path):
            with open(img_path, 'rb') as f:
                upload = client.upload_blob(f.read())
                embed = models.AppBskyEmbedImages.Main(images=[models.AppBskyEmbedImages.Image(alt="", image=upload.blob)])
        elif link:
            meta = get_og_metadata(link)
            if meta:
                thumb_blob = None
                if meta["image_url"]:
                    try:
                        img_r = session.get(meta["image_url"], timeout=5)
                        thumb_blob = client.upload_blob(img_r.content).blob
                    except: pass
                embed = models.AppBskyEmbedExternal.Main(external=models.AppBskyEmbedExternal.External(
                    title=meta["title"], description=meta["description"], uri=link, thumb=thumb_blob
                ))
        client.send_post(text=tb, embed=embed)
        logger.info("BlueSky Post erfolgreich")
    except Exception as e:
        logger.error(f"BlueSky Fehler: {e}")
        raise

def post_to_mastodon(text, img_path):
    try:
        token = os.getenv('MASTO_TOKEN')
        if not token: raise ValueError("Token fehlt")
        logger.info("Verbinde mit Mastodon...")
        m = Mastodon(access_token=token, api_base_url='https://mastodon.social')
        media_ids = [m.media_post(img_path)['id']] if img_path and os.path.exists(img_path) else []
        m.status_post(status=text[:500], media_ids=media_ids)
        logger.info("Mastodon Post erfolgreich")
    except Exception as e:
        logger.error(f"Mastodon Fehler: {e}")
        raise

def check_filter(entry, include, exclude):
    text = (entry.title + " " + entry.get('summary', '')).lower()
    tags = [t.term.lower() for t in entry.tags] if hasattr(entry, 'tags') else []
    if any(w.lower() in text or w.lower() in tags for w in exclude): return False
    return not include or any(w.lower() in text or w.lower() in tags for w in include)

def post_with_retry(func, *args, **kwargs):
    for attempt in range(MAX_RETRIES):
        try: return func(*args, **kwargs)
        except Exception as e:
            if attempt < MAX_RETRIES - 1: sleep(2**attempt); continue
            raise

def run():
    try:
        logger.info("=== Bot-Run gestartet ===")
        with open('config.json') as f: config = json.load(f)
        if not os.path.exists('posted.txt'): open('posted.txt', 'w').close()
        for cfg in config:
            logger.info(f"\n--- Prüfe Feed: {cfg.get('name')} ---")
            try:
                r = session.get(cfg['url'], timeout=REQUEST_TIMEOUT)
                feed = feedparser.parse(r.content)
                for entry in feed.entries:
                    if is_posted(entry.link) or not check_filter(entry, cfg.get('include', []), cfg.get('exclude', [])):
                        continue
                    logger.info(f"Verarbeite: {entry.title}")
                    img_path = download_image(get_first_image(entry)) if cfg.get('include_images') else None
                    msg = cfg['template'].format(title=entry.title, link=entry.link, content=get_html_content(entry))
                    
                    post_success = False
                    if "bluesky" in cfg.get('targets', []):
                        post_with_retry(post_to_bluesky, msg, entry.link, img_path); post_success = True
                    if "mastodon" in cfg.get('targets', []):
                        post_with_retry(post_to_mastodon, msg, img_path); post_success = True
                    
                    if post_success:
                        submit_to_indexnow(entry.link)
                        mark_as_posted(entry.link)
                    if img_path and os.path.exists(img_path): os.remove(img_path)
            except Exception as e: logger.error(f"Feed Fehler: {e}")
        logger.info("=== Bot-Run beendet ===")
    except Exception as e: logger.critical(f"Kritischer Fehler: {e}"); raise

if __name__ == "__main__": run()