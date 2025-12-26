# AI Deals Hunter (Auto Scraper)

A Next.js + Supabase app that auto-scrapes the web daily for AI free trials, free tiers, credits, and promo codes (when available).

## ✅ How it works
- GitHub Actions runs `scripts/scraper.py` daily
- Uses Playwright to load JS websites
- Crawls stable pages like `/pricing`, `/plans`, `/student`, etc.
- Extracts offers + promo codes
- Upserts deals into Supabase
- Frontend fetches deals from Supabase

## ✅ Required setup
### Supabase SQL (run once)
```sql
create table if not exists deals (
  id uuid default gen_random_uuid() primary key,
  tool_name text not null,
  category text not null,
  deal_type text not null,
  deal_value text not null,
  promo_code text,
  link text not null,
  source_url text not null,
  confidence_score int default 50,
  status text default 'active',
  last_seen timestamp with time zone default now(),
  created_at timestamp with time zone default now()
);

alter table deals enable row level security;

create policy "Public read deals"
on deals for select
using (true);

alter table deals
add constraint deals_unique_key
unique (tool_name, deal_type, deal_value);
