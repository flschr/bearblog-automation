/**
 * Cloudflare Worker: RSS Feed Monitor
 *
 * This worker monitors RSS feeds for changes and triggers GitHub Actions
 * when new content is detected. It uses ETag/Last-Modified headers for
 * efficient change detection.
 *
 * Setup Instructions:
 * 1. Create a new Cloudflare Worker at https://workers.cloudflare.com
 * 2. Copy this code into the worker editor
 * 3. Set the following environment variables in Worker settings:
 *    - GITHUB_TOKEN: Personal Access Token with 'repo' scope
 *    - GITHUB_OWNER: Your GitHub username (e.g., "flschr")
 *    - GITHUB_REPO: Your repository name (e.g., "bearblog-automation")
 *    - RSS_FEED_URLS: Comma-separated list of RSS feed URLs to monitor
 * 4. Add a Cron Trigger (e.g., "*/10 * * * *" for every 10 minutes)
 * 5. Deploy the worker
 */

// Configuration via environment variables
const CONFIG = {
  GITHUB_API: 'https://api.github.com',
  DISPATCH_EVENT_TYPE: 'rss_feed_update',
  REQUEST_TIMEOUT: 10000,
};

/**
 * Main handler for scheduled triggers
 */
export default {
  async scheduled(event, env, ctx) {
    console.log('RSS Monitor: Starting scheduled check');

    try {
      await checkFeeds(env);
    } catch (error) {
      console.error('Error in scheduled handler:', error);
    }
  },

  /**
   * HTTP handler for manual testing
   * Visit worker URL to manually trigger a check
   */
  async fetch(request, env, ctx) {
    if (request.method === 'GET') {
      try {
        const result = await checkFeeds(env);
        return new Response(JSON.stringify(result, null, 2), {
          headers: { 'Content-Type': 'application/json' },
        });
      } catch (error) {
        return new Response(JSON.stringify({ error: error.message }), {
          status: 500,
          headers: { 'Content-Type': 'application/json' },
        });
      }
    }

    return new Response('RSS Feed Monitor - Use GET to test', { status: 200 });
  },
};

/**
 * Check all configured RSS feeds for changes
 */
async function checkFeeds(env) {
  const { GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO, RSS_FEED_URLS } = env;

  // Validate configuration
  if (!GITHUB_TOKEN || !GITHUB_OWNER || !GITHUB_REPO || !RSS_FEED_URLS) {
    throw new Error('Missing required environment variables');
  }

  const feedUrls = RSS_FEED_URLS.split(',').map(url => url.trim());
  const results = {
    checked: [],
    changed: [],
    triggered: false,
    errors: [],
  };

  console.log(`Checking ${feedUrls.length} feed(s)`);

  // Check each feed
  for (const feedUrl of feedUrls) {
    try {
      const hasChanged = await checkFeedChanged(feedUrl, env);

      results.checked.push(feedUrl);

      if (hasChanged) {
        console.log(`Feed changed: ${feedUrl}`);
        results.changed.push(feedUrl);
      } else {
        console.log(`Feed unchanged: ${feedUrl}`);
      }
    } catch (error) {
      console.error(`Error checking feed ${feedUrl}:`, error);
      results.errors.push({ feed: feedUrl, error: error.message });
    }
  }

  // If any feed changed, trigger GitHub Actions
  if (results.changed.length > 0) {
    try {
      await triggerGitHubActions(GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO, results.changed);
      results.triggered = true;
      console.log('GitHub Actions triggered successfully');
    } catch (error) {
      console.error('Error triggering GitHub Actions:', error);
      results.errors.push({ action: 'trigger', error: error.message });
    }
  }

  return results;
}

/**
 * Check if a feed has changed using HEAD request and KV storage
 */
async function checkFeedChanged(feedUrl, env) {
  try {
    // Make HEAD request to get headers
    const response = await fetch(feedUrl, {
      method: 'HEAD',
      headers: {
        'User-Agent': 'RSS-Monitor/1.0',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const newETag = response.headers.get('etag') || '';
    const newLastModified = response.headers.get('last-modified') || '';

    // Get cached headers from KV storage
    const cacheKey = `feed:${feedUrl}`;
    const cachedData = await env.RSS_CACHE?.get(cacheKey, { type: 'json' });

    // If no cache, assume changed and store new headers
    if (!cachedData) {
      await env.RSS_CACHE?.put(cacheKey, JSON.stringify({
        etag: newETag,
        lastModified: newLastModified,
        lastCheck: new Date().toISOString(),
      }));
      return true; // First check, assume changed
    }

    // Compare ETag (more reliable)
    if (newETag && cachedData.etag) {
      if (newETag === cachedData.etag) {
        return false; // No change
      }
    }

    // Compare Last-Modified
    if (newLastModified && cachedData.lastModified) {
      if (newLastModified === cachedData.lastModified) {
        return false; // No change
      }
    }

    // Headers differ or missing - assume changed
    await env.RSS_CACHE?.put(cacheKey, JSON.stringify({
      etag: newETag,
      lastModified: newLastModified,
      lastCheck: new Date().toISOString(),
    }));

    return true;
  } catch (error) {
    console.error(`Error checking feed ${feedUrl}:`, error);
    // On error, assume changed to avoid missing updates
    return true;
  }
}

/**
 * Trigger GitHub Actions via repository_dispatch
 */
async function triggerGitHubActions(token, owner, repo, changedFeeds) {
  const url = `${CONFIG.GITHUB_API}/repos/${owner}/${repo}/dispatches`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/vnd.github+json',
      'User-Agent': 'RSS-Monitor/1.0',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      event_type: CONFIG.DISPATCH_EVENT_TYPE,
      client_payload: {
        feeds: changedFeeds,
        triggered_at: new Date().toISOString(),
      },
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`GitHub API error: ${response.status} - ${errorText}`);
  }

  return true;
}
