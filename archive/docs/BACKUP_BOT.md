# Backup Bot

The Backup Bot automatically saves your Bear Blog posts from the public RSS feed as Markdown files with images to this repository.

---

## How It Works

The Backup Bot works from your public RSS feed:

- It fetches entries from `backup.feed_url` (default: `<site_url>/feed/`)
- It processes all entries currently visible in that feed
- It stores each article as `YYYY-MM-DD-slug/index.md` and downloads referenced images/files

**Detailed Steps**
1. Downloads your RSS feed
2. Parses each article entry
3. Creates a folder per post: `YYYY-MM-DD-slug/`
4. Saves content as `index.md` with YAML frontmatter
5. Downloads all images referenced in the post (all common formats)
6. Optionally downloads linked files (PDFs, etc.) if enabled
7. Tracks processed articles to avoid duplicates

---

## Configuration

### Central Config (`config.yaml`)

```yaml
blog:
  bearblog_username: "your-username"

backup:
  folder: "blog-backup"
  feed_url: "https://example.com/feed/"

  # Optional: Download linked files (PDFs, documents, etc.)
  linked_files:
    enabled: false
    allowed_extensions:
      - pdf
      - epub
      - zip
    allowed_domains:
      - "bear-images.sfo2.cdn.digitaloceanspaces.com"
```

| Setting | Description | Default |
|---------|-------------|---------|
| `backup.folder` | Directory for blog post backups | `blog-backup` |
| `backup.feed_url` | RSS feed URL used for backup | `<site_url>/feed/` |
| `backup.linked_files.enabled` | Download linked files (PDFs, etc.) | `false` |
| `backup.linked_files.allowed_extensions` | File extensions to download | `[]` |
| `backup.linked_files.allowed_domains` | Domains to download from | `[]` |

### Linked Files Backup

By default, the Backup Bot downloads **images** in all common formats (jpg, png, webp, gif, etc.) automatically.

If you want to also backup **linked files** like PDFs, EPUBs, or ZIPs, you can enable the `linked_files` feature:

1. Set `enabled: true`
2. Add allowed file extensions to `allowed_extensions`
3. Add trusted domains to `allowed_domains` (for security)

> [!NOTE]
> When you enable this feature, the bot will also check **existing articles** for linked files on the next run. Files that already exist won't be downloaded again.

## Backup Folder Structure

```
blog-backup/
├── 2025-01-15-my-first-post/
│   ├── index.md
│   └── image.webp
├── 2025-01-20-another-post/
│   ├── index.md
│   ├── photo1.webp
│   └── photo2.webp
└── ...
```

Each `index.md` contains:
- YAML frontmatter with all metadata (title, date, tags, etc.)
- Full post content in Markdown

---

## Scheduling

The backup runs:
- **Weekly**: Every Monday at midnight UTC (default, feel free to adopt)
- **After new posts**: When the Social Bot detects new articles in any RSS feed, it triggers the Backup Bot to run afterwards - ensuring your backup stays current
- **Manually**: Via GitHub Actions → Run workflow

---

## Related Documentation

- [Social Bot](SOCIAL_BOT.md) - Automatic social media posting & feed configuration
- [Cloudflare Worker](CLOUDFLARE_WORKER.md) - Instant trigger setup
