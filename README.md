# 🐻 (Bear) Blog Automation for fischr.org

Hey and welcome 👋🏼 This is the powerhouse behind my [Bear Blog](https://bearblog.dev)-powered website [fischr.org](https://fischr.org). Whenever I publish a new article, this repository automatically

- **posts the article to Mastodon and Bluesky**, with an individual template based on the content
- **backs up everything** as Markdown files with images right here in this repo
- **pings search engines** for faster indexing
- **archives URLs to the Internet Archive** for long-term preservation
- and **collects webmentions** from other blogs linking to your articles.
- plus **checks blog posts for broken links** and opens issues when found.

## Project Structure

```
├── config.yaml              # Central configuration
├── mappings.json            # Article → Social post URL mappings (auto-generated)
├── webmentions.json         # Blog webmentions collection (auto-generated)
├── bots/
│   ├── social_bot/          # Social media posting bot
│   │   └── config.json      # Feed & template config
│   ├── backup_bot/          # Bear Blog backup bot
│   ├── link_checker/        # Broken link checker
│   └── webmentions/         # Webmentions collection bot
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

**Automatic Error Recovery:**

If posting fails on one platform (e.g., Mastodon is down) but succeeds on another (e.g., Bluesky), the bot automatically retries the failed platform:
- ⏰ **Retry Schedule:** Default: 1h, 4h, 12h (configurable in `config.yaml`)
- 🔄 **Max Retries:** 3 attempts (configurable)
- 🧠 **Smart Error Detection:** Only retries temporary errors (500, 503, timeouts), skips permanent errors (401, 403)
- 📋 **GitHub Issues:** Creates an issue if all retries are exhausted

Configure retry behavior in `config.yaml`:
```yaml
social:
  retry_queue:
    retry_delays_hours: [1, 4, 12]  # Or [0.5, 2, 6] for faster retries
    max_retries: 3                   # Or 0 to disable retries
```

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

### 🔗 Webmentions Collection

Automatically collects webmentions from traditional blog posts that link to your articles using [webmention.io](https://webmention.io).

**What are webmentions:**
Webmentions are the modern web's way of tracking who links to your content - think of them as backlinks or pingbacks that follow the W3C standard.

**How it works:**
- Fetches mentions from webmention.io API every 6 hours
- **Filters out social media** (Mastodon, Bluesky, Twitter) - those are already in `mappings.json`
- Stores only traditional blog mentions in `webmentions.json`
- Incremental updates (only fetches new mentions)

**Setup:**
1. Sign up at [webmention.io](https://webmention.io) with your domain
2. Add the webmention endpoint to your site's HTML `<head>`
3. Add GitHub secrets: `WEBMENTION_IO_TOKEN` and `BEARBLOG_DOMAIN`
4. The workflow runs automatically every 6 hours

**Configuration:**
```yaml
webmentions:
  enabled: true
  excluded_domains:
    - mastodon.social  # Already tracked in mappings.json
    - bsky.app          # Already tracked in mappings.json
    # Add more as needed
```

→ [Full Documentation](bots/webmentions/README.md)

---

### 🧭 Broken Link Checker

Automatically scans your backed up posts for broken links and creates a GitHub Issue with the article URL and failing link.

**How it works:**
- Parses links from `blog-backup/*/index.md`
- Checks each external URL (HEAD with GET fallback)
- Creates a GitHub Issue when broken links are found

**Configuration:**
```yaml
link_checker:
  enabled: true
  timeout_seconds: 10
  max_workers: 8
  user_agent: "bearblog-link-checker/1.0"
```

**Triggering:**
- Runs automatically after the Backup Bot
- Runs weekly via cron

→ [Full Documentation](docs/LINK_CHECKER.md)

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
