from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, datetime, timedelta, timezone
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
DEEP = "#0f0c25"

FONT = "DejaVu Sans,Arial,sans-serif"


def api(path: str):
    req = urllib.request.Request("https://api.github.com" + path, headers={"Accept": "application/vnd.github+json", "User-Agent": "rutaabali3-profile-readme", **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {})})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def esc(value) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def write(name: str, lines: list[str]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    lines.append("</svg>")
    (OUT / name).write_text("\n".join(lines) + "\n", encoding="utf-8")


def base(width: int, height: int, title: str, subtitle: str, icon: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}" data-design="reference-v2">',
        '<defs>',
        '<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#0c0b1b"/><stop offset="1" stop-color="#171330"/></linearGradient>',
        '<linearGradient id="violet" x1="0" x2="1"><stop stop-color="#7047c7"/><stop offset=".55" stop-color="#8d5cff"/><stop offset="1" stop-color="#c18cff"/></linearGradient>',
        '<filter id="glow"><feGaussianBlur stdDeviation="5" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
        '</defs>',
        '<rect width="100%" height="100%" rx="24" fill="url(#bg)" stroke="#362171" stroke-width="1.5"/>',
        f'<circle cx="70" cy="74" r="38" fill="#24134e" stroke="url(#violet)" stroke-width="2"/>',
        f'<text x="70" y="85" text-anchor="middle" fill="{TEXT}" font-family="{FONT}" font-size="28" font-weight="700">{esc(icon)}</text>',
        f'<text x="128" y="72" fill="{TEXT}" font-family="{FONT}" font-size="28" font-weight="700">{esc(title)}</text>',
        f'<text x="128" y="101" fill="{MUTED}" font-family="{FONT}" font-size="15">{esc(subtitle)}</text>',
        '<path d="M690 96 C735 58 762 116 806 74 S875 54 892 87" fill="none" stroke="#7047c7" stroke-width="1.5" opacity=".8"/>',
        '<path d="M706 100 C750 73 770 118 814 85 S869 70 900 92" fill="none" stroke="#362171" stroke-width="1"/>',
        '<circle cx="806" cy="74" r="3.5" fill="#c18cff" filter="url(#glow)"/><circle cx="892" cy="87" r="3.5" fill="#8d5cff" filter="url(#glow)"/>',
    ]


def panel(lines: list[str], x: int, y: int, w: int, h: int) -> None:
    lines.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="{PANEL_ALT}" stroke="{BORDER}"/>')


def icon_badge(lines: list[str], x: int, y: int, glyph: str, accent: str = ACCENT) -> None:
    lines.extend([
        f'<circle cx="{x}" cy="{y}" r="25" fill="#24134e" stroke="{accent}" stroke-width="1.5"/>',
        f'<text x="{x}" y="{y + 8}" text-anchor="middle" fill="{TEXT}" font-family="{FONT}" font-size="23" font-weight="700">{esc(glyph)}</text>',
    ])


def metric(lines: list[str], x: int, y: int, w: int, h: int, label: str, value: str, detail: str, glyph: str, accent: str) -> None:
    panel(lines, x, y, w, h)
    icon_badge(lines, x + 40, y + 43, glyph, accent)
    lines.extend([
        f'<text x="{x + 78}" y="{y + 49}" fill="{ACCENT_2}" font-family="{FONT}" font-size="15" font-weight="700">{esc(label)}</text>',
        f'<text x="{x + 28}" y="{y + 118}" fill="{TEXT}" font-family="{FONT}" font-size="44" font-weight="700">{esc(value)}</text>',
        f'<text x="{x + 28}" y="{y + 147}" fill="{MUTED}" font-family="{FONT}" font-size="14">{esc(detail)}</text>',
        f'<path d="M{x + 28} {y + h - 28} C{x + 72} {y + h - 48} {x + 110} {y + h - 12} {x + 150} {y + h - 38} S{x + 230} {y + h - 10} {x + w - 28} {y + h - 54}" fill="none" stroke="{accent}" stroke-width="2" opacity=".85"/>',
        f'<circle cx="{x + w - 28}" cy="{y + h - 54}" r="4" fill="{accent}" filter="url(#glow)"/>',
        f'<rect x="{x + 1}" y="{y + h - 5}" width="{w - 2}" height="4" rx="2" fill="url(#violet)"/>',
    ])


def compact_metric(lines: list[str], x: int, y: int, w: int, h: int, label: str, value: str, detail: str, glyph: str, accent: str) -> None:
    panel(lines, x, y, w, h)
    icon_badge(lines, x + 28, y + 28, glyph, accent)
    label_parts = label.split(" ", 1) if len(label) > 12 and " " in label else [label]
    if len(label_parts) == 2:
        lines.extend([
            f'<text x="{x + 52}" y="{y + 20}" fill="{ACCENT_2}" font-family="{FONT}" font-size="10" font-weight="700">{esc(label_parts[0])}</text>',
            f'<text x="{x + 52}" y="{y + 33}" fill="{ACCENT_2}" font-family="{FONT}" font-size="10" font-weight="700">{esc(label_parts[1])}</text>',
        ])
    else:
        lines.append(f'<text x="{x + 52}" y="{y + 27}" fill="{ACCENT_2}" font-family="{FONT}" font-size="11" font-weight="700">{esc(label)}</text>')
    lines.extend([
        f'<text x="{x + 18}" y="{y + 88}" fill="{TEXT}" font-family="{FONT}" font-size="32" font-weight="700">{esc(value)}</text>',
        f'<text x="{x + 18}" y="{y + 111}" fill="{MUTED}" font-family="{FONT}" font-size="11">{esc(detail)}</text>',
        f'<path d="M{x + 18} {y + h - 25} C{x + 42} {y + h - 42} {x + 68} {y + h - 12} {x + 92} {y + h - 31} S{x + w - 30} {y + h - 16} {x + w - 18} {y + h - 43}" fill="none" stroke="{accent}" stroke-width="1.8" opacity=".9"/>',
        f'<circle cx="{x + w - 18}" cy="{y + h - 43}" r="3.5" fill="{accent}" filter="url(#glow)"/>',
    ])


def main() -> None:
    user = api(f"/users/{urllib.parse.quote(OWNER)}")
    repos = api(f"/users/{urllib.parse.quote(OWNER)}/repos?per_page=100&sort=updated")
    languages = Counter(); stars = 0; forks = 0
    for repo in repos:
        stars += int(repo.get("stargazers_count", 0)); forks += int(repo.get("forks_count", 0))
        try:
            for lang, amount in api(f"/repos/{OWNER}/{repo['name']}/languages").items(): languages[lang] += int(amount)
        except Exception: pass
    total_bytes = sum(languages.values()) or 1
    top_languages = languages.most_common(8)
    events = []
    try: events = api(f"/users/{urllib.parse.quote(OWNER)}/events/public?per_page=100")
    except Exception: pass
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d UTC")
    commit_items = []
    try:
        query = urllib.parse.quote(f"author:{OWNER} committer-date:>={datetime.now(timezone.utc).year}-01-01")
        commit_items = api(f"/search/commits?q={query}&per_page=100").get("items", [])
    except Exception: pass
    commit_days = Counter()
    for item in commit_items:
        raw = item.get("commit", {}).get("committer", {}).get("date")
        if raw: commit_days[raw[:10]] += 1

    lines = base(1000, 390, "Contributor statistics", f"Live GitHub metrics · exact terminal palette · refreshed {updated}", "C")
    metric(lines, 28, 140, 226, 196, "Public repos", user.get("public_repos", 0), "repositories", "R", ACCENT)
    metric(lines, 266, 140, 226, 196, "Followers", user.get("followers", 0), "people following", "F", ACCENT_2)
    metric(lines, 504, 140, 226, 196, "Stars", stars, "across public repos", "*", "#7047c7")
    metric(lines, 742, 140, 226, 196, "Forks", forks, "repository forks", "+", "#c18cff")
    write("profile-stats.svg", lines)

    lines = base(1000, 610, "Most used languages", f"Repository language mix · refreshed {updated}", "<>")
    panel(lines, 28, 138, 944, 430)
    for index, (language, amount) in enumerate(top_languages):
        col = index % 2; row = index // 2; x = 58 + col * 456; y = 176 + row * 92
        percent = amount / total_bytes * 100; bar_width = max(10, int(330 * percent / 100)); accent = ACCENT if index % 2 == 0 else ACCENT_2
        icon_badge(lines, x + 24, y + 20, language[:2].upper(), accent)
        lines.extend([
            f'<text x="{x + 62}" y="{y + 15}" fill="{TEXT}" font-family="{FONT}" font-size="17" font-weight="700">{esc(language)}</text>',
            f'<text x="{x + 400}" y="{y + 15}" text-anchor="end" fill="{ACCENT_2}" font-family="{FONT}" font-size="16" font-weight="700">{percent:.1f}%</text>',
            f'<rect x="{x + 62}" y="{y + 34}" width="338" height="12" rx="6" fill="{GRID}"/>',
            f'<rect x="{x + 62}" y="{y + 34}" width="{bar_width}" height="12" rx="6" fill="url(#violet)"/>',
        ])
    write("language-stats.svg", lines)

    lines = base(1000, 590, "Profile details", f"Contribution activity · exact terminal palette · refreshed {updated}", "P")
    panel(lines, 28, 138, 565, 410); panel(lines, 615, 138, 357, 410)
    icon_badge(lines, 650, 176, "~", ACCENT)
    lines.extend([f'<text x="690" y="180" fill="{TEXT}" font-family="{FONT}" font-size="20" font-weight="700">Activity overview</text>', f'<text x="58" y="180" fill="{TEXT}" font-family="{FONT}" font-size="20" font-weight="700">Commit activity</text>', f'<text x="58" y="208" fill="{MUTED}" font-family="{FONT}" font-size="14">Recent contribution rhythm</text>'])
    start = date.today() - timedelta(days=181)
    for index in range(182):
        day = start + timedelta(days=index); col = index // 7; row = index % 7; count = commit_days.get(day.isoformat(), 0)
        color = GRID if count == 0 else (BORDER if count == 1 else ("#7047c7" if count < 4 else ACCENT))
        lines.append(f'<rect x="{58 + col * 18}" y="{244 + row * 25}" width="14" height="14" rx="4" fill="{color}"/>')
    lines.extend([f'<text x="58" y="454" fill="{MUTED}" font-family="{FONT}" font-size="12">Less</text>', f'<rect x="98" y="444" width="14" height="14" rx="4" fill="{GRID}"/><rect x="120" y="444" width="14" height="14" rx="4" fill="{BORDER}"/><rect x="142" y="444" width="14" height="14" rx="4" fill="#7047c7"/><rect x="164" y="444" width="14" height="14" rx="4" fill="{ACCENT}"/>', f'<text x="190" y="454" fill="{MUTED}" font-family="{FONT}" font-size="12">More</text>'])
    active_days = sum(value > 0 for value in commit_days.values()); total_commits = sum(commit_days.values()); best_day = max(commit_days.values(), default=0)
    compact_metric(lines, 637, 214, 145, 142, "Commits this year", total_commits, "commits", "C", ACCENT)
    compact_metric(lines, 805, 214, 145, 142, "Active days", active_days, "days", "D", ACCENT_2)
    compact_metric(lines, 637, 374, 145, 142, "Best day", best_day, "commits", "*", "#7047c7")
    compact_metric(lines, 805, 374, 145, 142, "Public events", len(events), "events", "E", "#c18cff")
    write("profile-details.svg", lines)


if __name__ == "__main__": main()
