import os
import requests
import re
import feedparser
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from b2sdk.v2 import InMemoryAccountInfo, B2Api

# --- PATH LOGIC ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTED_FILE_PATH = os.path.join(BASE_DIR, 'posted.txt')

# --- CONFIGURATION ---
B2_KEY_ID = os.getenv('B2_KEY_ID')
B2_APPLICATION_KEY = os.getenv('B2_APPLICATION_KEY')
B2_BUCKET_NAME = os.getenv('B2_BUCKET_NAME')
RSS_FEED_URL = "https://fischr.org/feed/"

def get_b2_bucket():
    """Initializes and returns the Backblaze B2 bucket object."""
    info = InMemoryAccountInfo()
    b2_api = B2Api(info)
    b2_api.authorize_account("production", B2_KEY_ID, B2_APPLICATION_KEY)
    return b2_api.get_bucket_by_name(B2_BUCKET_NAME)

def run_regular_backup():
    """Checks the RSS feed for new entries and backs them up."""
    print("🚀 Checking RSS feed for new posts...")
    bucket = get_b2_bucket()
    feed = feedparser.parse(RSS_FEED_URL)
    
    if not os.path.exists(POSTED_FILE_PATH):
        with open(POSTED_FILE_PATH, 'w') as f: pass

    with open(POSTED_FILE_PATH, 'r') as f:
        already_done = f.read().splitlines()

    new_posts_count = 0

    for entry in feed.entries:
        if entry.link in already_done:
            continue
        
        # Get date from RSS (YYYY-MM-DD)
        dt = entry.published_parsed
        date_str = f"{dt.tm_year}-{dt.tm_mon:02d}-{dt.tm_mday:02d}"
        
        # Generate folder name from date and slug
        raw_slug = entry.link.strip('/').split('/')[-1]
        folder_name = f"{date_str}-{raw_slug}"

        print(f"📥 New post found: {entry.title} -> {folder_name}")
        
        html_content = entry.content[0].value if hasattr(entry, 'content') else entry.summary
        soup = BeautifulSoup(html_content, "html.parser")

        # --- CLEANUP: Remove Pot-of-Honey ---
        for honey in soup.find_all(href=re.compile(r"pot-of-honey")):
            honey.decompose()
        
        # Extract unique hashtags
        tags = re.findall(r'#\w+', soup.get_text())
        tags_str = ", ".join(set(tags)) if tags else ""

        # --- IMAGES: Flat structure & WebP fix ---
        img_tags = soup.find_all('img')
        for i, img in enumerate(img_tags):
            img_url = img.get('src')
            if not img_url: continue
            if img_url.startswith('/'): img_url = "https://fischr.org" + img_url
            
            try:
                img_data = requests.get(img_url, timeout=10).content
                # Handle WebP extension specifically
                ext = 'webp' if 'webp' in img_url.lower() else img_url.split('.')[-1].split('?')[0][:3].lower()
                bucket.upload_bytes(img_data, f"{folder_name}/img_{i}.{ext}")
            except: pass

        # --- MARKDOWN: Strict ATX Headings and iFrame support ---
        markdown_main = md(
            str(soup), 
            headings_style='ATX',
            convert=['iframe']
        ).strip()
        
        # Remove Bearblog date pattern from body text
        markdown_main = re.sub(r'\d{1,2} [A-Z][a-z]{2}, \d{4}', '', markdown_main).strip()

        # Build Frontmatter
        final_md = f"""---
Title: {entry.title}
URL: {entry.link}
Date: {date_str}
Tags: {tags_str}
---

{markdown_main}
"""
        # Save to B2
        bucket.upload_bytes(final_md.encode('utf-8'), f"{folder_name}/article.md")
        
        # Update progress file
        with open(POSTED_FILE_PATH, 'a') as f:
            f.write(entry.link + '\n')
        
        new_posts_count += 1
        print(f"   ✅ {folder_name} successfully backed up.")

    if new_posts_count == 0:
        print("☕ Everything up to date. No new posts.")

if __name__ == "__main__":
    run_regular_backup()