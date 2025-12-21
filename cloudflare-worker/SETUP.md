# Cloudflare Worker Setup: RSS Feed Monitor

This guide shows you how to set up the Cloudflare Worker to monitor your RSS feeds and trigger GitHub Actions only when new content is published.

## Benefits

✅ **Efficient**: Only runs GitHub Actions when RSS feed actually changes
✅ **Fast**: Cloudflare Workers are extremely fast and reliable
✅ **Free**: 100,000 requests/day on free plan (more than enough)
✅ **No Domain Required**: Works without owning a domain or using Cloudflare's proxy

---

## Step 1: Create GitHub Personal Access Token

1. Go to https://github.com/settings/tokens
2. Click **"Generate new token (classic)"**
3. Give it a name: `RSS Monitor Worker`
4. Select scope: **`repo`** (full control of private repositories)
5. Click **"Generate token"**
6. **Copy the token** (you won't see it again!)

---

## Step 2: Create Cloudflare Worker

1. Sign up for a free Cloudflare account at https://dash.cloudflare.com/sign-up
2. Go to **Workers & Pages** in the sidebar
3. Click **"Create application"** → **"Create Worker"**
4. Give it a name: `rss-monitor` (or anything you like)
5. Click **"Deploy"** (we'll add code in next step)

---

## Step 3: Add Worker Code

1. After deployment, click **"Edit code"** button
2. **Delete** all existing code
3. **Copy** the entire content from `rss-monitor.js`
4. **Paste** it into the worker editor
5. Click **"Save and Deploy"**

---

## Step 4: Create KV Namespace (for caching)

1. Go back to **Workers & Pages** → **KV**
2. Click **"Create namespace"**
3. Name it: `RSS_CACHE`
4. Click **"Add"**

---

## Step 5: Configure Environment Variables

1. Go to your worker → **Settings** → **Variables**
2. Add the following **Environment Variables**:

| Variable Name | Value | Example |
|--------------|-------|---------|
| `GITHUB_TOKEN` | Your GitHub Personal Access Token | `ghp_xxxxxxxxxxxx` |
| `GITHUB_OWNER` | Your GitHub username | `flschr` |
| `GITHUB_REPO` | Your repository name | `bearblog-automation` |
| `RSS_FEED_URLS` | Comma-separated RSS feed URLs | `https://fischr.org/feed/` |

3. Click **"Save"** after each variable

---

## Step 6: Bind KV Namespace

1. Still in **Settings** → scroll to **KV Namespace Bindings**
2. Click **"Add binding"**
3. Variable name: `RSS_CACHE`
4. KV namespace: Select `RSS_CACHE` (the one you created)
5. Click **"Save"**

---

## Step 7: Add Cron Trigger

1. Go to **Triggers** tab
2. Scroll to **Cron Triggers**
3. Click **"Add Cron Trigger"**
4. Enter schedule: `*/10 * * * *` (every 10 minutes)
   - Or `*/15 * * * *` for every 15 minutes
   - Or `*/5 * * * *` for every 5 minutes (more aggressive)
5. Click **"Add Trigger"**

### Cron Schedule Examples

| Schedule | Description |
|----------|-------------|
| `*/5 * * * *` | Every 5 minutes |
| `*/10 * * * *` | Every 10 minutes (recommended) |
| `*/15 * * * *` | Every 15 minutes |
| `*/30 * * * *` | Every 30 minutes |

---

## Step 8: Test the Worker

### Option A: Manual Test via URL

1. Go to your worker's **Overview** page
2. Copy the worker URL (e.g., `rss-monitor.your-subdomain.workers.dev`)
3. Open it in your browser
4. You should see JSON output showing the check results

### Option B: Test via Cron

1. Wait for the next scheduled run (check the time)
2. Go to **Logs** → **Begin log stream**
3. Watch for log entries showing feed checks

---

## Step 9: Disable GitHub Actions Cron (Optional)

Once the Cloudflare Worker is running successfully, you can disable the GitHub Actions cron schedule:

Edit `.github/workflows/social_bot.yml`:

```yaml
on:
  # schedule:
  #   - cron: '*/50 * * * *' # Disabled - using Cloudflare Worker instead
  workflow_dispatch: # Keep for manual trigger
  repository_dispatch: # Keep for Cloudflare Worker trigger
    types: [rss_feed_update]
```

**Note:** Keep `workflow_dispatch` for manual testing and `repository_dispatch` for the worker!

---

## Monitoring & Debugging

### View Worker Logs

1. Go to your worker → **Logs**
2. Click **"Begin log stream"**
3. Watch real-time logs of feed checks and triggers

### Check GitHub Actions

1. Go to your GitHub repository → **Actions** tab
2. You should see workflow runs triggered by `repository_dispatch`
3. Look for the event: `rss_feed_update`

### Test Trigger Manually

Visit your worker URL to manually trigger a check:
```
https://rss-monitor.your-subdomain.workers.dev
```

---

## Troubleshooting

### Worker triggers but GitHub Actions don't run

- Check that `GITHUB_TOKEN` has `repo` scope
- Verify `GITHUB_OWNER` and `GITHUB_REPO` are correct
- Ensure workflow has `repository_dispatch` trigger configured

### Worker always reports "changed"

- Check that KV namespace is properly bound as `RSS_CACHE`
- View KV storage to see if cache entries are being saved
- Some servers don't send ETag/Last-Modified headers (expected behavior)

### Worker crashes or errors

- Check **Logs** tab for error messages
- Verify all environment variables are set correctly
- Ensure RSS feed URLs are valid and accessible

---

## Cost & Limits

**Free Tier includes:**
- 100,000 requests/day
- 10ms CPU time per request
- Unlimited KV reads
- 1,000 KV writes/day

**For this use case:**
- Cron every 10 min = 144 requests/day (well within limits)
- KV writes only when feeds change (minimal)

**You will NOT exceed free tier limits with this setup!**

---

## How It Works

```
Cloudflare Worker (every 10 min)
  ├─ HEAD request to RSS feed (fast, no content download)
  ├─ Check ETag/Last-Modified headers
  ├─ Compare with KV cache
  │
  ├─ If unchanged:
  │   └─ Log "no change" and exit (saves GitHub Actions minutes)
  │
  └─ If changed:
      ├─ Update KV cache
      ├─ Trigger GitHub Actions via repository_dispatch
      └─ GitHub Actions runs social_bot.py
          ├─ Bot also checks ETag/Last-Modified (double-check)
          ├─ Downloads full RSS feed only if needed
          └─ Posts new articles to social media
```

---

## Questions?

Open an issue in the repository if you need help!
