# Social Bot

The Social Bot automatically posts new blog entries from your RSS feeds to Bluesky and Mastodon.

---

## How It Works

1. Monitors your configured RSS feeds
2. Detects new posts using ETag/Last-Modified headers
3. Filters posts based on include/exclude rules
4. Formats posts using customizable templates
5. Posts to Bluesky and/or Mastodon with rich text and link cards
6. Submits URLs to search engines via IndexNow
7. Archives URLs to the Internet Archive for long-term preservation (optional)

---

## Configuration

### Central Config (`config.yaml`)

```yaml
social:
  mastodon_instance: "https://mastodon.social"
  max_article_age_days: 7  # Optional: Skip articles older than X days

  # Retry queue for partial posting failures
  retry_queue:
    retry_delays_hours: [1, 4, 12]  # Retry after 1h, 4h, 12h
    max_retries: 3                   # Max attempts before giving up

web_archive:
  enabled: true  # Optional: Archive URLs to web.archive.org
```

| Option | Default | Description |
|--------|---------|-------------|
| `mastodon_instance` | — | Your Mastodon instance URL |
| `max_article_age_days` | `0` (disabled) | Skip articles older than X days (see [Article Age Limit](#article-age-limit)) |
| `retry_queue.retry_delays_hours` | `[1, 4, 12]` | Retry schedule in hours (see [Automatic Retry Queue](#automatic-retry-queue)) |
| `retry_queue.max_retries` | `3` | Max retry attempts before creating GitHub issue (see [Automatic Retry Queue](#automatic-retry-queue)) |
| `web_archive.enabled` | `false` | Automatically submit URLs to Internet Archive (see [Web Archive Integration](#web-archive-integration)) |

### Feed Config (`bots/social_bot/config.json`)

Each feed is configured as an object in the JSON array:

```json
[
  {
    "name": "Blog Articles",
    "url": "https://yourblog.com/feed/",
    "include": ["blog"],
    "exclude": ["draft"],
    "include_images": true,
    "template": "New post: {title}\n\n{link}",
    "targets": ["bluesky", "mastodon"]
  }
]
```

#### Configuration Options

| Option | Required | Description |
|--------|----------|-------------|
| `name` | Yes | Descriptive name (used in logs) |
| `url` | Yes | RSS feed URL |
| `include` | No | Only posts with these keywords in title/hashtags/categories |
| `exclude` | No | Skip posts with these keywords |
| `include_images` | No | Attach first image with ALT text (`true`/`false`) |
| `template` | Yes | Post format with placeholders |
| `targets` | Yes | Platforms: `["bluesky"]`, `["mastodon"]`, or both |

#### Template Variables

Use these placeholders in the `template` field:

| Variable | Description |
|----------|-------------|
| `{title}` | Post title |
| `{link}` | URL to the blog post |
| `{content}` | Cleaned text content (auto-truncated) |

**Content limits:**
- BlueSky: 300 characters
- Mastodon: 500 characters

**Hashtags:** Added in templates are automatically converted to native rich text on BlueSky.

#### Examples

**Photo Posts**
```json
{
  "name": "Photos",
  "url": "https://yourblog.com/feed?q=photos",
  "include": ["photo"],
  "include_images": true,
  "template": "{content} #photography",
  "targets": ["bluesky", "mastodon"]
}
```

**Blog Articles**
```json
{
  "name": "Blog",
  "url": "https://yourblog.com/feed/",
  "include": ["blog"],
  "exclude": ["draft", "private"],
  "template": "New post: {title}\n\n{link}",
  "targets": ["bluesky", "mastodon"]
}
```

**Movie Reviews**
```json
{
  "name": "Movies",
  "url": "https://yourblog.com/feed?q=movies",
  "template": "Just watched {title}. {link}",
  "targets": ["bluesky"]
}
```

---

## GitHub Secrets

Configure these in **Settings → Secrets → Actions**:

| Secret | Required | Description |
|--------|----------|-------------|
| `BSKY_HANDLE` | Yes | Your BlueSky handle (e.g., `user.bsky.social`) |
| `BSKY_PW` | Yes | BlueSky App Password |
| `MASTO_TOKEN` | Yes | Mastodon Access Token |
| `INDEXNOW_KEY` | No | IndexNow API key for SEO pings |

### Getting Credentials

**BlueSky App Password:**
1. Go to [bsky.app/settings/app-passwords](https://bsky.app/settings/app-passwords)
2. Create a new app password
3. Copy and save as `BSKY_PW`

**Mastodon Access Token:**
1. Go to your instance → Settings → Development
2. Create a new application
3. Copy the access token as `MASTO_TOKEN`

---

## Features

### Rich Text Support
- Hashtags are converted to clickable tags
- Links get proper rich text formatting
- Bluesky posts include link card previews with OG images (handled automatically by Mastodon)

### Smart Filtering
- Include/exclude posts by keywords in title, hashtags/categories
- Attach first image with ALT text (optional)

### Efficiency
- Tracks posted articles to prevent duplicates

### Article Age Limit

When you edit an old article (e.g., change its URL or title), it might appear as "new" to the bot since the URL isn't in the posted articles list. To prevent accidentally re-posting old content, you can set a maximum article age:

```yaml
social:
  max_article_age_days: 7
```

**How it works:**
- The bot checks the article's `published` date from the RSS feed
- Articles older than the configured limit are skipped, even if they haven't been posted before
- This is particularly useful when migrating content or editing old articles
- Set to `0` or remove the setting to disable this check

**Example log output:**
```
Skipping old article (14 days old, max 7): My Old Blog Post
```

### Web Archive Integration

When enabled in `config.yaml`, the bot automatically submits new article URLs to the [Internet Archive](https://web.archive.org) for permanent preservation:

```yaml
web_archive:
  enabled: true  # Set to false to disable
```

**How it works:**
- After successfully posting to social media, the URL is submitted to web.archive.org
- Creates a permanent snapshot of your content
- No authentication required
- Runs asynchronously (doesn't block posting if Archive is slow)

**Benefits:**
- 📚 Permanent preservation even if your site goes down
- 📖 Historical record of your content
- 🔗 Citable archived versions for researchers
- 💾 Additional backup layer

### Automatic Retry Queue

**What is it?**

If posting fails on one platform (e.g., Mastodon returns a 500 error) but succeeds on another (e.g., Bluesky), the article is automatically added to a retry queue. The bot will automatically retry the failed platform on subsequent runs.

**Configuration:**

```yaml
social:
  retry_queue:
    # Retry delays in hours (supports decimals for minutes)
    retry_delays_hours: [1, 4, 12]  # Default: retry after 1h, 4h, 12h

    # Maximum number of retry attempts
    max_retries: 3  # Default: 3 attempts before giving up
```

**Examples:**

**Fast retries** (for time-sensitive posts):
```yaml
retry_delays_hours: [0.25, 1, 4]  # 15 minutes, 1 hour, 4 hours
max_retries: 3
```

**Patient retries** (for less critical posts):
```yaml
retry_delays_hours: [2, 8, 24]  # 2 hours, 8 hours, 24 hours
max_retries: 3
```

**Disable retries** (create GitHub issue immediately):
```yaml
retry_delays_hours: []
max_retries: 0
```

**How it works:**

1. **Initial Failure**: Article posted to Bluesky ✅, Mastodon fails with `500 Internal Server Error` ❌
2. **Queue Addition**: Article marked as posted (Bluesky was successful), Mastodon added to retry queue
3. **Automatic Retry #1** (after 1h): Bot runs → retries Mastodon
   - If success ✅: Removed from queue, done!
   - If failure ❌: Stays in queue, next retry in 4h
4. **Automatic Retry #2** (after 4h): Bot runs → retries Mastodon again
   - If success ✅: Removed from queue, done!
   - If failure ❌: Stays in queue, next retry in 12h
5. **Automatic Retry #3** (after 12h): Bot runs → final retry attempt
   - If success ✅: Removed from queue, done!
   - If failure ❌: Marked as "exhausted" → GitHub issue created

**Smart Error Detection:**

The bot only retries temporary errors:

✅ **Retriable** (automatic retry):
- `500 Internal Server Error`
- `502 Bad Gateway`
- `503 Service Unavailable`
- `504 Gateway Timeout`
- `429 Too Many Requests`
- Connection timeouts/errors

❌ **Non-Retriable** (immediate GitHub issue):
- `400 Bad Request` (invalid request)
- `401 Unauthorized` (wrong credentials)
- `403 Forbidden` (no permission)
- `404 Not Found` (API endpoint missing)
- `422 Unprocessable Entity` (invalid data)

**GitHub Issues:**

The bot creates issues for two scenarios:

1. **Immediate partial failure** (any error): Creates issue with detailed error info
2. **Exhausted retries** (after all attempts fail): Creates issue listing all failed articles

**Monitoring:**

Check the retry queue status:
```bash
# View current queue
cat bots/social_bot/retry_queue.json | jq .

# View exhausted retries only
cat bots/social_bot/retry_queue.json | jq '.[] | select(.next_retry_after == "exhausted")'

# Count entries
cat bots/social_bot/retry_queue.json | jq 'length'
```

### Automatic Issue for Unmatched Articles
When a new article doesn't match any posting configuration, the bot:
1. Generates a detailed matching report showing:
   - Article info (title, link, published date)
   - Detected RSS tags from the feed
   - Each config checked and why it didn't match
2. Creates a GitHub Issue with the full report
3. Suggests possible actions to fix the configuration

This helps diagnose why articles aren't being posted and makes it easier to adjust the filter rules.

---

## Triggering

The bot can be triggered:
- **Manually**: GitHub Actions → Run workflow
- **Webhook**: Via Cloudflare Worker (see [Cloudflare Worker Setup](CLOUDFLARE_WORKER.md))
- **Schedule**: Uncomment cron in workflow file

---

## Related Documentation

- [Backup Bot](BACKUP_BOT.md) - Automatic blog backups
- [Cloudflare Worker](CLOUDFLARE_WORKER.md) - Instant trigger setup
