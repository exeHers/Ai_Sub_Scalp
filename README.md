# AI Sub Scalp

Production-ready tool that discovers and tracks AI app promotions with strict filters.

## What It Finds
- Free trials (any duration)
- Free credits that enable full access (heuristic-based)
- 100% discount promo codes
- Free for limited time
- Completely free plans
- Open-source and self-hostable AI apps

## What It Rejects
- Any discount less than 100%
- Student-only offers
- Referral-only free offers
- Non-AI products

## Quick Start

### 1) Install
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

### 2) Run a Scan
```bash
aisubscalp scan
```

### 3) Export
```bash
aisubscalp export --format json --output outputs/deals.json
aisubscalp export --format csv --output outputs/deals.csv
```

### 4) Scheduled Runs
```bash
aisubscalp run --scheduled --interval 360
```

## Configuration

Config files live in `config/`:
- `config/sources.json` for sources and query templates
- `config/keywords.json` for verification keywords and categories

You can override the config directory:
```bash
aisubscalp --config-dir config scan
```

## Data Storage

SQLite DB is created at `data/aisubscalp.db` by default. The schema enforces unique
records by app name + promo type + website URL.

## Output Schema

Each deal is normalized to:
- app_name
- website_url
- promo_type
- trial_length
- requirements
- promo_code
- source_urls
- date_found
- category
- notes
- verification_status
- verification_notes

Examples are in `examples/`.

## Environment Variables

- `GITHUB_TOKEN` (optional) enables GitHub search via API.

## Docker
```bash
docker compose up --build
```

## Development
```bash
pip install -r requirements-dev.txt
pytest
ruff check aisubscalp tests
black aisubscalp tests
```

## CLI Commands

```bash
aisubscalp scan
aisubscalp export --format json|csv --output <path>
aisubscalp run --scheduled --interval <minutes>
```

## Notes

- Scraping is rate-limited and uses rotating user-agents.
- Verification is lightweight: HTTP 200 + keyword check.
- If verification fails, the deal is stored as Unverified.
