# AI Deals Hunter (Auto Scraper)

Next.js + Supabase app that scrapes AI websites daily to find:
- Free trials
- Free tiers
- Free credits
- Student discounts
- Promo codes (when visible)

## ✅ Setup

### 1) Supabase SQL
Run this in Supabase SQL Editor:

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