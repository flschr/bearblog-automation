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
    # Einfaches File-Lock (für einzelne GitHub Action ausreichend)
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
    """Thread-sicher prüfen ob Link bereits gepostet wurde."""
    if not os.path.exists('posted.txt'):
        return False
    
    with posted_file_lock():
        with open('posted.txt', 'r') as f:
            return link in f.read()

def mark_as_posted(link):
    """Thread-sicher Link als gepostet markieren."""
    with posted_file_lock():
        with open('posted.txt', 'a') as f:
            f.write(link + '\n')
    logger.info(f"Markiert als gepostet: {link}")

def get_html_content(entry):
    """Wandelt HTML in sauberen Text um."""
    try:
        html = entry.content[0].value if hasattr(entry, 'content') else entry.get('summary', '')
        soup = BeautifulSoup(html, "html.parser")
        for img in soup.find_all('img'): 
            img.decompose()
        return soup.get_text(separator=' ')
    except Exception as e:
        logger.error(f"Fehler beim HTML-Parsing: {e}")
        return ""

def get_first_image(entry):
    """Sucht das erste Beitragsbild im Feed."""
    try:
        html = entry.content[0].value if hasattr(entry, 'content') else entry.get('summary', '')
        match = re.search(r'<img [^>]*src="([^"]+)"', html)
        return match.group(1) if match else None
    except Exception as e:
        logger.error(f"Fehler bei Bildextraktion: {e}")
        return None

def download_image(img_url, save_path="temp.jpg"):
    """Lädt Bild herunter mit Validierung."""
    try:
        logger.info(f"Lade Bild herunter: {img_url}")
        r = session.get(img_url, timeout=REQUEST_TIMEOUT, stream=True)
        r.raise_for_status()
        
        # Größencheck
        content_length = int(r.headers.get('content-length', 0))
        if content_length > MAX_IMAGE_SIZE:
            logger.warning(f"Bild zu groß ({content_length} bytes): {img_url}")
            return None
        
        # Content-Type Check
        content_type = r.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            logger.warning(f"Kein Bild-Content-Type ({content_type}): {img_url}")
            return None
        
        # Speichern
        with open(save_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Bild erfolgreich heruntergeladen: {save_path}")
        return save_path
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Fehler beim Bild-Download: {e}")
        return None
    except Exception as e:
        logger.error(f"Unerwarteter Fehler beim Bild-Download: {e}")
        return None

def get_og_metadata(url):
    """Extrahiert OG-Daten für die BlueSky Vorschau-Karte."""
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
    except requests.exceptions.RequestException as e:
        logger.error(f"Fehler beim Abrufen der OG-Metadata: {e}")
        return None
    except Exception as e:
        logger.error(f"Unerwarteter Fehler bei OG-Metadata: {e}")
        return None

def submit_to_indexnow(url):
    """Übermittelt die URL via IndexNow (Bing/Yandex)."""
    key = os.getenv('INDEXNOW_KEY')
    if not key:
        logger.debug("IndexNow Key nicht gesetzt, überspringe Submission")
        return
    
    payload = {
        "host": "fischr.org",
        "key": key,
        "keyLocation": f"https://fischr.org/{key}.txt",
        "urlList": [url]
    }
    
    try:
        r = session.post("https://www.bing.com/indexnow", json=payload, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        logger.info(f"IndexNow Submission erfolgreich: {url} (Status: {r.status_code})")
    except requests.exceptions.RequestException as e:
        logger.error(f"IndexNow Fehler für {url}: {e}")
    except Exception as e:
        logger.error(f"Unerwarteter IndexNow Fehler: {e}")

def post_to_bluesky(text, link, img_path):
    """Postet auf BlueSky mit klickbarem Link und Vorschau-Karte."""
    try:
        client = Client()
        handle = os.getenv('BSKY_HANDLE')
        password = os.getenv('BSKY_PW')
        
        if not handle or not password:
            raise ValueError("BlueSky Credentials fehlen")
        
        logger.info("Verbinde mit BlueSky...")
        client.login(handle, password)
        
        tb = client_utils.TextBuilder()
        
        # Klickbaren Link im Text erzeugen
        if link and link in text:
            parts = text.split(link)
            tb.text(parts[0][:150])
            tb.link(link, link)
            if len(parts) > 1: 
                tb.text(parts[1])
        else:
            tb.text(text[:290])

        embed = None
        if img_path and os.path.exists(img_path):
            # Priorität A: Bild-Post
            logger.info(f"Lade Bild hoch zu BlueSky: {img_path}")
            with open(img_path, 'rb') as f:
                upload = client.upload_blob(f.read())
                embed = models.AppBskyEmbedImages.Main(images=[
                    models.AppBskyEmbedImages.Image(alt="", image=upload.blob)
                ])
        elif link:
            # Priorität B: Link-Post mit Vorschau-Karte
            meta = get_og_metadata(link)
            if meta:
                thumb_blob = None
                if meta["image_url"]:
                    try:
                        img_r = session.get(meta["image_url"], timeout=5)
                        img_r.raise_for_status()
                        thumb_blob = client.upload_blob(img_r.content).blob
                    except Exception as e:
                        logger.warning(f"Thumbnail-Upload fehlgeschlagen: {e}")
                
                embed = models.AppBskyEmbedExternal.Main(external=models.AppBskyEmbedExternal.External(
                    title=meta["title"], 
                    description=meta["description"], 
                    uri=link, 
                    thumb=thumb_blob
                ))

        client.send_post(text=tb, embed=embed)
        logger.info("BlueSky Post erfolgreich")
        return True
        
    except Exception as e:
        logger.error(f"BlueSky Post fehlgeschlagen: {e}")
        raise

def post_to_mastodon(text, img_path):
    """Postet auf Mastodon (Plain Text für native Vorschau)."""
    try:
        token = os.getenv('MASTO_TOKEN')
        if not token:
            raise ValueError("Mastodon Token fehlt")
        
        logger.info("Verbinde mit Mastodon...")
        m = Mastodon(access_token=token, api_base_url='https://mastodon.social')
        
        media_ids = []
        if img_path and os.path.exists(img_path):
            logger.info(f"Lade Bild hoch zu Mastodon: {img_path}")
            media_ids = [m.media_post(img_path)['id']]
        
        m.status_post(status=text[:500], media_ids=media_ids)
        logger.info("Mastodon Post erfolgreich")
        return True
        
    except Exception as e:
        logger.error(f"Mastodon Post fehlgeschlagen: {e}")
        raise

def check_filter(entry, include, exclude):
    """Filtert Artikel nach Keywords/Tags."""
    try:
        text = (entry.title + " " + entry.get('summary', '')).lower()
        tags = [t.term.lower() for t in entry.tags] if hasattr(entry, 'tags') else []
        
        # Exclude hat Priorität
        if any(w.lower() in text or w.lower() in tags for w in exclude): 
            return False
        
        # Include-Filter (wenn leer, alles erlaubt)
        return not include or any(w.lower() in text or w.lower() in tags for w in include)
    except Exception as e:
        logger.error(f"Fehler beim Filter-Check: {e}")
        return False

def post_with_retry(func, *args, **kwargs):
    """Führt Funktion mit Retry-Logic aus."""
    for attempt in range(MAX_RETRIES):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                wait_time = 2 ** attempt
                logger.warning(f"Versuch {attempt + 1} fehlgeschlagen, warte {wait_time}s: {e}")
                sleep(wait_time)
                continue
            logger.error(f"Alle {MAX_RETRIES} Versuche fehlgeschlagen")
            raise

def run():
    """Hauptprozess des Bots."""
    try:
        logger.info("=== Bot-Run gestartet ===")
        
        # Config laden
        with open('config.json') as f: 
            config = json.load(f)
        logger.info(f"Config geladen: {len(config)} Feed(s)")
        
        # posted.txt initialisieren falls nicht vorhanden
        if not os.path.exists('posted.txt'): 
            open('posted.txt', 'w').close()
            logger.info("posted.txt erstellt")
        
        for cfg in config:
            feed_name = cfg.get('name', 'Unbekannt')
            logger.info(f"\n--- Prüfe Feed: {feed_name} ---")
            
            try:
                # Feed abrufen mit Session
                feed_url = cfg['url']
                logger.info(f"Rufe Feed ab: {feed_url}")
                response = session.get(feed_url, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                feed = feedparser.parse(response.content)
                
                if not feed.entries:
                    logger.warning(f"Keine Einträge in Feed: {feed_name}")
                    continue
                
                logger.info(f"{len(feed.entries)} Einträge gefunden")
                
                for entry in feed.entries:
                    if not hasattr(entry, 'link'):
                        logger.warning("Eintrag ohne Link gefunden, überspringe")
                        continue
                    
                    # Duplikat-Check (thread-sicher)
                    if is_posted(entry.link):
                        logger.debug(f"Bereits gepostet: {entry.link}")
                        continue
                    
                    # Filter-Check
                    if not check_filter(entry, cfg.get('include', []), cfg.get('exclude', [])):
                        logger.debug(f"Gefiltert: {entry.title}")
                        continue
                    
                    logger.info(f"Poste: {entry.title}")
                    
                    # Bild herunterladen falls gewünscht
                    img_path = None
                    if cfg.get('include_images'):
                        img_url = get_first_image(entry)
                        if img_url:
                            img_path = download_image(img_url)
                    
                    # Post-Text erstellen
                    clean_body = get_html_content(entry)
                    msg = cfg['template'].format(
                        title=entry.title, 
                        link=entry.link, 
                        content=clean_body
                    )
                    
                    # Zu Plattformen posten
                    post_success = False
                    try:
                        if "bluesky" in cfg.get('targets', []):
                            post_with_retry(post_to_bluesky, msg, entry.link, img_path)
                            post_success = True
                        
                        if "mastodon" in cfg.get('targets', []):
                            post_with_retry(post_to_mastodon, msg, img_path)
                            post_success = True
                        
                        # IndexNow Submission
                        if post_success:
                            submit_to_indexnow(entry.link)
                            # Sofort als gepostet markieren (thread-sicher)
                            mark_as_posted(entry.link)
                        
                    except Exception as e:
                        logger.error(f"Post fehlgeschlagen für {entry.title}: {e}")
                    finally:
                        # Temporäres Bild aufräumen
                        if img_path and os.path.exists(img_path):
                            os.remove(img_path)
                            logger.debug(f"Temporäres Bild gelöscht: {img_path}")
            
            except Exception as e:
                logger.error(f"Fehler bei Feed {feed_name}: {e}")
                continue
        
        logger.info("=== Bot-Run beendet ===")
        
    except Exception as e:
        logger.critical(f"Kritischer Fehler im Bot: {e}")
        raise

if __name__ == "__main__": 
    run()