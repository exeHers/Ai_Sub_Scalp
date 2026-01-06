from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

from .config import load_config
from .discovery import discover_all
from .exporter import export_csv, export_json
from .scan import build_deals, to_dicts
from .scheduler import run_schedule
from .storage import fetch_deals, init_db, upsert_deals
from .utils import RateLimiter, setup_logging


def _default_repo_root() -> Path:
    cwd = Path.cwd()
    if (cwd / "config").exists():
        return cwd
    return Path(__file__).resolve().parents[1]


def _default_config_dir() -> Path:
    return _default_repo_root() / "config"


def _default_db_path() -> Path:
    return _default_repo_root() / "data" / "aisubscalp.db"


def _default_log_path() -> Path:
    return _default_repo_root() / "logs" / "aisubscalp.log"


def scan_command(args: argparse.Namespace) -> None:
    config = load_config(Path(args.config_dir))
    limiter = RateLimiter(config.rate_limit_seconds[0], config.rate_limit_seconds[1])
    github_token = os.getenv("GITHUB_TOKEN")

    logging.info("Starting discovery...")
    items = discover_all(
        queries=config.queries,
        sources=config.sources,
        limiter=limiter,
        limit=config.max_results_per_source,
        github_token=github_token,
    )
    logging.info("Discovered %s candidate items", len(items))

    deals = build_deals(items, config, limiter)
    logging.info("Accepted %s deals after filtering", len(deals))

    conn = init_db(Path(args.db_path))
    upserted = upsert_deals(conn, deals)
    logging.info("Stored %s deals in SQLite", upserted)

    if args.export:
        records = to_dicts(deals)
        export_path = Path(args.export)
        if args.format == "json":
            export_json(records, export_path)
        else:
            export_csv(records, export_path)
        logging.info("Exported %s records to %s", len(records), export_path)


def export_command(args: argparse.Namespace) -> None:
    conn = init_db(Path(args.db_path))
    records = fetch_deals(conn)
    export_path = Path(args.output)
    if args.format == "json":
        export_json(records, export_path)
    else:
        export_csv(records, export_path)
    logging.info("Exported %s records to %s", len(records), export_path)


def run_command(args: argparse.Namespace) -> None:
    def task() -> None:
        scan_command(args)

    run_schedule(task, args.interval)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aisubscalp")
    parser.add_argument("--config-dir", default=str(_default_config_dir()))
    parser.add_argument("--db-path", default=str(_default_db_path()))
    parser.add_argument("--log-path", default=str(_default_log_path()))
    parser.add_argument("--verbose", action="store_true")

    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="Discover and scan sources")
    scan.add_argument("--export", help="Optional export path")
    scan.add_argument("--format", choices=["json", "csv"], default="json")
    scan.set_defaults(func=scan_command)

    export = subparsers.add_parser("export", help="Export from SQLite")
    export.add_argument("--output", required=True, help="Output file path")
    export.add_argument("--format", choices=["json", "csv"], default="json")
    export.set_defaults(func=export_command)

    run = subparsers.add_parser("run", help="Run scheduled scans")
    run.add_argument("--scheduled", action="store_true")
    run.add_argument("--interval", type=int, default=360)
    run.set_defaults(func=run_command)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    setup_logging(Path(args.log_path), args.verbose)
    if args.command == "run" and not args.scheduled:
        logging.error("Use --scheduled with run to start the scheduler.")
        return
    args.func(args)


if __name__ == "__main__":
    main()
