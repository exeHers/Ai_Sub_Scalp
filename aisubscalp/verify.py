from __future__ import annotations

import logging
from typing import List, Optional, Tuple

import requests

from .utils import RateLimiter, pick_user_agent


def verify_url(
    url: str, keywords: List[str], limiter: RateLimiter
) -> Tuple[str, Optional[str]]:
    limiter.wait()
    headers = {"User-Agent": pick_user_agent()}
    try:
        resp = requests.get(url, headers=headers, timeout=20)
    except requests.RequestException as exc:
        return "Unverified", f"Request failed: {exc}"

    if resp.status_code != 200:
        return "Unverified", f"HTTP {resp.status_code}"

    content = resp.text.lower()
    if any(keyword in content for keyword in keywords):
        return "Verified", None
    logging.debug("Verification keywords missing for %s", url)
    return "Unverified", "Verification keywords missing"
