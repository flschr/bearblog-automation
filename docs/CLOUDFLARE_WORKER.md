# Cloudflare Worker Setup

Use a Cloudflare Worker to trigger the Social Bot **only when RSS feeds actually change**.

**Benefits:**
- More reliable than GitHub Actions cron (no delays or skipped runs)
- More efficient (only runs when RSS changes)
- 100% free (Cloudflare free tier: 100k requests/day)

---

## Setup

### 1. Create GitHub Personal Access Token

1. Go to https://github.com/settings/tokens
2. Click **"Generate new token (classic)"**
3. Name: `RSS Monitor Worker`
4. Scope: **`repo`**
5. Copy the token

### 2. Create Cloudflare Worker

1. Sign up at https://dash.cloudflare.com/sign-up
2. Go to **Workers & Pages** → **Create Worker**
3. Name: `rss-monitor`
4. Click **Deploy**

### 3. Add Worker Code

1. Click **Edit code**
2. Delete all existing code
3. Paste contents from `social_bot/cloudflare-worker/rss-monitor.js`
4. Click **Save and Deploy**

### 4. Create KV Namespace

1. Go to **Workers & Pages** → **KV**
2. Click **Create namespace**
3. Name: `RSS_CACHE`

### 5. Configure Environment Variables

In your worker → **Settings** → **Variables**, add:

| Variable | Value |
|----------|-------|
| `GITHUB_TOKEN` | Your GitHub token |
| `GITHUB_OWNER` | Your GitHub username |
| `GITHUB_REPO` | `bearblog-automation` |
| `RSS_FEED_URLS` | Comma-separated feed URLs |

### 6. Bind KV Namespace

In **Settings** → **KV Namespace Bindings**:
- Variable name: `RSS_CACHE`
- Select the `RSS_CACHE` namespace

### 7. Add Cron Trigger

In **Triggers** → **Cron Triggers**:
- Schedule: `*/10 * * * *` (every 10 minutes)

---

## Disable GitHub Actions Cron (Optional)

Once the worker is running, you can disable the Actions schedule:

```yaml
# .github/workflows/social_bot.yml
on:
  # schedule:
  #   - cron: '*/50 * * * *'  # Disabled - using Cloudflare Worker
  workflow_dispatch:
  repository_dispatch:
    types: [rss_feed_update]
```

---

## How It Works

```
Cloudflare Worker (every 10 min)
  ├─ HEAD request to RSS feed
  ├─ Check ETag/Last-Modified headers
  ├─ Compare with KV cache
  │
  ├─ If unchanged: exit
  │
  └─ If changed:
      ├─ Update KV cache
      └─ Trigger GitHub Actions via repository_dispatch
```

---

## Troubleshooting

**Actions don't run:**
- Check `GITHUB_TOKEN` has `repo` scope
- Verify `GITHUB_OWNER` and `GITHUB_REPO` values

**Always reports "changed":**
- Check KV namespace is bound as `RSS_CACHE`
- Some servers don't send ETag headers (expected)

**View logs:**
- Worker → Logs → Begin log stream
