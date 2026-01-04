# 🐻 (Bear) Blog Automation for fischr.org

Hey and welcome 👋🏼 This is the powerhouse behind my [Bear Blog](https://bearblog.dev)-powered website [fischr.org](https://fischr.org). Whenever I publish a new article, this repository automatically

- **posts the article to Mastodon and Bluesky**, with an individual template based on the content
- **backs up everything** as Markdown files with images right here in this repo
- **pings search engines** for faster indexing
- and **archives URLs to the Internet Archive** for long-term preservation.

## Project Structure

```
├── config.yaml              # Central configuration
├── mappings.json            # Article → Social post URL mappings (auto-generated)
├── bots/
│   ├── social_bot/          # Social media posting bot
│   │   └── config.json      # Feed & template config
│   └── backup_bot/          # Bear Blog backup bot
├── blog-backup/             # Archived posts (auto-generated)
└── docs/                    # Documentation
```

## Features

### 🤖 Social Media Posting

Automatically posts new blog articles to **Mastodon** and **Bluesky** with customizable templates, rich text formatting, and image support.

**How it works:**
- Monitors your RSS feed for new articles
- Formats posts using templates with placeholders (`{title}`, `{content}`, `{link}`)
- Posts to your configured social media accounts
- Tracks posted articles to prevent duplicates

**Configuration:**
- Set up feeds and templates in `bots/social_bot/config.json`
- Configure Mastodon instance in `config.yaml`
- Add credentials as GitHub Secrets (`BSKY_HANDLE`, `BSKY_PW`, `MASTO_TOKEN`)

→ [Full Documentation](docs/SOCIAL_BOT.md)

---

### 💾 Automatic Backup

Creates a complete backup of your Bear Blog as Markdown files with images, stored directly in this repository.

**What gets backed up:**
- All published posts as Markdown files
- All images from your posts
- Post metadata (title, date, slug, etc.)

**Configuration:**
- Set your blog URL in `config.yaml`
- Backups are saved to `blog-backup/` directory

→ [Full Documentation](docs/BACKUP_BOT.md)

---

### 🔍 Search Engine Ping

Notifies search engines (Google, Bing, etc.) immediately when you publish new content for faster indexing.

**How it works:**
- Uses IndexNow protocol to ping search engines
- Submits new article URLs after posting to social media
- No configuration needed (optional: add `INDEXNOW_KEY` secret for tracking)

---

### 📚 Web Archive Integration

Automatically submits new articles to the [Internet Archive](https://web.archive.org) for permanent preservation.

**Why archive:**
- 📚 Permanent preservation even if your site goes down
- 📖 Historical record of your content at publication time
- 🔗 Citable archived versions for researchers
- 💾 Additional backup layer beyond your blog

**Configuration:**
```yaml
web_archive:
  enabled: true  # Set to false to disable
```

**How it works:**
- After posting to social media, the URL is submitted to web.archive.org
- Creates a permanent snapshot of your content
- Runs asynchronously (doesn't block posting)
- No authentication required

---

## Setup your own (Bear) Blog Automation

Want to use this for your blog? Here's the path:

1. **Fork this repo**
2. **Configure Social Bot** → Set up feeds, templates & secrets ([see above](#-social-media-posting) or [full docs](docs/SOCIAL_BOT.md))
3. **Configure Backup Bot** → Set up automatic backups ([see above](#-automatic-backup) or [full docs](docs/BACKUP_BOT.md)) *(optional)*
4. **Set up Cloudflare Worker** → Enable instant triggering (<1 minute delay) ([docs](docs/CLOUDFLARE_WORKER.md)) *(optional)*

## Author & License

- Made by [René Fischer](https://fischr.org) to automate [fischr.org](https://fischr.org).
- License: [WTFPL](https://www.wtfpl.net/) — Do what you want. I couldn't care less :)
