import os
import requests
import re
import feedparser
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from b2sdk.v2 import InMemoryAccountInfo, B2Api

# --- PFAD-LOGIK ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTED_FILE_PATH = os.path.join(BASE_DIR, 'posted.txt')

# --- KONFIGURATION ---
B2_KEY_ID = os.getenv('B2_KEY_ID')
B2_APPLICATION_KEY = os.getenv('B2_APPLICATION_KEY')
B2_BUCKET_NAME = os.getenv('B2_BUCKET_NAME')
RSS_FEED_URL = "https://fischr.org/feed/"

def get_b2_bucket():
    info = InMemoryAccountInfo()
    b2_api = B2Api(info)
    b2_api.authorize_account("production", B2_KEY_ID, B2_APPLICATION_KEY)
    return b2_api.get_bucket_by_name(B2_BUCKET_NAME)

def slugify(text):
    return re.sub(r'[\W_]+', '-', text.lower()).strip('-')

def run_partial_backup():
    print("Checking RSS feed for new posts...")
    bucket = get_b2_bucket()
    feed = feedparser.parse(RSS_FEED_URL)
    
    if not os.path.exists(POSTED_FILE_PATH):
        open(POSTED_FILE_PATH, 'a').close()

    with open(POSTED_FILE_PATH, 'r') as f:
        already_done = f.read().splitlines()

    new_posts = 0

    for entry in feed.entries:
        if entry.link in already_done:
            continue
        
        print(f"Found new post: {entry.title}")
        title_slug = slugify(entry.title)
        
        # HTML aus dem Feed holen
        html_content = entry.content[0].value if hasattr(entry, 'content') else entry.summary
        soup = BeautifulSoup(html_content, "html.parser")
        
        # 1. Bilder sichern
        img_tags = soup.find_all('img')
        for i, img in enumerate(img_tags):
            img_url = img.get('src')
            if not img_url: continue
            if img_url.startswith('/'): img_url = "https://fischr.org" + img_url
            
            try:
                img_data = requests.get(img_url, timeout=10).content
                ext = img_url.split('.')[-1].split('?')[0][:3]
                bucket.upload_bytes(img_data, f"backups/{title_slug}/images/img_{i}.{ext}")
            except:
                pass

        # 2. Markdown Datei erstellen
        markdown_text = f"# {entry.title}\n\nURL: {entry.link}\n\n" + md(html_content)
        bucket.upload_bytes(markdown_text.encode('utf-8'), f"backups/{title_slug}/article.md")
        
        # 3. Link als erledigt markieren
        with open(POSTED_FILE_PATH, 'a') as f:
            f.write(entry.link + '\n')
        
        new_posts += 1
        print(f"Successfully backed up: {title_slug}")

    if new_posts == 0:
        print("No new posts found.")

if __name__ == "__main__":
    run_partial_backup()