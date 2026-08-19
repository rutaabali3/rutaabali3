#!/usr/bin/env python3
"""Generate the reference-style purple commit activity card from real GitHub data."""
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
BG = "#0c0b1b"; PANEL = "#171330"; PANEL_ALT = "#14132f"; BORDER = "#362171"; ACCENT = "#8d5cff"; ACCENT_2 = "#b58cff"; TEXT = "#e5ddff"; MUTED = "#9e94bb"; GRID = "#241b45"
FONT = "DejaVu Sans,Arial,sans-serif"


def api_search(query: str) -> list[dict]:
    items = []
    for page in range(1, 11):
        params = urllib.parse.urlencode({"q": query, "per_page": "100", "page": str(page), "sort": "committer-date", "order": "desc"})
        request = urllib.request.Request(f"{API}?{params}", headers={"Accept": "application/vnd.github+json", "User-Agent": "rutaabali3-commit-card", **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {})})
        with urllib.request.urlopen(request, timeout=30) as response: batch = json.load(response).get("items", [])
        items.extend(batch)
        if len(batch) < 100: break
    return items


def parse_date(item: dict):
    value = item.get("commit", {}).get("committer", {}).get("date")
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(dt.timezone.utc) if value else None


def longest_run(dates: set[dt.date]) -> int:
    best = 0
    for day in dates:
        if day - dt.timedelta(days=1) in dates: continue
        run = 1
        while day + dt.timedelta(days=run) in dates: run += 1
        best = max(best, run)
    return best


def card(x: int, color: str, label: str, value: int, detail: str, glyph: str) -> str:
    w = 204; y = 124; h = 220
    return f'''  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="{PANEL_ALT}" stroke="{BORDER}"/>
  <circle cx="{x + 42}" cy="{y + 44}" r="25" fill="#24134e" stroke="{color}" stroke-width="1.5"/>
  <text x="{x + 42}" y="{y + 52}" text-anchor="middle" fill="{TEXT}" font-family="{FONT}" font-size="23" font-weight="700">{glyph}</text>
  <text x="{x + 78}" y="{y + 50}" fill="{ACCENT_2}" font-family="{FONT}" font-size="15" font-weight="700">{label}</text>
  <text x="{x + 28}" y="{y + 132}" fill="{TEXT}" font-family="{FONT}" font-size="52" font-weight="700">{value}</text>
  <text x="{x + 28}" y="{y + 168}" fill="{MUTED}" font-family="{FONT}" font-size="14">{detail}</text>
  <path d="M{x + 28} {y + 194} C{x + 62} {y + 176} {x + 98} {y + 206} {x + 126} {y + 184} S{x + 170} {y + 202} {x + 176} {y + 170}" fill="none" stroke="{color}" stroke-width="2" opacity=".9"/>
  <circle cx="{x + 176}" cy="{y + 170}" r="4" fill="{color}"/>
  <rect x="{x + 1}" y="{y + h - 5}" width="{w - 2}" height="4" rx="2" fill="url(#violet)"/>'''


def main() -> None:
    start_24h = NOW - dt.timedelta(hours=24); start_history = NOW - dt.timedelta(days=3650)
    recent = api_search(f"author:{OWNER} committer-date:>={start_24h:%Y-%m-%dT%H:%M:%SZ}")
    history = api_search(f"author:{OWNER} committer-date:>={start_history:%Y-%m-%dT%H:%M:%SZ}")
    dates = [parsed.date() for item in history if (parsed := parse_date(item))]
    date_set = set(dates); per_day = collections.Counter(dates)
    current_streak = 0; day = NOW.date()
    if day not in date_set and day - dt.timedelta(days=1) in date_set: day -= dt.timedelta(days=1)
    while day in date_set: current_streak += 1; day -= dt.timedelta(days=1)
    values = {"last_24h": len(recent), "current_streak": current_streak, "most_in_day": max(per_day.values(), default=0), "longest_streak": longest_run(date_set)}
    output = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="430" viewBox="0 0 1000 430" role="img" aria-label="Commit activity statistics" data-design="reference-v2">
  <defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{BG}"/><stop offset="1" stop-color="{PANEL}"/></linearGradient><linearGradient id="violet" x1="0" x2="1"><stop stop-color="#7047c7"/><stop offset=".55" stop-color="{ACCENT}"/><stop offset="1" stop-color="#c18cff"/></linearGradient></defs>
  <rect width="1000" height="430" rx="24" fill="url(#bg)" stroke="{BORDER}" stroke-width="1.5"/>
  <circle cx="70" cy="74" r="38" fill="#24134e" stroke="url(#violet)" stroke-width="2"/><text x="70" y="84" text-anchor="middle" fill="{TEXT}" font-family="{FONT}" font-size="28" font-weight="700">↗</text>
  <text x="128" y="72" fill="{TEXT}" font-family="{FONT}" font-size="28" font-weight="700">Commit activity</text>
  <text x="128" y="101" fill="{MUTED}" font-family="{FONT}" font-size="15">Live metrics from GitHub · <tspan fill="{ACCENT_2}">refreshed daily</tspan></text>
  <path d="M720 96 C760 58 792 116 832 74 S918 54 964 87" fill="none" stroke="#7047c7" stroke-width="1.5"/><circle cx="832" cy="74" r="4" fill="#c18cff"/><circle cx="964" cy="87" r="4" fill="{ACCENT}"/>
{card(28, ACCENT, 'Last 24 hours', values['last_24h'], 'commits', '24')}
{card(266, ACCENT_2, 'Current streak', values['current_streak'], 'consecutive days', 'ST')}
{card(504, '#7047c7', 'Most in one day', values['most_in_day'], 'commits on best day', '*')}
{card(742, '#c18cff', 'Longest streak', values['longest_streak'], 'consecutive days', 'LS')}
</svg>'''
    OUTPUT.parent.mkdir(parents=True, exist_ok=True); OUTPUT.write_text(output, encoding="utf-8")


if __name__ == "__main__": main()
