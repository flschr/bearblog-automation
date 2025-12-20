# Bear Blog Backup System

This repository contains two different backup systems for your Bear Blog:

## 1. Backblaze B2 Backup (Existing)

**Files:**
- [full_backup.py](full_backup.py) - Downloads articles from sitemap and saves them to Backblaze B2
- [.github/workflows/backup_full.yml](../.github/workflows/backup_full.yml)

**How it works:**
- Crawls the sitemap from fischr.org
- Converts HTML to Markdown
- Uploads images to Backblaze B2
- Saves Markdown files to B2

---

## 2. GitHub Backup (New) ⭐

**Files:**
- [backup_to_github.py](backup_to_github.py) - Downloads CSV export and creates local folder structure
- [.github/workflows/backup_to_github.yml](../.github/workflows/backup_to_github.yml)

**How it works:**
- Downloads the complete CSV export from Bear Blog (authenticated with session cookie)
- **Incremental backup**: Only processes new or changed articles
- Creates a folder for each article: `YYYY-MM-DD-title/`
- Saves all metadata in the frontmatter of `index.md`
- Downloads all images locally to the article folder
- Original URLs in the markdown remain unchanged (as backup)
- Tracking via `processed_articles.txt` (UID + Content-Hash)

### Setup for GitHub Backup

#### 1. Find Session Cookie

**In Brave/Chrome:**
1. Open https://bearblog.dev/fischr/dashboard/
2. Press `F12` → Tab `Application` → `Cookies`
3. Look for `sessionid` and copy the value

**In Firefox:**
1. Press `F12` → Tab `Storage` → `Cookies`
2. Look for `sessionid` and copy the value

#### 2. Store Cookie in GitHub

1. Go to: Repository → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `BEAR_COOKIE`
4. Value: `sessionid=YOUR_COPIED_VALUE` (including `sessionid=`)

#### 3. Start First Test Run

1. Go to: Repository → **Actions**
2. Select on the left: **Bear Blog Backup to GitHub**
3. Click on the right: **Run workflow** → **Run workflow**

### Folder Structure

After backup, the structure looks like this:

```
blog_posts/
├── 2025-05-23-inside/
│   ├── index.md
│   └── mv5bywjky2i3nwqtywzimc00mjfjlwiyogi.webp
├── 2025-05-15-my-second-article/
│   ├── index.md
│   └── photo.jpg
└── ...
```

### Example index.md

```markdown
---
uid: "EqTWJujZaKDmWMfMYxIV"
title: "🍿 Inside (★​★★​☆☆)"
slug: "inside"
alias: "2025/05/24/inside"
published_date: "2025-05-23T22:00:00+00:00"
tags: "blog, popcornfieber"
publish: "True"
---

![Auto-generated description: ...](https://bear-images.sfo2.cdn.digitaloceanspaces.com/fischr/mv5b...webp)

[Inside](https://de.wikipedia.org/wiki/Inside_(2023)) is one of those chamber pieces...
```

### Schedule

- **Automatic:** Every Monday at midnight (UTC)
- **Manual:** Anytime via GitHub Actions

### Cookie Expiration

The session cookie expires after ~3 months. When the backup fails:

1. You'll receive an email from GitHub about the failed workflow
2. Log in to Bear Blog
3. Copy the new `sessionid` value
4. Update the secret `BEAR_COOKIE` in GitHub

### Advantages of This System

✅ **Complete**: All articles from CSV, not just feed
✅ **Incremental**: Only processes new/changed articles (fast & efficient)
✅ **Offline-capable**: Images stored locally in repo
✅ **Versioned**: GitHub shows all changes in history
✅ **Portable**: Markdown + Frontmatter → import to other systems possible
✅ **Free**: GitHub Actions & Storage are free for public repos

### How Does Incremental Backup Work?

The script saves a list of all processed articles in `backup/processed_articles.txt`:

```
EqTWJujZaKDmWMfMYxIV|5f4dcc3b5aa765d61d8327deb882cf99
xYz123AbC456DeF789|a3c65c2974270fd093ee8a9bf8ae7d0b
...
```

Format: `UID|Content-Hash`

**On each run:**
1. CSV is downloaded
2. Content hash is calculated for each article
3. Comparison with `processed_articles.txt`:
   - **New**: Article is processed and added to list
   - **Changed**: Article is reprocessed, hash is updated
   - **Unchanged**: Article is skipped ⚡

**Result:** Only new or edited articles are downloaded and committed!
