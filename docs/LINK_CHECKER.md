# Link Checker

The Link Checker scans your backed-up blog posts for broken links and creates GitHub Issues when it finds any.

---

## How It Works

1. **Load Posts**: Reads all `blog-backup/*/index.md` files
2. **Extract Links**: Parses external HTTP/HTTPS links from Markdown
3. **Check Links**: Tests each unique link with HEAD request (GET fallback)
4. **Report**: Writes results to `bots/linkcheck_bot/broken_links.json`
5. **Create Issue**: GitHub Actions workflow creates an issue with broken links and deletes the report

**Smart Detection:**
- Uses HEAD requests first (faster)
- Falls back to GET if HEAD fails
- Follows redirects automatically
- Handles timeouts gracefully

---

## Configuration

### Central Config (`config.yaml`)

```yaml
blog:
  site_url: "https://your-domain.com"

link_checker:
  enabled: true
  timeout_seconds: 10
  max_workers: 8
  user_agent: "bearblog-link-checker/1.0"
```

| Option | Default | Description |
|--------|---------|-------------|
| `blog.site_url` | — | Your blog URL (used for article URLs in reports) |
| `link_checker.enabled` | `true` | Enable/disable link checking |
| `link_checker.timeout_seconds` | `10` | Request timeout in seconds |
| `link_checker.max_workers` | `8` | Concurrent link checks |
| `link_checker.user_agent` | `bearblog-link-checker/1.0` | User agent for requests |

---

## Triggering

The link checker runs automatically in three scenarios:

1. **After Backup Bot** (`workflow_run`): Checks links whenever backup completes
2. **Weekly Schedule** (`cron`): Every Monday at 03:00 UTC
3. **Manual Trigger**: Via GitHub Actions → Run workflow

---

## GitHub Issues

When broken links are found, an issue is created with:

**Issue Content:**
- Article title and URL
- Broken link URL
- HTTP status code or error message
- Timestamp

**Example:**
```
🔗 Broken links found in blog posts

### Article: My Blog Post
- URL: https://fischr.org/my-blog-post/
- Broken link: https://example.com/missing-page
- Status: 404 Not Found
```

---

## Related Documentation

- [Backup Bot](BACKUP_BOT.md) - Creates the backups that are checked
- [Social Bot](SOCIAL_BOT.md) - Automatic social media posting
