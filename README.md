# 🐻 (Bear) Blog Automation for fischr.org

Hey and welcome 👋🏼 This is the powerhouse behind my [Bear Blog](https://bearblog.dev)-powered website [fischr.org](https://fischr.org). Whenever I publish a new article, this repository automatically posts it to social media, backs up the content, pings search engines, and collects webmentions.

## Project Structure

```
├── config.yaml              # Central configuration
├── mappings.json            # Article → Social post URL mappings (auto-generated)
├── webmentions.json         # Blog webmentions collection (auto-generated)
├── bots/
│   ├── social_bot/          # Social media posting bot
│   │   └── config.json      # Feed & template config
│   ├── backup_bot/          # Bear Blog backup bot
│   ├── linkcheck_bot/       # Broken link checker
│   └── webmentions_bot/     # Webmentions collection bot
├── blog-backup/             # Archived posts (auto-generated)
└── docs/                    # Documentation
```

## Features

### 🤖 Social Media Posting

Automatically posts new blog articles to **Mastodon** and **Bluesky** with customizable templates, rich text formatting, and image support.

**Key features:**
- RSS feed monitoring with smart filtering
- Customizable post templates
- Automatic retry on partial failures
- Search engine pinging (IndexNow)
- Internet Archive integration

→ [Full Documentation](docs/SOCIAL_BOT.md)

---

### 💾 Automatic Backup

Creates a complete backup of your Bear Blog as Markdown files with images, stored directly in this repository.

**What gets backed up:**
- All published posts as Markdown with frontmatter
- All images referenced in posts
- Optional: Linked files (PDFs, documents, etc.)

→ [Full Documentation](docs/BACKUP_BOT.md)

---

### 🔗 Webmentions Collection

Collects webmentions from traditional blog posts that link to your articles using [webmention.io](https://webmention.io).

**Key features:**
- Filters out social media (already in `mappings.json`)
- Stores only traditional blog mentions
- Runs automatically every 6 hours

→ [Full Documentation](docs/WEBMENTIONS_BOT.md)

---

### 🧭 Broken Link Checker

Scans your backed up posts for broken links and creates GitHub Issues when found.

**Key features:**
- Checks all external links in backups
- Reports article URL and broken link
- Runs weekly and after backups

→ [Full Documentation](docs/LINK_CHECKER.md)

---

## Setup your own (Bear) Blog Automation

Want to use this for your blog? Here's the path:

1. **Fork this repo**
2. **Configure Social Bot** → Set up feeds, templates & secrets ([docs](docs/SOCIAL_BOT.md))
3. **Configure Backup Bot** → Set up automatic backups ([docs](docs/BACKUP_BOT.md)) *(optional)*
4. **Set up Webmentions** → Collect backlinks from other blogs ([docs](docs/WEBMENTIONS_BOT.md)) *(optional)*
5. **Set up Cloudflare Worker** → Enable instant triggering ([docs](docs/CLOUDFLARE_WORKER.md)) *(optional)*

## Author & License

- Made by [René Fischer](https://fischr.org) to automate [fischr.org](https://fischr.org).
- License: [WTFPL](https://www.wtfpl.net/) — Do what you want. I couldn't care less :)
