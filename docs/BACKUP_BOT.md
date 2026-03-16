# Backup Bot

The Backup Bot creates a Git-tracked backup of your Bear Blog posts from RSS and stores them in this repository as Markdown + local assets.

---

## How It Works

The bot reads your public RSS feed and keeps a local backup tree in sync:

- Fetches entries from `backup.feed_url` (or falls back to `<site_url>/feed/`)
- Builds a content hash per entry (`id/link/title/date/content`)
- Creates or updates post folders named `YYYY-MM-DD-slug/`
- Writes `index.md` with YAML frontmatter + Markdown body
- Downloads referenced images (concurrent)
- Optionally downloads selected linked files (PDF/EPUB/ZIP, etc.)
- Stores processed hashes in `archive/bots/backup_bot/processed_articles.txt`

### What Changed (current script behavior)

Compared to older backup behavior, the current bot is **hash-based**, not “new-entry-only”:

- If an existing RSS entry changes, the backup is updated on the next run
- Already unchanged entries are skipped quickly
- Linked files can be enabled with domain + extension allowlists for safer downloads

---

## Configuration

### Central Config (`config.yaml`)

```yaml
blog:
  site_url: "https://example.com"

backup:
  folder: "blog-backup"
  # feed_url: "https://example.com/feed/"  # optional override

  linked_files:
    enabled: false
    allowed_extensions:
      - pdf
      - epub
      - zip
    allowed_domains:
      - "example.com"
      - "bear-images.sfo2.cdn.digitaloceanspaces.com"
```

| Setting | Description | Default |
|---------|-------------|---------|
| `backup.folder` | Directory for blog post backups | `blog-backup` |
| `backup.feed_url` | RSS feed URL used for backup | `<site_url>/feed/` |
| `backup.linked_files.enabled` | Download linked non-image files | `false` |
| `backup.linked_files.allowed_extensions` | Allowed file extensions for linked files | `[]` |
| `backup.linked_files.allowed_domains` | Allowed domains for linked files | `[]` |

> Images are always downloaded from article content (subject to shared safety/size checks). `linked_files` only controls additional file links.

---

## Workflow & Triggering

Active workflow: `.github/workflows/backup_bot.yml`

The backup runs:
- **Weekly**: Monday 00:00 UTC
- **After Social Bot updates**: called via `workflow_call` from `social_bot.yml`
- **Manually**: via `workflow_dispatch`

The workflow commits:
- `blog-backup/**`
- `archive/bots/backup_bot/processed_articles.txt`

---

## Backup Folder Structure

```
blog-backup/
├── 2025-01-15-my-first-post/
│   ├── index.md
│   └── image.webp
├── 2025-01-20-another-post/
│   ├── index.md
│   ├── photo1.webp
│   └── attachment.pdf
└── ...
```

Each `index.md` contains frontmatter fields from RSS metadata (title, link, published, tags, rss_id/source) plus the article content.

---

## Related Documentation

- [Social Bot](SOCIAL_BOT.md) - Automatic social media posting & feed configuration
- [Link Checker](LINK_CHECKER.md) - Broken external link checks after backups
- [Webmentions Bot](WEBMENTIONS_BOT.md) - Collection of traditional blog mentions
- [Cloudflare Worker](CLOUDFLARE_WORKER.md) - Fast RSS-trigger setup for social workflow
