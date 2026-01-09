# Broken Link Checker

The Broken Link Checker scans your backed-up posts for broken links and opens a GitHub Issue when it finds any.

---

## How It Works

1. Loads all `blog-backup/*/index.md` files
2. Extracts external HTTP/HTTPS links
3. Checks each unique link (HEAD with GET fallback)
4. Writes a report to `bots/linkcheck_bot/broken_links.json`
5. The workflow creates a GitHub Issue and deletes the report file

---

## Configuration

Add the following section to `config.yaml`:

```yaml
blog:
  site_url: "https://your-domain.com"

link_checker:
  enabled: true
  timeout_seconds: 10
  max_workers: 8
  user_agent: "bearblog-link-checker/1.0"
```

`blog.site_url` is used to build article URLs when no canonical URL is set in the frontmatter.

---

## Workflow

The checker runs in two cases:

- **After Backup Bot** (`workflow_run`)
- **Weekly** via cron (every Monday at 03:00 UTC)

You can also run it manually from GitHub Actions.

---

## Output

When broken links are found, a GitHub Issue is created with:

- Article URL
- Broken link URL
- Status (HTTP status or timeout/error)
