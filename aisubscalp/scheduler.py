from __future__ import annotations

import logging
import time
from typing import Callable


def run_schedule(task: Callable[[], None], interval_minutes: int) -> None:
    logging.info("Scheduler started. Interval: %s minutes", interval_minutes)
    while True:
        start = time.time()
        task()
        elapsed = time.time() - start
        sleep_for = max(interval_minutes * 60 - elapsed, 5)
        logging.info("Next run in %.1f seconds", sleep_for)
        time.sleep(sleep_for)
