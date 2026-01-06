from __future__ import annotations

import csv
from pathlib import Path
from typing import List

from .utils import to_json


def export_json(records: List[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(to_json(records), encoding="utf-8")


def export_csv(records: List[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not records:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0].keys()))
        writer.writeheader()
        for row in records:
            writer.writerow(row)
