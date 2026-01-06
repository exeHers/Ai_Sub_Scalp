from __future__ import annotations

import logging
import re
from html import unescape
from typing import Iterable, List, Optional
from urllib.parse import quote_plus, urlparse

import requests
from bs4 import BeautifulSoup

from .models import SourceItem
from .utils import RateLimiter, pick_user_agent

SOCIAL_DOMAINS = {
    "facebook.com",
    "twitter.com",
    "x.com",
    "instagram.com",
    "linkedin.com",
    "youtube.com",
    "tiktok.com",
    "discord.gg",
}


def _get(url: str, limiter: RateLimiter, timeout: int = 20) -> Optional[str]:
    limiter.wait()
    headers = {"User-Agent": pick_user_agent()}
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        if response.status_code != 200:
            logging.debug("Non-200 response %s for %s", response.status_code, url)
            return None
        return response.text
    except requests.RequestException as exc:
        logging.debug("Request failed for %s: %s", url, exc)
        return None


def _clean_url(url: str) -> str:
    url = unescape(url)
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return ""
    if any(domain in parsed.netloc for domain in SOCIAL_DOMAINS):
        return ""
    return url.split("#")[0]


def search_duckduckgo(query: str, limiter: RateLimiter, limit: int) -> List[SourceItem]:
    url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
    html = _get(url, limiter)
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    items: List[SourceItem] = []
    for result in soup.select("a.result__a"):
        href = result.get("href", "")
        title = result.get_text(strip=True)
        cleaned = _clean_url(href)
        if not cleaned:
            continue
        items.append(SourceItem(title=title, url=cleaned, source="duckduckgo", snippet=""))
        if len(items) >= limit:
            break
    return items


def search_reddit(subreddit: str, query: str, limiter: RateLimiter, limit: int) -> List[SourceItem]:
    url = (
        f"https://www.reddit.com/r/{subreddit}/search.json?"
        f"q={quote_plus(query)}&restrict_sr=1&sort=new&limit={limit}"
    )
    limiter.wait()
    headers = {"User-Agent": "aisubscalp/0.1"}
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.status_code != 200:
            return []
        payload = resp.json()
    except requests.RequestException:
        return []
    except ValueError:
        return []

    items: List[SourceItem] = []
    for child in payload.get("data", {}).get("children", []):
        data = child.get("data", {})
        title = data.get("title", "")
        permalink = data.get("url", "")
        if not title or not permalink:
            continue
        items.append(
            SourceItem(
                title=title,
                url=permalink,
                source=f"reddit/{subreddit}",
                snippet=data.get("selftext", "")[:280],
            )
        )
    return items


def search_hackernews(query: str, limiter: RateLimiter, limit: int) -> List[SourceItem]:
    url = (
        "https://hn.algolia.com/api/v1/search_by_date?"
        f"query={quote_plus(query)}&tags=story&hitsPerPage={limit}"
    )
    limiter.wait()
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code != 200:
            return []
        payload = resp.json()
    except (requests.RequestException, ValueError):
        return []

    items: List[SourceItem] = []
    for hit in payload.get("hits", []):
        title = hit.get("title") or ""
        url = hit.get("url") or ""
        if not title or not url:
            continue
        items.append(
            SourceItem(
                title=title,
                url=url,
                source="hackernews",
                snippet=hit.get("story_text") or "",
            )
        )
    return items


def search_producthunt_rss(feed_url: str, limiter: RateLimiter, limit: int) -> List[SourceItem]:
    xml = _get(feed_url, limiter)
    if not xml:
        return []
    soup = BeautifulSoup(xml, "xml")
    items: List[SourceItem] = []
    for item in soup.find_all("item"):
        title = item.title.text if item.title else ""
        link = item.link.text if item.link else ""
        if not title or not link:
            continue
        items.append(SourceItem(title=title, url=link, source="producthunt", snippet=""))
        if len(items) >= limit:
            break
    return items


def scrape_directory(url: str, limiter: RateLimiter, limit: int) -> List[SourceItem]:
    html = _get(url, limiter)
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    items: List[SourceItem] = []
    for link in soup.find_all("a", href=True):
        cleaned = _clean_url(link["href"])
        if not cleaned:
            continue
        title = link.get_text(strip=True) or cleaned
        items.append(SourceItem(title=title, url=cleaned, source="directory", snippet=""))
        if len(items) >= limit:
            break
    return items


def search_github(query: str, limiter: RateLimiter, limit: int, token: Optional[str]) -> List[SourceItem]:
    if not token:
        return []
    url = f"https://api.github.com/search/repositories?q={quote_plus(query)}&per_page={limit}"
    limiter.wait()
    headers = {"Authorization": f"Bearer {token}", "User-Agent": "aisubscalp/0.1"}
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.status_code != 200:
            return []
        payload = resp.json()
    except (requests.RequestException, ValueError):
        return []

    items: List[SourceItem] = []
    for repo in payload.get("items", []):
        name = repo.get("full_name") or ""
        link = repo.get("html_url") or ""
        description = repo.get("description") or ""
        if not name or not link:
            continue
        items.append(SourceItem(title=name, url=link, source="github", snippet=description))
    return items


def discover_all(
    queries: Iterable[str],
    sources: dict,
    limiter: RateLimiter,
    limit: int,
    github_token: Optional[str],
) -> List[SourceItem]:
    items: List[SourceItem] = []

    for query in queries:
        items.extend(search_duckduckgo(query, limiter, limit))

    for subreddit in sources.get("reddit", {}).get("subreddits", []):
        for query in sources.get("reddit", {}).get("queries", []):
            items.extend(search_reddit(subreddit, query, limiter, limit))

    for query in sources.get("hackernews", {}).get("queries", []):
        items.extend(search_hackernews(query, limiter, limit))

    for feed_url in sources.get("producthunt", {}).get("rss_feeds", []):
        items.extend(search_producthunt_rss(feed_url, limiter, limit))

    for url in sources.get("directories", []):
        items.extend(scrape_directory(url, limiter, limit))

    for query in sources.get("github", {}).get("queries", []):
        items.extend(search_github(query, limiter, limit, github_token))

    return items
