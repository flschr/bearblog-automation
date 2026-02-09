# Webmentions Collection Bot

This bot collects webmentions from traditional blog posts linking to your BearBlog articles using the [webmention.io](https://webmention.io) service.

## What are Webmentions?

Webmentions are a W3C standard protocol that allows one website to notify another that it has been linked to or mentioned. Think of them as "backlinks" or "pingbacks" for the modern web.

## Key Features

- **Blog-Only Collection**: Tracks only traditional blog webmentions
- **Social Media Filtering**: Automatically excludes social media platforms (Mastodon, Bluesky, Twitter, etc.) since those are already tracked in `mappings.json` by the social bot
- **Incremental Updates**: Only fetches new mentions since the last run
- **Thread-Safe**: Uses file locking to prevent data corruption
- **Automated**: Runs every 6 hours via GitHub Actions

## Setup Instructions

### 1. Set Up webmention.io Account

1. Go to [webmention.io](https://webmention.io/)
2. Sign in with your domain
3. Get your API token from the dashboard
4. Add the following to your website's HTML `<head>` section:

```html
<link rel="webmention" href="https://webmention.io/YOUR-DOMAIN/webmention" />
<link rel="pingback" href="https://webmention.io/YOUR-DOMAIN/xmlrpc" />
```

Replace `YOUR-DOMAIN` with your actual domain (e.g., `fischr.org`).

### 2. Configure GitHub Secrets

Add the following secrets to your GitHub repository:

1. Go to your repository **Settings** → **Secrets and variables** → **Actions**
2. Add these secrets:
   - `WEBMENTION_IO_TOKEN`: Your API token from webmention.io dashboard
   - `BEARBLOG_DOMAIN`: Your BearBlog domain (e.g., `fischr.org`)

### 3. Enable the Workflow

The workflow is automatically enabled once you merge this feature branch. It will:
- Run every 6 hours automatically
- Can be triggered manually from the Actions tab

## How It Works

### Data Flow

1. **Fetch**: Retrieves mentions from webmention.io API for your domain
2. **Filter**: Excludes social media sources (already tracked elsewhere)
3. **Process**: Organizes mentions by target URL
4. **Store**: Saves to `webmentions.json` in the repository root
5. **Commit**: Automatically commits changes to the repository

### Output Format

The `webmentions.json` file is structured as follows:

```json
{
  "https://fischr.org/article-url/": {
    "target": "https://fischr.org/article-url/",
    "mentions": [
      {
        "source": "https://example-blog.com/post-linking-to-you/",
        "type": "mention",
        "published": "2026-01-08T12:00:00Z",
        "author": {
          "name": "Jane Blogger",
          "url": "https://example-blog.com/"
        },
        "title": "Great article about...",
        "content": "I found this interesting article...",
        "fetched_at": "2026-01-08T14:30:00Z"
      }
    ]
  }
}
```

### Social Media Filtering

The bot automatically excludes mentions from:
- Mastodon instances (including custom instances)
- Bluesky (bsky.app)
- Twitter/X
- Facebook, Instagram, Threads
- LinkedIn

These are excluded because:
1. They're already tracked in `mappings.json` by the social bot
2. They're not traditional blog webmentions
3. This prevents duplicate tracking

## Configuration

Edit `config.yaml` to customize the webmentions settings:

```yaml
webmentions:
  enabled: true
  excluded_domains:
    - mastodon.social
    - chaos.social
    - bsky.app
    # Add more domains as needed
```

## Manual Triggering

You can manually trigger the webmentions fetch:

1. Go to **Actions** tab in your repository
2. Select **Fetch Webmentions** workflow
3. Click **Run workflow** button

## Troubleshooting

### No mentions appearing?

1. **Check webmention.io setup**: Verify the `<link>` tags are in your website's HTML
2. **Verify API token**: Make sure `WEBMENTION_IO_TOKEN` secret is set correctly
3. **Check domain**: Ensure `BEARBLOG_DOMAIN` matches your webmention.io account
4. **Wait for mentions**: Other sites need to send webmentions to your endpoint first

### Workflow failing?

1. Check the Actions tab for error logs
2. Verify both secrets are set correctly
3. Ensure webmention.io service is accessible

### Social media mentions still appearing?

If you see social media mentions that shouldn't be there:
1. Edit `config.yaml` and add the domain to `excluded_domains`
2. Or edit `bots/webmentions_bot/fetch_webmentions.py` to add it to `EXCLUDED_SOCIAL_DOMAINS`

## File Structure

```
bots/webmentions_bot/
├── README.md                    # This file
└── fetch_webmentions.py         # Main webmentions fetcher script

.github/workflows/
└── fetch-webmentions.yml        # GitHub Actions workflow

webmentions.json                 # Output file (at repository root)
```

## Dependencies

- `requests`: HTTP requests to webmention.io API
- `PyYAML`: Configuration file parsing
- Shared utilities from `bots/shared.py`

## Development

To test locally:

```bash
export WEBMENTION_IO_TOKEN="your-token"
export BEARBLOG_DOMAIN="your-domain.com"
python bots/webmentions_bot/fetch_webmentions.py
```

## Related Features

- **Social Bot**: Tracks Mastodon and Bluesky mentions in `mappings.json`
- **Backup Bot**: Archives blog content for preservation

## Resources

- [webmention.io](https://webmention.io/) - Service homepage
- [W3C Webmention Spec](https://www.w3.org/TR/webmention/) - Technical specification
- [IndieWeb Wiki](https://indieweb.org/Webmention) - Community documentation
