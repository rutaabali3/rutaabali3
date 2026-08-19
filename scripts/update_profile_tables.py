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
README = ROOT / "readme.md"
START = "<!-- LIVE-GITHUB-TABLES:START -->"
END = "<!-- LIVE-GITHUB-TABLES:END -->"


def api(path: str):
    request = urllib.request.Request(
        "https://api.github.com" + path,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "rutaabali3-profile-tables",
            **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def md_escape(value) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


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
            for language, amount in api(f"/repos/{OWNER}/{repo['name']}/languages").items():
                languages[language] += int(amount)
        except Exception:
            pass

    year = datetime.now(timezone.utc).year
    commit_items = []
    try:
        query = urllib.parse.quote(f"author:{OWNER} committer-date:>={year}-01-01")
        commit_items = api(f"/search/commits?q={query}&per_page=100").get("items", [])
    except Exception:
        pass

    commit_days = Counter()
    for item in commit_items:
        raw = item.get("commit", {}).get("committer", {}).get("date")
        if raw:
            commit_days[raw[:10]] += 1

    all_commit_items = []
    try:
        query = urllib.parse.quote(f"author:{OWNER} committer-date:>={datetime.now(timezone.utc).year - 10}-01-01")
        all_commit_items = api(f"/search/commits?q={query}&per_page=100").get("items", [])
    except Exception:
        pass
    history_days = Counter()
    for item in all_commit_items:
        raw = item.get("commit", {}).get("committer", {}).get("date")
        if raw:
            history_days[raw[:10]] += 1

    active_dates = sorted((day for day, count in commit_days.items() if count), reverse=True)
    total_commits = sum(commit_days.values())
    active_days = len(active_dates)
    best_day = max(commit_days.values(), default=0)
    all_dates = set(history_days)
    current_streak = 0
    cursor = date.today()
    if cursor.isoformat() not in all_dates:
        cursor -= timedelta(days=1)
    while cursor.isoformat() in all_dates:
        current_streak += 1
        cursor -= timedelta(days=1)
    longest_streak = 0
    for raw_day in all_dates:
        day = date.fromisoformat(raw_day)
        if (day - timedelta(days=1)).isoformat() in all_dates:
            continue
        run = 1
        while (day + timedelta(days=run)).isoformat() in all_dates:
            run += 1
        longest_streak = max(longest_streak, run)

    total_bytes = sum(languages.values()) or 1
    language_rows = []
    for language, amount in languages.most_common(8):
        language_rows.append(f"| {md_escape(language)} | {amount:,} bytes | {amount / total_bytes * 100:.1f}% |")

    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    rows = [
        START,
        f"_Live GitHub API snapshot · generated automatically · refreshed {updated}_",
        "",
        "### Commit activity output",
        "",
        "| Metric | Value | Meaning |",
        "|:--|--:|:--|",
        f"| Commits in the last 24 hours | **{sum(1 for item in commit_items if item.get('commit')):,}** | Recent commit activity |",
        f"| Current streak | **{current_streak} days** | Consecutive days with commits |",
        f"| Most commits in one day | **{best_day}** | Best commit day this year |",
        f"| Longest streak | **{longest_streak} days** | Longest historical consecutive run |",
        "",
        "### Contributor statistics output",
        "",
        "| Metric | Value | Meaning |",
        "|:--|--:|:--|",
        f"| Public repositories | **{user.get('public_repos', 0):,}** | Public repositories owned |",
        f"| Followers | **{user.get('followers', 0):,}** | GitHub followers |",
        f"| Stars | **{stars:,}** | Stars across public repositories |",
        f"| Forks | **{forks:,}** | Forks across public repositories |",
        "",
        "### Language mix output",
        "",
        "| Language | Repository bytes | Share |",
        "|:--|--:|--:|",
    ]
    rows.extend(language_rows)
    rows.extend([
        "",
        "### Profile details output",
        "",
        "| Activity detail | Value | Meaning |",
        "|:--|--:|:--|",
        f"| Commits this year | **{total_commits:,}** | Commits found in {year} |",
        f"| Active days this year | **{active_days:,}** | Days with at least one commit |",
        f"| Best day this year | **{best_day:,} commits** | Highest daily total |",
        f"| Public events | **{len(api(f'/users/{urllib.parse.quote(OWNER)}/events/public?per_page=100')):,}** | Recent public GitHub events |",
        "",
        "| Recent active date | Commits |",
        "|:--|--:|",
    ])
    rows.extend(f"| {day} | {commit_days[day]:,} |" for day in active_dates[:12])
    rows.extend([END, ""])

    content = README.read_text(encoding="utf-8")
    block = "\n".join(rows)
    if START in content and END in content:
        before = content.split(START, 1)[0]
        after = content.split(END, 1)[1]
        content = before + block + after
    else:
        marker = "## Experience snapshot"
        content = content.replace(marker, block + "\n" + marker, 1)
    README.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
