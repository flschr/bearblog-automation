# Auto-exclude domains with bot detection from link checker

## Summary

The link checker now automatically excludes domains that show signs of bot detection or aggressive rate limiting. This prevents false positives and reduces noise in link checking reports.

## Changes

### 1. Automatic Domain Exclusion
When the link checker encounters specific HTTP status codes that indicate bot blocking, it automatically:
- Adds the domain to `bots/linkcheck_bot/excluded_domains.txt`
- Logs the exclusion in `bots/linkcheck_bot/auto_excluded_domains.json`
- Prevents future checks for that domain in the same run

**Status codes that trigger auto-exclusion:**
- `403 Forbidden` - Often indicates bot blocking
- `429 Too Many Requests` - Rate limiting
- `999` - LinkedIn's custom "request denied" code

### 2. Pre-populated Excluded Domains
Added common false positives to `excluded_domains.txt`:
- **Wikipedia & Wikimedia projects** (wikipedia.org, wikimedia.org, wiktionary.org, etc.)
- **Reference sites** (britannica.com, merriam-webster.com)
- **Social media** (linkedin.com, facebook.com, instagram.com, twitter.com, x.com)
- **Cloudflare** (cloudflare.com)

### 3. Simplified Configuration
- Removed `excluded_domains` from `config.yaml` - all exclusions are now managed in `excluded_domains.txt`
- The system only uses `bots/linkcheck_bot/excluded_domains.txt` for exclusions

## Monitoring Auto-Excluded Domains

Check `bots/linkcheck_bot/auto_excluded_domains.json` to see which domains were automatically excluded and when. Each entry includes:
- Domain name
- Original URL that triggered the exclusion
- HTTP status code (reason)
- Timestamp

## Review Process

Periodically review auto-excluded domains to ensure legitimate sites aren't being excluded incorrectly. If a domain was incorrectly excluded:
1. Remove it from `excluded_domains.txt`
2. Manually verify the link is working
3. Consider adjusting the auto-exclusion logic if needed

## Technical Details

- Thread-safe implementation using locks to prevent race conditions
- In-memory tracking prevents duplicate exclusions in the same run
- Domains are normalized (www. prefix removed) for consistency
- Both exact matches and subdomains are excluded
