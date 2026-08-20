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


def search_commits(query: str, sort: str | None = None, max_items: int = 300):
    """Page through /search/commits, returning (items, total_count).

    total_count comes straight from GitHub's response on every page, so it's
    accurate even if we stop paginating early. `sort` should be set whenever
    recency matters (e.g. streak calculations) -- the search endpoint's
    default order is best-match relevance, not chronological, so leaving it
    unset silently returns an unpredictable sample of commits.
    """
    items: list[dict] = []
    total_count = 0
    page = 1
    while len(items) < max_items:
        params = f"q={urllib.parse.quote(query)}&per_page=100&page={page}"
        if sort:
            params += f"&sort={sort}&order=desc"
        try:
            data = api(f"/search/commits?{params}")
        except Exception:
            break
        total_count = data.get("total_count", total_count)
        batch = data.get("items", [])
        if not batch:
            break
        items.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return items, total_count


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

    now = datetime.now(timezone.utc)
    year = now.year

    # Real rolling-24h window (previous version reused the year-to-date
    # query here, so this number was always identical to "commits this
    # year" -- both landed on the same 100-item page cap).
    since_24h = (now - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
    last24_query = f"author:{OWNER} committer-date:>={since_24h}"
    _, commits_last_24h = search_commits(last24_query, sort="committer-date")

    # Year-to-date commits. total_count is trusted for the headline number;
    # the fetched items are only used for the best-day / active-days
    # breakdown, which is why we still page through a few hundred of them.
    ytd_query = f"author:{OWNER} committer-date:>={year}-01-01"
    ytd_items, total_commits = search_commits(ytd_query, sort="committer-date")

    commit_days = Counter()
    for item in ytd_items:
        raw = item.get("commit", {}).get("committer", {}).get("date")
        if raw:
            commit_days[raw[:10]] += 1
    best_day = max(commit_days.values(), default=0)
    active_days = sum(1 for count in commit_days.values() if count)

    # Longer history for the streak calc. Sorted by committer-date so the
    # most recent commits are guaranteed to be in the first page -- without
    # `sort=committer-date`, the old query returned a best-match sample that
    # often skipped yesterday/today entirely, which is why "current streak"
    # was showing 0 days.
    history_query = f"author:{OWNER} committer-date:>={year - 10}-01-01"
    history_items, _ = search_commits(history_query, sort="committer-date", max_items=1000)
    history_days = Counter()
    for item in history_items:
        raw = item.get("commit", {}).get("committer", {}).get("date")
        if raw:
            history_days[raw[:10]] += 1

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

    updated = now.strftime("%Y-%m-%d %H:%M UTC")
    rows = [
        START,
        f"_Live GitHub API snapshot · generated automatically · refreshed {updated}_",
        "",
        "## Commit activity output",
        "",
        "| Metric | Live value | What it represents | Data window | Refresh |",
        "|:--|--:|:--|:--|:--|",
        f"| Commits in the last 24 hours | **{commits_last_24h:,}** | Recent commit activity | Rolling 24 hours | Automatic |",
        f"| Current streak | **{current_streak} days** | Consecutive days with commits | GitHub history | Automatic |",
        f"| Most commits in one day | **{best_day}** | Highest daily commit total | Current year | Automatic |",
        f"| Longest streak | **{longest_streak} days** | Longest consecutive run | GitHub history | Automatic |",
        "",
        "## Contributor statistics output",
        "",
        "| Metric | Live value | What it represents | Data basis | Refresh |",
        "|:--|--:|:--|:--|:--|",
        f"| Public repositories | **{user.get('public_repos', 0):,}** | Public repositories owned | GitHub profile | Automatic |",
        f"| Followers | **{user.get('followers', 0):,}** | People following this profile | GitHub profile | Automatic |",
        f"| Stars | **{stars:,}** | Stars across public repositories | Repository metadata | Automatic |",
        f"| Forks | **{forks:,}** | Forks across public repositories | Repository metadata | Automatic |",
        "",
        "## Language mix output",
        "",
        "| Language | Repository bytes | Share of detected code | Data basis | Refresh |",
        "|:--|--:|--:|:--|:--|",
    ]
    rows.extend(f"{row[:-1]} | Repository language statistics | Automatic |" for row in language_rows)
    rows.extend([
        "",
        "## Profile details output",
        "",
        "| Activity detail | Live value | What it represents | Data window | Refresh |",
        "|:--|--:|:--|:--|:--|",
        f"| Commits this year | **{total_commits:,}** | Commits found in {year} | Calendar year | Automatic |",
        f"| Active days this year | **{active_days:,}** | Days with at least one commit | Calendar year | Automatic |",
        f"| Best day this year | **{best_day:,} commits** | Highest daily total | Calendar year | Automatic |",
        f"| Public events | **{len(api(f'/users/{urllib.parse.quote(OWNER)}/events/public?per_page=100')):,}** | Recent public GitHub events | Latest API window | Automatic |",
    ])
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
