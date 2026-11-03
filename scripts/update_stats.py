"""Generate a self-contained profile card from GitHub's public repository API."""

import json
import os
from collections import Counter
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen

OWNER = "k-dev178"
OUTPUT = Path(__file__).resolve().parents[1] / "assets" / "github-stats.svg"


def fetch_repositories():
    repositories = []
    page = 1
    while True:
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-stats"}
        if token := os.environ.get("GH_TOKEN"):
            headers["Authorization"] = f"Bearer {token}"
        request = Request(
            f"https://api.github.com/users/{OWNER}/repos?per_page=100&page={page}",
            headers=headers,
        )
        with urlopen(request, timeout=30) as response:
            batch = json.load(response)
        repositories.extend(batch)
        if len(batch) < 100:
            return repositories
        page += 1


def render(repositories, updated):
    originals = [r for r in repositories if not r["fork"] and not r.get("private", False)]
    languages = Counter(r["language"] for r in originals if r["language"])
    metrics = [
        ("Repositories", len(originals)),
        ("Stars", sum(r["stargazers_count"] for r in originals)),
        ("Forks", sum(r["forks_count"] for r in originals)),
    ]
    elements = []
    for index, (label, value) in enumerate(metrics):
        x = 28 + index * 180
        elements.append(f'<text x="{x}" y="105" class="number">{value}</text>')
        elements.append(f'<text x="{x}" y="131" class="muted">{label}</text>')
    for index, (language, count) in enumerate(languages.most_common(5)):
        y = 203 + index * 31
        elements.append(f'<text x="28" y="{y}" class="body">{escape(language)}</text>')
        elements.append(f'<text x="550" y="{y}" text-anchor="end" class="muted">{count} repos</text>')
    if not languages:
        elements.append('<text x="28" y="203" class="muted">No language data yet</text>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="580" height="400" viewBox="0 0 580 400" role="img" aria-labelledby="title desc">
  <title id="title">{OWNER} · GitHub overview</title>
  <desc id="desc">Public non-fork repository statistics. Languages counted by repository.</desc>
  <style>
    text {{ font-family: -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; }}
    .heading {{ fill: #7dd3fc; font-size: 20px; font-weight: 600; }}
    .number {{ fill: #f1f5f9; font-size: 30px; font-weight: 700; }}
    .body {{ fill: #e2e8f0; font-size: 15px; }}
    .muted {{ fill: #94a3b8; font-size: 13px; }}
  </style>
  <rect x="1" y="1" width="578" height="398" rx="16" fill="#0f172a" stroke="#334155"/>
  <text x="28" y="41" class="heading">{OWNER} / GitHub</text>
  {''.join(elements)}
  <path d="M28 151H552" stroke="#334155"/>
  <text x="28" y="177" class="muted">Primary languages · repository count</text>
  <text x="28" y="375" class="muted">Public non-fork repos · Updated {escape(updated)} UTC</text>
</svg>
'''


if __name__ == "__main__":
    # Fetch everything before writing so API failures preserve the previous card.
    repositories = fetch_repositories()
    card = render(repositories, datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(card, encoding="utf-8")
