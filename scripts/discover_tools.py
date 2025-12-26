import os
import re
import json
import requests
from datetime import datetime, timezone

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

REST_HEADERS = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

DISCOVERY_SOURCES = [
    "https://theresanaiforthat.com/",
    "https://www.futurepedia.io/",
    "https://www.aitoolhunt.com/"
]

URL_REGEX = re.compile(r"https?://[^\s\"'>]+", re.IGNORECASE)

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def is_valid_http_url(url: str) -> bool:
    return url.startswith("http://") or url.startswith("https://")

def should_skip(url: str) -> bool:
    bad = [
        "google.com", "facebook.com", "twitter.com", "x.com",
        "instagram.com", "linkedin.com", "youtube.com", "tiktok.com",
        "mailto:", "discord.gg"
    ]
    return any(b in url for b in bad)

def upsert_tools(tools):
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        print("❌ Missing Supabase secrets.")
        return

    endpoint = f"{SUPABASE_URL}/rest/v1/tools?on_conflict=url"
    res = requests.post(endpoint, headers=REST_HEADERS, data=json.dumps(tools), timeout=25)

    if res.status_code not in [200, 201, 204]:
        print("❌ Supabase error:", res.status_code, res.text)
        return

    print(f"✅ Upserted {len(tools)} tools into Supabase")

def extract_urls(html: str):
    urls = set(URL_REGEX.findall(html))
    cleaned = []

    for u in urls:
        u = u.strip().rstrip("/")
        if not is_valid_http_url(u):
            continue
        if should_skip(u):
            continue
        if len(u) < 15:
            continue
        cleaned.append(u)

    return list(set(cleaned))[:250]

def main():
    all_tools = []

    for src in DISCOVERY_SOURCES:
        print(f"\n🔎 Discovering from: {src}")
        try:
            html = requests.get(src, timeout=25, headers={"User-Agent": "Mozilla/5.0"}).text
        except Exception as e:
            print(f"⚠️ Failed to fetch {src}: {e}")
            continue

        urls = extract_urls(html)

        for u in urls:
            tool_name = u.split("//")[-1].split("/")[0].replace("www.", "")
            all_tools.append({
                "tool_name": tool_name.title(),
                "category": "Unknown",
                "url": u,
                "source": src,
                "discovered_at": now_iso(),
                "scan_priority": 50
            })

    if not all_tools:
        print("❌ No tools discovered today.")
        return

    unique = {}
    for t in all_tools:
        unique[t["url"]] = t

    print(f"\n✅ Tools discovered (unique): {len(unique)}")
    upsert_tools(list(unique.values()))

if __name__ == "__main__":
    main()