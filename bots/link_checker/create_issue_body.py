#!/usr/bin/env python3
"""Create issue body for broken links report."""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

def main():
    report_file = Path("bots/link_checker/broken_links.json")

    if not report_file.exists():
        sys.exit(1)

    report = json.loads(report_file.read_text(encoding="utf-8"))

    if not report:
        sys.exit(0)

    lines = [
        "## Broken Links Detected",
        "",
        "The following broken links were found in blog posts:",
        "",
    ]

    for item in report:
        article = item.get("article_url", "unknown")
        link = item.get("link_url", "unknown")
        status = item.get("status", "unknown")
        lines.append(f"- **Article:** {article}")
        lines.append(f"  - Link: {link}")
        lines.append(f"  - Status: `{status}`")
        lines.append("")

    lines.extend([
        "### Workflow Run",
        f"- **Run ID:** {os.environ.get('RUN_ID', 'unknown')}",
        f"- **Triggered by:** {os.environ.get('EVENT_NAME', 'unknown')}",
        f"- **Timestamp:** {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
    ])

    Path("issue_body.md").write_text("\n".join(lines), encoding="utf-8")

if __name__ == "__main__":
    main()
