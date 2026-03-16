# 🐻 (Bear) Blog Automation for fischr.org

Hey and welcome 👋🏼 This is the automation behind my [Bear Blog](https://bearblog.dev)-powered website [fischr.org](https://fischr.org). Whenever I publish or update an article, this repository automatically posts it to social media, creates/updates a full backup from RSS, pings search engines, and collects webmentions.

## Project Structure

```
├── config.yaml                      # Central configuration
├── mappings.json                    # Article → Social post URL mappings (auto-generated)
├── webmentions.json                 # Blog webmentions collection (auto-generated)
├── bots/
│   ├── social_bot/                  # Social media posting bot
│   │   └── config.json              # Feed & template config
│   └── webmentions_bot/             # Webmentions collection bot
├── archive/
│   ├── bots/
│   │   ├── backup_bot/              # Backup bot script + tracking file
│   │   └── linkcheck_bot/           # Link checker bot script + config
│   └── docs/                        # Archived/legacy docs
├── .github/workflows/
│   ├── social_bot.yml               # Main social posting workflow
│   ├── backup_bot.yml               # Backup workflow
│   ├── linkcheck_bot.yml            # Broken link checker workflow
│   └── fetch-webmentions.yml        # Webmentions workflow
└── docs/                            # Active documentation (including link checker)
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

### 💾 RSS Backup Bot

Creates a Git-tracked backup of your Bear Blog posts from RSS, including frontmatter, embedded images, and (optionally) linked files like PDFs.

**Key features:**
- Stores each post as `blog-backup/YYYY-MM-DD-slug/index.md`
- Re-processes entries when RSS content changes (hash-based tracking)
- Concurrent image downloads for faster runs
- Optional whitelist-based linked-file backup
- Triggered weekly, manually, and automatically after social updates

→ [Full Documentation](docs/BACKUP_BOT.md)

---

### 🔗 Broken Link Checker

Checks all external links in your backed-up posts and creates a GitHub issue when broken links are found.

**Key features:**
- Runs automatically after successful backup runs
- Weekly scheduled checks + manual trigger
- Excludes problematic domains and can auto-exclude repeated bot-protection domains
- Uploads a JSON artifact and opens an issue with grouped results

→ [Full Documentation](docs/LINK_CHECKER.md)

---

### 🔗 Webmentions Collection

Collects webmentions from traditional blog posts that link to your articles using [webmention.io](https://webmention.io).

**Key features:**
- Filters out social media (already in `mappings.json`)
- Stores only traditional blog mentions
- Runs automatically every 6 hours

→ [Full Documentation](docs/WEBMENTIONS_BOT.md)

---

## Archived / Legacy

The following components remain in `archive/` as legacy parts:

- Archived workflows (`archive/workflows/*.yml`)
- Legacy docs (`archive/docs/`)

---

## Setup your own (Bear) Blog Automation

Want to use this for your blog? Here's the path:

1. **Fork this repo**
2. **Configure Social Bot** → Set up feeds, templates & secrets ([docs](docs/SOCIAL_BOT.md))
3. **Set up Backup Bot** → Keep a versioned RSS backup of your content ([docs](docs/BACKUP_BOT.md)) *(optional but recommended)*
4. **Set up Webmentions** → Collect backlinks from other blogs ([docs](docs/WEBMENTIONS_BOT.md)) *(optional)*
5. **Set up Cloudflare Worker** → Enable instant triggering ([docs](docs/CLOUDFLARE_WORKER.md)) *(optional)*

## Author & License

- Made by [René Fischer](https://fischr.org) to automate [fischr.org](https://fischr.org).
- License: [WTFPL](https://www.wtfpl.net/) — Do what you want. I couldn't care less :)
