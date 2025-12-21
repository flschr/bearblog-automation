# Bear Blog Automation

Automates social media posting and backups for [Bear Blog](https://bearblog.dev).

**Features:**
- **Social Bot**: Posts new articles to BlueSky & Mastodon with images, hashtags, and rich text
- **Backup Bot**: Archives all posts as Markdown with images to this repository
- **SEO**: Automatic IndexNow submission for faster search engine indexing

---

## Quick Start (Fork This Repo)

### 1. Fork & Edit `config.yaml`

```yaml
blog:
  bearblog_username: "your-username"

social:
  mastodon_instance: "https://mastodon.social"
```

### 2. Configure Feeds

Edit `social_bot/config.json` for your RSS feeds. See [Configuration Guide](docs/CONFIGURATION.md).

### 3. Add GitHub Secrets

Go to **Settings → Secrets → Actions** and add:

| Secret | Description |
|--------|-------------|
| `BSKY_HANDLE` | BlueSky handle (e.g., `user.bsky.social`) |
| `BSKY_PW` | BlueSky App Password |
| `MASTO_TOKEN` | Mastodon Access Token |
| `INDEXNOW_KEY` | *(optional)* IndexNow API key |
| `BEAR_COOKIE` | *(optional)* `sessionid=...` for backups |

### 4. Enable Actions

Go to **Actions** tab → Enable workflows.

---

## Documentation

- [Feed Configuration & Templates](docs/CONFIGURATION.md)
- [Cloudflare Worker Setup](docs/CLOUDFLARE_WORKER.md) *(optional, for efficient triggering)*

---

## Project Structure

```
├── config.yaml           # Central config (edit when forking)
├── social_bot/           # Social media automation
│   ├── config.json       # Feed configurations
│   └── cloudflare-worker # Optional external trigger
├── backup_bot/           # Blog backup to Markdown
├── blog_posts/           # Archived posts
└── docs/                 # Documentation
```

---

## License

[WTFPL](https://www.wtfpl.net/) - Do what you want.

Created by [René Fischer](https://fischr.org) for automating fischr.org.
