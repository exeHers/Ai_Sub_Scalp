from __future__ import annotations

import json
import logging
import random
import time
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Iterable

DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/121.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
]


class RateLimiter:
    def __init__(self, min_delay: float, max_delay: float):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self._last = 0.0

    def wait(self) -> None:
        now = time.time()
        elapsed = now - self._last
        delay = random.uniform(self.min_delay, self.max_delay)
        if elapsed < delay:
            time.sleep(delay - elapsed)
        self._last = time.time()


def pick_user_agent() -> str:
    return random.choice(DEFAULT_USER_AGENTS)


def setup_logging(log_path: Path, verbose: bool) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def to_json(obj: Any) -> str:
    def default(value: Any) -> Any:
        if is_dataclass(value):
            return asdict(value)
        if isinstance(value, Path):
            return str(value)
        return str(value)

    return json.dumps(obj, indent=2, ensure_ascii=True, default=default)


def unique_by(items: Iterable[Any], key_fn) -> list[Any]:
    seen = {}
    for item in items:
        key = key_fn(item)
        if key not in seen:
            seen[key] = item
    return list(seen.values())
