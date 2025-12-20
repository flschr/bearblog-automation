import os
import requests
import re
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from b2sdk.v2 import InMemoryAccountInfo, B2Api

# --- KONFIGURATION ---
B2_KEY_ID = os.getenv('B2_KEY_ID')
B2_APPLICATION_KEY = os.getenv('B2_APPLICATION_KEY')
B2_BUCKET_NAME = os.getenv('B2_BUCKET_NAME')
SITEMAP_URL = "https://fischr.org/sitemap.xml"

EXCLUDE = ['https://fischr.org/', 'https://fischr.org/blog/', 'https://fischr.org/fotos/', 'https://fischr.org/about/']

def get_b2_bucket():
    info = InMemoryAccountInfo()
    b2_api = B2Api(info)
    b2_api.authorize_account("production", B2_KEY_ID, B2_APPLICATION_KEY)
    return b2_api.get_bucket_by_name(B2_BUCKET_NAME)

def run_full_backup():
    print("🚀 Starte MANUELLES FULL BACKUP (Datum-URL Sortierung)...")
    bucket = get_b2_bucket()
    
    r = requests.get(SITEMAP_URL, timeout=15)
    sitemap_soup = BeautifulSoup(r.content, 'xml')
    
    # Wir extrahieren URL und Datum (lastmod)
    entries = []
    for url_tag in sitemap_soup.find_all('url'):
        loc = url_tag.find('loc').text
        lastmod = url_tag.find('lastmod').text if url_tag.find('lastmod') else "0000-00-00"
        entries.append({'url': loc, 'date': lastmod})

    count = 0
    for entry in entries:
        url = entry['url']
        date = entry['date']
        
        if url in EXCLUDE:
            continue
        
        try:
            # Slug aus URL generieren
            raw_slug = url.strip('/').split('/')[-1]
            if not raw_slug or "fischr.org" in raw_slug: raw_slug = "home"
            
            # Ordnername: 2025-12-19-mein-artikel-name
            folder_name = f"{date}-{raw_slug}"

            print(f"📥 Verarbeite: {url} -> Ordner: {folder_name}")
            
            res = requests.get(url, timeout=10)
            soup = BeautifulSoup(res.content, 'html.parser')
            
            title = soup.find('h1').text if soup.find('h1') else raw_slug
            content_area = soup.find('main') or soup.find('article')
            if not content_area: continue

            # 1. Bilder sichern
            for i, img in enumerate(content_area.find_all('img')):
                img_url = img.get('src')
                if not img_url: continue
                if img_url.startswith('/'): img_url = "https://fischr.org" + img_url
                try:
                    img_data = requests.get(img_url, timeout=10).content
                    ext = img_url.split('.')[-1].split('?')[0][:3]
                    # Pfad: backups/2025-12-19-slug/images/img_0.jpg
                    bucket.upload_bytes(img_data, f"backups/{folder_name}/images/img_{i}.{ext}")
                except: pass

            # 2. Markdown sichern
            markdown_text = f"# {title}\n\nURL: {url}\nDatum: {date}\n\n" + md(str(content_area))
            bucket.upload_bytes(markdown_text.encode('utf-8'), f"backups/{folder_name}/article.md")
            
            count += 1
            print(f"   ✅ {folder_name} gesichert.")
            
        except Exception as e:
            print(f"❌ Fehler bei {url}: {e}")

    print(f"\n✨ FULL BACKUP abgeschlossen. {count} Artikel verarbeitet.")

if __name__ == "__main__":
    run_full_backup()