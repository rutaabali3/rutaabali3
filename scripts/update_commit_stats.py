#!/usr/bin/env python3
"""Generate a profile SVG with four real GitHub commit metrics."""
from __future__ import annotations

import collections
import datetime as dt
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
    items: list[dict] = []
    for page in range(1, 11):
        params = urllib.parse.urlencode({
            "q": query,
            "per_page": "100",
            "page": str(page),
            "sort": "committer-date",
            "order": "desc",
        })
        request = urllib.request.Request(f"{API}?{params}")
        request.add_header("Accept", "application/vnd.github+json")
        request.add_header("X-GitHub-Api-Version", "2022-11-28")
        if TOKEN:
            request.add_header("Authorization", f"Bearer {TOKEN}")
        with urllib.request.urlopen(request, timeout=30) as response:
            batch = json.load(response).get("items", [])
        items.extend(batch)
        if len(batch) < 100:
            break
    return items


def parse_date(item: dict) -> dt.datetime | None:
    value = item.get("commit", {}).get("committer", {}).get("date")
    if not value:
        return None
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(dt.timezone.utc)


def longest_run(dates: set[dt.date]) -> int:
    best = 0
    for day in dates:
        if day - dt.timedelta(days=1) in dates:
            continue
        run = 1
        while day + dt.timedelta(days=run) in dates:
            run += 1
        best = max(best, run)
    return best


def card(x: int, color: str, label: str, value: int, detail: str) -> str:
    return f'''  <rect x="{x}" y="82" width="204" height="154" rx="12" fill="#100b22" stroke="#49306d"/>
  <circle cx="{x + 28}" cy="116" r="12" fill="{color}" opacity=".22"/>
  <circle cx="{x + 28}" cy="116" r="5" fill="{color}"/>
  <text x="{x + 52}" y="121" fill="#dfc2ff" font-family="Segoe UI,Arial,sans-serif" font-size="13" font-weight="600">{label}</text>
  <text x="{x + 24}" y="174" fill="#f5eaff" font-family="Segoe UI,Arial,sans-serif" font-size="34" font-weight="700">{value}</text>
  <text x="{x + 24}" y="202" fill="#c4acd9" font-family="Segoe UI,Arial,sans-serif" font-size="12">{detail}</text>'''


def main() -> None:
    start_24h = NOW - dt.timedelta(hours=24)
    start_history = NOW - dt.timedelta(days=3650)
    recent = api_search(f"author:{OWNER} committer-date:>={start_24h:%Y-%m-%dT%H:%M:%SZ}")
    history = api_search(f"author:{OWNER} committer-date:>={start_history:%Y-%m-%dT%H:%M:%SZ}")
    dates = [item_date.date() for item in history if (item_date := parse_date(item))]
    date_set = set(dates)
    per_day = collections.Counter(dates)

    current_streak = 0
    day = NOW.date()
    if day not in date_set and (day - dt.timedelta(days=1)) in date_set:
        day -= dt.timedelta(days=1)
    while day in date_set:
        current_streak += 1
        day -= dt.timedelta(days=1)

    values = {
        "last_24h": len(recent),
        "current_streak": current_streak,
        "most_in_day": max(per_day.values(), default=0),
        "longest_streak": longest_run(date_set),
    }
    output = f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="270" viewBox="0 0 900 270" role="img" aria-label="Commit activity statistics">
  <defs>
    <linearGradient id="bg" x1="0" x2="1" y1="0" y2="1"><stop stop-color="#090714"/><stop offset="1" stop-color="#21113d"/></linearGradient>
  </defs>
  <rect width="900" height="270" rx="16" fill="url(#bg)" stroke="#5b3b8a"/>
  <text x="30" y="34" fill="#f5eaff" font-family="Segoe UI,Arial,sans-serif" font-size="20" font-weight="700">Commit activity</text>
  <text x="30" y="58" fill="#c4acd9" font-family="Segoe UI,Arial,sans-serif" font-size="12">Live metrics from GitHub · refreshed daily</text>
{card(24, '#a855f7', 'Last 24 hours', values['last_24h'], 'commits')}
{card(240, '#c084fc', 'Current streak', values['current_streak'], 'consecutive days')}
{card(456, '#8b5cf6', 'Most in one day', values['most_in_day'], 'commits on best day')}
{card(672, '#f0abfc', 'Longest streak', values['longest_streak'], 'consecutive days')}
</svg>'''
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(output, encoding="utf-8")


if __name__ == "__main__":
    main()
