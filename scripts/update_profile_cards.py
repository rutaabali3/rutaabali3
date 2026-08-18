from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

OWNER = os.environ.get("GITHUB_REPOSITORY_OWNER", "rutaabali3")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets"

BG = "#0c0b1b"
PANEL = "#171330"
PANEL_ALT = "#14132f"
BORDER = "#362171"
ACCENT = "#8d5cff"
ACCENT_2 = "#b58cff"
TEXT = "#e5ddff"
MUTED = "#9e94bb"
GRID = "#241b45"


def api(path: str):
    req = urllib.request.Request(
        "https://api.github.com" + path,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "rutaabali3-profile-readme",
            **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def esc(value) -> str:
    text = str(value)
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def svg_open(width: int, height: int, title: str, subtitle: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f'<rect width="{width}" height="{height}" rx="16" fill="{BG}" stroke="{BORDER}"/>',
        f'<path d="M0 80H{width}" stroke="{GRID}"/>',
        f'<text x="30" y="35" fill="{TEXT}" font-family="Segoe UI,Arial,sans-serif" font-size="20" font-weight="700">{esc(title)}</text>',
        f'<text x="30" y="59" fill="{MUTED}" font-family="Segoe UI,Arial,sans-serif" font-size="12">{esc(subtitle)}</text>',
    ]


def write(name: str, lines: list[str]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    lines.append("</svg>")
    (OUT / name).write_text("\n".join(lines) + "\n", encoding="utf-8")


def metric_card(lines: list[str], x: int, y: int, width: int, label: str, value: str, detail: str, accent: str = ACCENT) -> None:
    lines.extend([
        f'<rect x="{x}" y="{y}" width="{width}" height="112" rx="12" fill="{PANEL}" stroke="{BORDER}"/>',
        f'<circle cx="{x + 26}" cy="{y + 28}" r="10" fill="{accent}" opacity=".2"/>',
        f'<circle cx="{x + 26}" cy="{y + 28}" r="4" fill="{accent}"/>',
        f'<text x="{x + 46}" y="{y + 33}" fill="{ACCENT_2}" font-family="Segoe UI,Arial,sans-serif" font-size="12" font-weight="600">{esc(label)}</text>',
        f'<text x="{x + 20}" y="{y + 79}" fill="{TEXT}" font-family="Segoe UI,Arial,sans-serif" font-size="28" font-weight="700">{esc(value)}</text>',
        f'<text x="{x + 20}" y="{y + 99}" fill="{MUTED}" font-family="Segoe UI,Arial,sans-serif" font-size="11">{esc(detail)}</text>',
    ])


def main() -> None:
    user = api(f"/users/{urllib.parse.quote(OWNER)}")
    repos = api(f"/users/{urllib.parse.quote(OWNER)}/repos?per_page=100&sort=updated")
    languages = Counter()
    stars = 0
    forks = 0
    for repo in repos:
        stars += int(repo.get("stargazers_count", 0))
        forks += int(repo.get("forks_count", 0))
        try:
            for lang, amount in api(f"/repos/{OWNER}/{repo['name']}/languages").items():
                languages[lang] += int(amount)
        except Exception:
            continue

    total_bytes = sum(languages.values()) or 1
    top_languages = languages.most_common(8)
    events = []
    try:
        events = api(f"/users/{urllib.parse.quote(OWNER)}/events/public?per_page=100")
    except Exception:
        pass
    push_events = sum(1 for event in events if event.get("type") == "PushEvent")
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d UTC")

    commit_items = []
    try:
        since = (datetime.now(timezone.utc).date()).isoformat()
        query = urllib.parse.quote(f"author:{OWNER} committer-date:>={since[:4]}-01-01")
        commit_items = api(f"/search/commits?q={query}&per_page=100") .get("items", [])
    except Exception:
        commit_items = []
    commit_days = Counter()
    for item in commit_items:
        raw = item.get("commit", {}).get("committer", {}).get("date")
        if raw:
            commit_days[raw[:10]] += 1

    lines = svg_open(900, 230, "Contributor statistics", f"Exact terminal palette · refreshed {updated}")
    metric_card(lines, 24, 92, 204, "Public repos", str(user.get("public_repos", 0)), "repositories", ACCENT)
    metric_card(lines, 240, 92, 204, "Followers", str(user.get("followers", 0)), "people following", ACCENT_2)
    metric_card(lines, 456, 92, 204, "Stars", str(stars), "across public repos", "#7047c7")
    metric_card(lines, 672, 92, 204, "Forks", str(forks), "repository forks", "#c18cff")
    write("profile-stats.svg", lines)

    lines = svg_open(900, 300, "Most used languages", f"Repository language mix · refreshed {updated}")
    for index, (language, amount) in enumerate(top_languages):
        col = index % 2
        row = index // 2
        x = 24 + col * 432
        y = 92 + row * 48
        percent = amount / total_bytes * 100
        bar_width = max(8, int(360 * percent / 100))
        lines.extend([
            f'<text x="{x}" y="{y + 17}" fill="{TEXT}" font-family="Segoe UI,Arial,sans-serif" font-size="13" font-weight="600">{esc(language)}</text>',
            f'<text x="{x + 384}" y="{y + 17}" fill="{MUTED}" text-anchor="end" font-family="Segoe UI,Arial,sans-serif" font-size="12">{percent:.1f}%</text>',
            f'<rect x="{x}" y="{y + 26}" width="360" height="8" rx="4" fill="{GRID}"/>',
            f'<rect x="{x}" y="{y + 26}" width="{bar_width}" height="8" rx="4" fill="{ACCENT if index % 2 == 0 else ACCENT_2}"/>',
        ])
    write("language-stats.svg", lines)

    lines = svg_open(900, 340, "Profile details", f"Contribution activity · exact terminal palette · refreshed {updated}")
    lines.extend([
        f'<text x="30" y="101" fill="{ACCENT_2}" font-family="Segoe UI,Arial,sans-serif" font-size="12" font-weight="600">Commit activity</text>',
        f'<text x="30" y="119" fill="{MUTED}" font-family="Segoe UI,Arial,sans-serif" font-size="11">Recent contribution rhythm</text>',
    ])
    start = datetime.now(timezone.utc).date() - __import__("datetime").timedelta(days=181)
    for index in range(182):
        day = start + __import__("datetime").timedelta(days=index)
        col = index // 7
        row = index % 7
        count = commit_days.get(day.isoformat(), 0)
        color = GRID if count == 0 else ("#362171" if count == 1 else ("#7047c7" if count < 4 else ACCENT))
        x = 30 + col * 17
        y = 132 + row * 17
        lines.append(f'<rect x="{x}" y="{y}" width="12" height="12" rx="3" fill="{color}"/>')
    active_days = sum(1 for value in commit_days.values() if value > 0)
    total_commits = sum(commit_days.values())
    best_day = max(commit_days.values(), default=0)
    lines.extend([
        f'<rect x="520" y="96" width="356" height="190" rx="14" fill="{PANEL}" stroke="{BORDER}"/>',
        f'<text x="548" y="132" fill="{TEXT}" font-family="Segoe UI,Arial,sans-serif" font-size="15" font-weight="700">Activity overview</text>',
        f'<text x="548" y="164" fill="{ACCENT_2}" font-family="Segoe UI,Arial,sans-serif" font-size="12">Commits this year</text>',
        f'<text x="548" y="190" fill="{TEXT}" font-family="Segoe UI,Arial,sans-serif" font-size="26" font-weight="700">{total_commits}</text>',
        f'<text x="700" y="164" fill="{ACCENT_2}" font-family="Segoe UI,Arial,sans-serif" font-size="12">Active days</text>',
        f'<text x="700" y="190" fill="{TEXT}" font-family="Segoe UI,Arial,sans-serif" font-size="26" font-weight="700">{active_days}</text>',
        f'<text x="548" y="226" fill="{ACCENT_2}" font-family="Segoe UI,Arial,sans-serif" font-size="12">Best day</text>',
        f'<text x="548" y="252" fill="{TEXT}" font-family="Segoe UI,Arial,sans-serif" font-size="26" font-weight="700">{best_day}</text>',
        f'<text x="700" y="226" fill="{ACCENT_2}" font-family="Segoe UI,Arial,sans-serif" font-size="12">Public events</text>',
        f'<text x="700" y="252" fill="{TEXT}" font-family="Segoe UI,Arial,sans-serif" font-size="26" font-weight="700">{len(events)}</text>',
        f'<text x="548" y="273" fill="{MUTED}" font-family="Segoe UI,Arial,sans-serif" font-size="11">Live GitHub activity</text>',
    ])
    write("profile-details.svg", lines)


if __name__ == "__main__":
    main()
