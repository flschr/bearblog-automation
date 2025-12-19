import os
import requests
import re
import feedparser
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from b2sdk.v2 import InMemoryAccountInfo, B2Api

# --- PFAD-LOGIK ---
# Ermittelt das Hauptverzeichnis (Root), um auf posted.txt zuzugreifen
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTED_FILE_PATH = os.path.join(BASE_DIR, 'posted.txt')

# --- KONFIGURATION ---
B2_KEY_ID = os.getenv('B2_KEY_ID')
B2_APPLICATION_KEY = os.getenv('B2_APPLICATION_KEY')
B2_BUCKET_NAME = "fischrorg-backup"
RSS_FEED_URL = "https://fischr.org/feed/"

def get_b2_bucket():
    info = InMemoryAccountInfo()
    b2_api = B2Api(info)
    b2_api.authorize_account("production", B2_KEY_ID, B2_APPLICATION_KEY)
    return b2_api.get_bucket_by_name(B2_BUCKET_NAME)

def slugify(text):
    # Erstellt saubere Dateinamen
    return re.sub(r'[\W_]+', '-', text.lower()).strip('-')

def run_backup():
    print("🚀 Starte Backup-Prozess...")
    bucket = get_b2_bucket()
    feed = feedparser.parse(RSS_FEED_URL)
    
    # Sicherstellen, dass posted.txt existiert
    if not os.path.exists(POSTED_FILE_PATH):
        with open(POSTED_FILE_PATH, 'w') as f: pass

    with open(POSTED_FILE_PATH, 'r') as f:
        already_done = f.read().splitlines()

    new_entries_count = 0

    for entry in feed.entries:
        if entry.link in already_done:
            continue
        
        print(f"📥 Sichere neuen Artikel: {entry.title}")
        title_slug = slugify(entry.title)
        
        # HTML Content extrahieren
        html_content = entry.content[0].value if hasattr(entry, 'content') else entry.summary
        soup = BeautifulSoup(html_content, "html.parser")
        
        # 1. Bilder zu Backblaze (stilles Backup)
        img_tags = soup.find_all('img')
        for i, img in enumerate(img_tags):
            img_url = img.get('src')
            if not img_url: continue
            if img_url.startswith('/'): img_url = "https://fischr.org" + img_url
            
            try:
                img_res = requests.get(img_url, timeout=10)
                # Extrahiere Endung (jpg, png etc)
                ext = img_url.split('.')[-1].split('?')[0][:3]
                if len(ext) > 4: ext = "jpg" # Fallback
                
                bucket.upload_bytes(
                    img_res.content, 
                    f"backups/{title_slug}/images/img_{i}.{ext}"
                )
            except Exception as e:
                print(f"   ⚠️ Bildfehler: {e}")

        # 2. Markdown erstellen und zu Backblaze (Links bleiben original)
        markdown_text = f"# {entry.title}\n\nURL: {entry.link}\n\n" + md(html_content)
        bucket.upload_bytes(
            markdown_text.encode('utf-8'), 
            f"backups/{title_slug}/article.md"
        )
        
        # 3. Fortschritt lokal speichern
        with open(POSTED_FILE_PATH, 'a') as f:
            f.write(entry.link + '\n')
        
        new_entries_count += 1
        print(f"   ✅ {title_slug} erfolgreich gesichert.")

    if new_entries_count == 0:
        print("☕ Keine neuen Artikel gefunden.")
    else:
        print(f"✨ Backup beendet. {new_entries_count} Artikel gesichert.")

if __name__ == "__main__":
    run_backup()