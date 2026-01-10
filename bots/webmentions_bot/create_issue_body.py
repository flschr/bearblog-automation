#!/usr/bin/env python3
"""
Create GitHub issue body for new webmentions notifications.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

REPORT_FILE = Path(__file__).parent / "new_mentions.json"
OUTPUT_FILE = Path(__file__).parent / "issue_body.md"


def create_issue_body():
    """Create formatted issue body from new mentions report."""
    if not REPORT_FILE.exists():
        print("No new mentions report found")
        sys.exit(0)

    try:
        with open(REPORT_FILE, 'r', encoding='utf-8') as f:
            new_mentions = json.load(f)
    except Exception as e:
        print(f"Error reading report: {e}")
        sys.exit(1)

    if not new_mentions:
        print("No new mentions in report")
        sys.exit(0)

    mention_count = len(new_mentions)

    # Build issue body
    lines = [
        "## New Webmentions Received",
        "",
        f"You have **{mention_count}** new webmention(s) from other blogs! 🎉",
        ""
    ]

    for i, mention in enumerate(new_mentions, 1):
        lines.append("---")
        lines.append("")
        lines.append(f"### Mention {i}")
        lines.append("")

        # Author
        author_name = mention.get('author', {}).get('name', 'Unknown')
        author_url = mention.get('author', {}).get('url', '')

        if author_url:
            lines.append(f"**From:** {author_name} ([{author_url}]({author_url}))")
        else:
            lines.append(f"**From:** {author_name}")

        # Source and target
        source = mention.get('source', 'Unknown')
        target = mention.get('target', 'Unknown')
        lines.append(f"**Source:** {source}")
        lines.append(f"**Your Article:** {target}")

        # Optional fields
        title = mention.get('title', '')
        if title:
            lines.append(f"**Title:** {title}")

        published = mention.get('published', '')
        if published:
            try:
                # Try to format the date nicely
                dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                formatted_date = dt.strftime('%Y-%m-%d %H:%M UTC')
                lines.append(f"**Published:** {formatted_date}")
            except:
                lines.append(f"**Published:** {published}")

        content = mention.get('content', '')
        if content:
            lines.append("")
            lines.append("**Excerpt:**")
            lines.append(f"> {content}")

        lines.append("")

    # Footer
    lines.extend([
        "---",
        "",
        "View all webmentions in the [`webmentions.json`](../../webmentions.json) file in the repository.",
        "",
        "**Tip:** You can disable these notifications by setting `notify_on_new_mentions: false` in `config.yaml`.",
        ""
    ])

    # Write to output file
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f"Created issue body with {mention_count} mention(s)")
    except Exception as e:
        print(f"Error writing issue body: {e}")
        sys.exit(1)


if __name__ == '__main__':
    create_issue_body()
