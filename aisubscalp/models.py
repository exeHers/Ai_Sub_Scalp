from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class SourceItem:
    title: str
    url: str
    source: str
    snippet: str = ""
    category: str = "Unknown"
    discovered_at: str = field(default_factory=utc_now_iso)


@dataclass
class Deal:
    app_name: str
    website_url: str
    promo_type: str
    trial_length: Optional[str]
    requirements: Optional[str]
    promo_code: Optional[str]
    source_urls: List[str]
    date_found: str
    category: str
    notes: str
    verification_status: str
    verification_notes: Optional[str]
