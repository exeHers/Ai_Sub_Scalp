from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable, List

from .models import Deal


SCHEMA = """
create table if not exists deals (
    id integer primary key autoincrement,
    app_name text not null,
    website_url text not null,
    promo_type text not null,
    trial_length text,
    requirements text,
    promo_code text,
    source_urls text not null,
    date_found text not null,
    category text not null,
    notes text not null,
    verification_status text not null,
    verification_notes text
);
create unique index if not exists deals_unique
on deals (app_name, promo_type, website_url);
"""


def init_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.executescript(SCHEMA)
    return conn


def upsert_deals(conn: sqlite3.Connection, deals: Iterable[Deal]) -> int:
    rows = 0
    for deal in deals:
        conn.execute(
            """
            insert into deals (
                app_name, website_url, promo_type, trial_length, requirements,
                promo_code, source_urls, date_found, category, notes,
                verification_status, verification_notes
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            on conflict(app_name, promo_type, website_url) do update set
                trial_length=excluded.trial_length,
                requirements=excluded.requirements,
                promo_code=excluded.promo_code,
                source_urls=excluded.source_urls,
                date_found=excluded.date_found,
                category=excluded.category,
                notes=excluded.notes,
                verification_status=excluded.verification_status,
                verification_notes=excluded.verification_notes
            """,
            (
                deal.app_name,
                deal.website_url,
                deal.promo_type,
                deal.trial_length,
                deal.requirements,
                deal.promo_code,
                json.dumps(deal.source_urls, ensure_ascii=True),
                deal.date_found,
                deal.category,
                deal.notes,
                deal.verification_status,
                deal.verification_notes,
            ),
        )
        rows += 1
    conn.commit()
    return rows


def fetch_deals(conn: sqlite3.Connection) -> List[dict]:
    cursor = conn.execute(
        """
        select app_name, website_url, promo_type, trial_length, requirements,
               promo_code, source_urls, date_found, category, notes,
               verification_status, verification_notes
        from deals
        order by date_found desc
        """
    )
    rows = []
    for row in cursor.fetchall():
        rows.append(
            {
                "app_name": row[0],
                "website_url": row[1],
                "promo_type": row[2],
                "trial_length": row[3],
                "requirements": row[4],
                "promo_code": row[5],
                "source_urls": json.loads(row[6]),
                "date_found": row[7],
                "category": row[8],
                "notes": row[9],
                "verification_status": row[10],
                "verification_notes": row[11],
            }
        )
    return rows
