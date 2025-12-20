import os
import requests
import re
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from b2sdk.v2 import InMemoryAccountInfo, B2Api

# --- CONFIGURATION ---
B2_KEY_ID = os.getenv('B2_KEY_ID')
B2_APPLICATION_KEY = os.getenv('B2_APPLICATION_KEY')
B2_BUCKET_NAME = os.getenv('B2_BUCKET_NAME')
SITEMAP_URL = "https://fischr.org/sitemap.xml"

# Exclude pages that are not blog posts
EXCLUDE = ['https://fischr.org/', 'https://fischr.org/blog/', 'https://fischr.org/fotos/', 'https://fischr.org/about/']

def get_b2_bucket():
    """Initializes and returns the Backblaze B2 bucket object."""
    info = InMemoryAccountInfo()
    b2_api = B2Api(info)
    b2_api.authorize_account("production", B2_KEY_ID, B2_APPLICATION_KEY)
    return b2_api.get_bucket_by_name(B2_BUCKET_NAME)

def extract_date_from_soup(soup):
    """Extracts the publish date from the HTML text (Format: '05 Sep, 2009')."""
    months = {
        "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06",
        "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
    }
    # Pattern for 'DD Mon, YYYY'
    pattern = r'(\d{1,2}) ([A-Z][a-z]{2}), (\d{4})'
    
    match = re.search(pattern, soup.get_text())
    if match:
        day = match.group(1).zfill(2)
        month = months.get(match.group(2), "01")
        year = match.group(3)
        return f"{year}-{month}-{day}"
    return "0000-00-00"

def run_full_backup():
    print("🚀 Starting Full Backup...", flush=True)
    bucket = get_b2_bucket()
    
    r = requests.get(SITEMAP_URL, timeout=15)
    sitemap_soup = BeautifulSoup(r.content, 'xml')
    urls = [loc.text for loc in sitemap_soup.find_all('loc')]

    processed_count = 0
    for url in urls:
        if url in EXCLUDE: continue
        
        try:
            res = requests.get(url, timeout=15)
            post_soup = BeautifulSoup(res.content, 'html.parser')
            
            publish_date = extract_date_from_soup(post_soup)
            raw_slug = url.strip('/').split('/')[-1]
            folder_name = f"{publish_date}-{raw_slug}"

            # THIS LINE IS KEY: It shows us the progress in real-time
            print(f"📥 Processing: {folder_name}...", end=" ", flush=True)

            content_area = post_soup.find('main') or post_soup.find('article')
            if not content_area: 
                print("⚠️ No content found.", flush=True)
                continue

            # Cleanup
            for honey in content_area.find_all(href=re.compile(r"pot-of-honey")):
                honey.decompose()

            tags = re.findall(r'#\w+', content_area.get_text())
            tags_str = ", ".join(set(tags)) if tags else ""

            for unwanted in content_area.find_all(['header', 'h1']):
                unwanted.decompose()

            # Upload Images
            for i, img in enumerate(content_area.find_all('img')):
                img_url = img.get('src')
                if img_url:
                    if img_url.startswith('/'): img_url = "https://fischr.org" + img_url
                    try:
                        img_data = requests.get(img_url, timeout=15).content
                        ext = 'webp' if 'webp' in img_url.lower() else img_url.split('.')[-1].split('?')[0][:3].lower()
                        bucket.upload_bytes(img_data, f"{folder_name}/img_{i}.{ext}")
                    except Exception as img_err:
                        print(f"(Image Error: {img_err})", end=" ", flush=True)

            # Markdown conversion & Upload
            markdown_main = md(str(content_area), headings_style='ATX', convert=['iframe']).strip()
            markdown_main = re.sub(r'\d{1,2} [A-Z][a-z]{2}, \d{4}', '', markdown_main).strip()

            final_md = f"---\nTitle: {raw_slug.replace('-', ' ').title()}\nURL: {url}\nDate: {publish_date}\nTags: {tags_str}\n---\n\n{markdown_main}"
            
            bucket.upload_bytes(final_md.encode('utf-8'), f"{folder_name}/article.md")
            
            print("✅ Done.", flush=True)
            processed_count += 1

        except Exception as e:
            print(f"❌ Error at {url}: {e}", flush=True)

    print(f"\n✨ Backup finished. {processed_count} articles processed.", flush=True)

if __name__ == "__main__":
    run_full_backup()