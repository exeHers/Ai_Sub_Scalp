from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class AppConfig:
    keywords: Dict[str, List[str]]
    queries: List[str]
    sources: Dict[str, Any]
    rate_limit_seconds: List[float]
    max_results_per_source: int


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_config(config_dir: Path) -> AppConfig:
    keywords = _load_json(config_dir / "keywords.json")
    sources = _load_json(config_dir / "sources.json")
    return AppConfig(
        keywords=keywords,
        queries=sources["search_queries"],
        sources=sources["sources"],
        rate_limit_seconds=sources.get("rate_limit_seconds", [1.0, 2.5]),
        max_results_per_source=sources.get("max_results_per_source", 60),
    )
