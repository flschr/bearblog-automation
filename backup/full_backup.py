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
    """Main function to crawl the sitemap and backup all articles."""
    print("🚀 Starting Full Backup (English comments, iFrame & WebP Fix)...")
    bucket = get_b2_bucket()
    
    # Load and parse sitemap
    r = requests.get(SITEMAP_URL, timeout=15)
    sitemap_soup = BeautifulSoup(r.content, 'xml')
    urls = [loc.text for loc in sitemap_soup.find_all('loc')]

    for url in urls:
        if url in EXCLUDE: continue
        
        try:
            res = requests.get(url, timeout=10)
            post_soup = BeautifulSoup(res.content, 'html.parser')
            
            # Identify publish date and slug
            publish_date = extract_date_from_soup(post_soup)
            raw_slug = url.strip('/').split('/')[-1]
            folder_name = f"{publish_date}-{raw_slug}"

            print(f"📥 Processing: {folder_name}")

            content_area = post_soup.find('main') or post_soup.find('article')
            if not content_area: continue

            # --- CLEANUP: Remove Pot-of-Honey and unwanted headers ---
            for honey in content_area.find_all(href=re.compile(r"pot-of-honey")):
                honey.decompose()

            # Extract hashtags before decomposing elements
            tags = re.findall(r'#\w+', content_area.get_text())
            tags_str = ", ".join(set(tags)) if tags else ""

            # Remove navigation and h1 (Title is in Frontmatter)
            for unwanted in content_area.find_all(['header', 'h1']):
                unwanted.decompose()

            # --- IMAGES: Save directly in article folder ---
            for i, img in enumerate(content_area.find_all('img')):
                img_url = img.get('src')
                if img_url:
                    if img_url.startswith('/'): img_url = "https://fischr.org" + img_url
                    try:
                        img_data = requests.get(img_url, timeout=10).content
                        # Proper WebP extension handling
                        ext = 'webp' if 'webp' in img_url.lower() else img_url.split('.')[-1].split('?')[0][:3].lower()
                        bucket.upload_bytes(img_data, f"{folder_name}/img_{i}.{ext}")
                    except: pass

            # --- MARKDOWN: ATX Headings and iFrame support ---
            markdown_main = md(
                str(content_area), 
                headings_style='ATX',
                convert=['iframe']
            ).strip()
            
            # Remove date string from content body
            markdown_main = re.sub(r'\d{1,2} [A-Z][a-z]{2}, \d{4}', '', markdown_main).strip()

            # Construct final Markdown with Frontmatter
            final_md = f"---\nTitle: {raw_slug.replace('-', ' ').title()}\nURL: {url}\nDate: {publish_date}\nTags: {tags_str}\n---\n\n{markdown_main}"
            
            bucket.upload_bytes(final_md.encode('utf-8'), f"{folder_name}/article.md")

        except Exception as e:
            print(f"❌ Error at {url}: {e}")

if __name__ == "__main__":
    run_full_backup()