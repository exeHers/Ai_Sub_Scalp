from __future__ import annotations

import logging
import os
from dataclasses import asdict
from typing import Iterable, List
from urllib.parse import urlparse

from .config import AppConfig
from .filters import apply_filters
from .models import Deal, SourceItem, utc_now_iso
from .utils import RateLimiter, unique_by
from .verify import verify_url


def infer_category(text: str, keywords: dict) -> str:
    lowered = text.lower()
    for category, terms in keywords.get("categories", {}).items():
        if any(term in lowered for term in terms):
            return category
    return "Unknown"


def infer_requirements(text: str) -> str | None:
    lowered = text.lower()
    if "no credit card" in lowered:
        return "No credit card required"
    if "signup" in lowered or "sign up" in lowered:
        return "Signup required"
    return None


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return url
    return f"{parsed.scheme}://{parsed.netloc}"


def build_deal(item: SourceItem, config: AppConfig, limiter: RateLimiter) -> Deal | None:
    text_blob = " ".join([item.title, item.snippet or "", item.url]).strip()
    result = apply_filters(text_blob)
    if not result.allowed:
        logging.debug("Rejected: %s (%s)", item.title, result.reason)
        return None

    verification_status, verification_notes = verify_url(
        item.url, config.keywords["verification_keywords"], limiter
    )
    category = infer_category(text_blob, config.keywords)
    requirements = infer_requirements(text_blob)
    notes = f"{item.source}: {item.title}"

    return Deal(
        app_name=item.title[:140],
        website_url=normalize_url(item.url),
        promo_type=result.promo_type or "Free",
        trial_length=result.trial_length,
        requirements=requirements,
        promo_code=result.promo_code,
        source_urls=[item.url],
        date_found=utc_now_iso(),
        category=category,
        notes=notes,
        verification_status=verification_status,
        verification_notes=verification_notes,
    )


def build_deals(items: Iterable[SourceItem], config: AppConfig, limiter: RateLimiter) -> List[Deal]:
    deals: List[Deal] = []
    for item in items:
        deal = build_deal(item, config, limiter)
        if deal:
            deals.append(deal)
    return unique_by(deals, lambda d: (d.app_name, d.promo_type, d.website_url))


def to_dicts(deals: Iterable[Deal]) -> list[dict]:
    return [asdict(deal) for deal in deals]
