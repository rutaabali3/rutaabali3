#!/usr/bin/env python3
"""Generate a small profile SVG with recent commit activity and streak data."""
from __future__ import annotations

import datetime as dt
import html
import json
import os
import pathlib
import urllib.parse
import urllib.request

OWNER = os.environ.get("GITHUB_REPOSITORY_OWNER", "rutaabali3")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUTPUT = pathlib.Path("assets/commit-stats.svg")
API = "https://api.github.com/search/commits"
NOW = dt.datetime.now(dt.timezone.utc)


def api_search(query: str) -> list[dict]:
    params = urllib.parse.urlencode({"q": query, "per_page": "100", "sort": "committer-date", "order": "desc"})
    request = urllib.request.Request(f"{API}?{params}")
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    if TOKEN:
        request.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response).get("items", [])


def parse_date(item: dict) -> dt.datetime | None:
    value = item.get("commit", {}).get("committer", {}).get("date")
    if not value:
        return None
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(dt.timezone.utc)


def main() -> None:
    start_24h = NOW - dt.timedelta(hours=24)
    start_90d = NOW - dt.timedelta(days=90)
    recent = api_search(f"author:{OWNER} committer-date:>={start_24h:%Y-%m-%dT%H:%M:%SZ}")
    history = api_search(f"author:{OWNER} committer-date:>={start_90d:%Y-%m-%dT%H:%M:%SZ}")
    dates = {item_date.date() for item in history if (item_date := parse_date(item))}

    streak = 0
    day = NOW.date()
    if day not in dates and (day - dt.timedelta(days=1)) in dates:
        day -= dt.timedelta(days=1)
    while day in dates:
        streak += 1
        day -= dt.timedelta(days=1)

    commits_24h = len(recent)
    output = f'''<svg xmlns="http://www.w3.org/2000/svg" width="760" height="170" viewBox="0 0 760 170" role="img" aria-label="Commit activity statistics">
  <defs>
    <linearGradient id="bg" x1="0" x2="1" y1="0" y2="1"><stop stop-color="#161b22"/><stop offset="1" stop-color="#242938"/></linearGradient>
    <linearGradient id="accent" x1="0" x2="1"><stop stop-color="#58a6ff"/><stop offset="1" stop-color="#a371f7"/></linearGradient>
  </defs>
  <rect width="760" height="170" rx="14" fill="url(#bg)" stroke="#30363d"/>
  <text x="32" y="38" fill="#f0f6fc" font-family="Segoe UI,Arial,sans-serif" font-size="18" font-weight="700">Commit activity</text>
  <text x="32" y="62" fill="#8b949e" font-family="Segoe UI,Arial,sans-serif" font-size="13">Updated automatically every day</text>
  <line x1="380" y1="25" x2="380" y2="145" stroke="#30363d"/>
  <circle cx="70" cy="108" r="18" fill="url(#accent)" opacity=".22"/>
  <text x="70" y="114" text-anchor="middle" fill="#79c0ff" font-family="Segoe UI,Arial,sans-serif" font-size="17">24h</text>
  <text x="112" y="104" fill="#f0f6fc" font-family="Segoe UI,Arial,sans-serif" font-size="28" font-weight="700">{commits_24h}</text>
  <text x="112" y="126" fill="#8b949e" font-family="Segoe UI,Arial,sans-serif" font-size="13">commits in the last 24 hours</text>
  <circle cx="450" cy="108" r="18" fill="#3fb950" opacity=".22"/>
  <text x="450" y="114" text-anchor="middle" fill="#56d364" font-family="Segoe UI,Arial,sans-serif" font-size="17">★</text>
  <text x="492" y="104" fill="#f0f6fc" font-family="Segoe UI,Arial,sans-serif" font-size="28" font-weight="700">{streak}</text>
  <text x="492" y="126" fill="#8b949e" font-family="Segoe UI,Arial,sans-serif" font-size="13">day commit streak</text>
</svg>'''
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(output, encoding="utf-8")


if __name__ == "__main__":
    main()
