# 🐻 (Bear) Blog Automation for fischr.org

Hey and welcome 👋🏼 This is the automation behind my [Bear Blog](https://bearblog.dev)-powered website [fischr.org](https://fischr.org). Whenever I publish a new article, this repository automatically posts it to social media, pings search engines, and collects webmentions.

## Project Structure

```
├── config.yaml              # Central configuration
├── mappings.json            # Article → Social post URL mappings (auto-generated)
├── webmentions.json         # Blog webmentions collection (auto-generated)
├── bots/
│   ├── social_bot/          # Social media posting bot
│   │   └── config.json      # Feed & template config
│   └── webmentions_bot/     # Webmentions collection bot
├── archive/
│   ├── bots/                # Archived, currently inactive bots (backup/linkcheck)
│   ├── docs/                # Archived docs for inactive bots
│   └── workflows/           # Archived GitHub workflows for inactive bots
└── docs/                    # Active documentation
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

### 🔗 Webmentions Collection

Collects webmentions from traditional blog posts that link to your articles using [webmention.io](https://webmention.io).

**Key features:**
- Filters out social media (already in `mappings.json`)
- Stores only traditional blog mentions
- Runs automatically every 6 hours

→ [Full Documentation](docs/WEBMENTIONS_BOT.md)

---

## Archived (currently inactive)

The following components were moved to `archive/` because they are currently not runnable/reliable in the active setup:

- Backup bot (`archive/bots/backup_bot/`)
- Link checker bot (`archive/bots/linkcheck_bot/`)
- Their workflow files (`archive/workflows/*.yml`)
- Their docs (`archive/docs/`)

---

## Setup your own (Bear) Blog Automation

Want to use this for your blog? Here's the path:

1. **Fork this repo**
2. **Configure Social Bot** → Set up feeds, templates & secrets ([docs](docs/SOCIAL_BOT.md))
3. **Set up Webmentions** → Collect backlinks from other blogs ([docs](docs/WEBMENTIONS_BOT.md)) *(optional)*
4. **Set up Cloudflare Worker** → Enable instant triggering ([docs](docs/CLOUDFLARE_WORKER.md)) *(optional)*

## Author & License

- Made by [René Fischer](https://fischr.org) to automate [fischr.org](https://fischr.org).
- License: [WTFPL](https://www.wtfpl.net/) — Do what you want. I couldn't care less :)
