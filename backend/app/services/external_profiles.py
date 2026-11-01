"""
Optional profile links (GitHub, LinkedIn, LeetCode, portfolio).

* Every link is optional and only read after the student gives consent.
* We never ask for or store third-party passwords.
* GitHub: official public REST API (no login). LinkedIn/LeetCode: no scraping;
  the student can paste details manually. Portfolio: one public page is fetched.
* If anything fails we mark the link "unavailable", explain why, and carry on.
"""
import ipaddress
import re
import socket
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx

from app.config import settings
from app.models import ProfileLink

HOSTS = {"github": ["github.com"], "linkedin": ["linkedin.com"], "leetcode": ["leetcode.com"]}


def validate_url(kind: str, url: str) -> str:
    url = url.strip()
    if not re.match(r"^https?://", url):
        url = "https://" + url
    p = urlparse(url)
    host = (p.hostname or "").lower()
    if p.scheme not in ("http", "https") or not host or "." not in host:
        raise ValueError("That does not look like a valid web address.")
    allowed = HOSTS.get(kind)
    if allowed and not any(host == h or host.endswith("." + h) for h in allowed):
        raise ValueError(f"A {kind} link should be on {allowed[0]}.")
    return url


def _is_public(host: str) -> bool:
    """Block localhost / private network addresses (protects the server from SSRF)."""
    try:
        for info in socket.getaddrinfo(host, None):
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return False
        return True
    except (socket.gaierror, ValueError):
        return False


def analyse_github(link: ProfileLink) -> None:
    m = re.match(r"https?://(?:www\.)?github\.com/([A-Za-z0-9-]+)", link.url)
    if not m:
        link.status, link.note = "invalid", "Use your profile link, like https://github.com/your-username."
        return
    user = m.group(1)
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "CareerPilot-AI"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    try:
        r = httpx.get(f"https://api.github.com/users/{user}/repos", params={"per_page": 30, "sort": "updated"},
                      headers=headers, timeout=8)
    except httpx.HTTPError:
        link.status, link.note = "unavailable", "GitHub could not be reached right now. We used your resume instead."
        return
    if r.status_code == 404:
        link.status, link.note = "unavailable", f"No public GitHub user called '{user}'."
        return
    if r.status_code != 200:
        link.status, link.note = "unavailable", f"GitHub answered {r.status_code} (often a rate limit). Try again later."
        return
    repos = [x for x in r.json() if not x.get("fork")]
    langs: dict[str, int] = {}
    for x in repos:
        if x.get("language"):
            langs[x["language"]] = langs.get(x["language"], 0) + 1
    link.summary = {
        "repo_count": len(repos), "languages": sorted(langs, key=lambda k: -langs[k]),
        "repos": [{"name": x["name"], "description": x.get("description") or "", "language": x.get("language"),
                   "topics": x.get("topics", []), "url": x["html_url"]} for x in repos[:8]],
        "note": "Repository count and stars are shown for context only; they do not change your skill levels.",
    }
    link.status = "ok"
    link.note = f"Read {len(repos)} public repositories (forks skipped)."


def analyse_portfolio(link: ProfileLink) -> None:
    host = urlparse(link.url).hostname or ""
    if not _is_public(host):
        link.status, link.note = "invalid", "That address is not a public website."
        return
    try:
        r = httpx.get(link.url, timeout=6, follow_redirects=True, headers={"User-Agent": "CareerPilot-AI"})
        text = re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", " ", r.text[:500_000], flags=re.S)
        link.summary = {"page_text": re.sub(r"\s+", " ", text)[:4000]}
        link.status, link.note = ("ok", "Read the public page.") if r.status_code == 200 else             ("unavailable", f"The page answered {r.status_code}.")
    except httpx.HTTPError:
        link.status, link.note = "unavailable", "The page could not be opened. We continued without it."


def analyse_link(link: ProfileLink) -> None:
    link.last_checked = datetime.now(timezone.utc)
    if not link.consent:
        link.status, link.note = "not_checked", "Saved. We will not read it until you allow it."
        return
    if link.kind == "github" and settings.github_enabled:
        analyse_github(link)
    elif link.kind in ("portfolio", "other"):
        analyse_portfolio(link)
    else:
        link.status = "manual"
        link.note = ("We do not scrape this site. Paste your skills, courses or problem counts in the details box "
                     "and we will use them as claims.")
