import os
import json
import re
import time
import requests
from datetime import datetime, timezone
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

REST_HEADERS = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

# ===== SAFE LIMITS FOR GITHUB ACTIONS =====
MAX_TOOLS_PER_RUN = int(os.getenv("MAX_TOOLS_PER_RUN", "10"))
MAX_PATHS_PER_TOOL = int(os.getenv("MAX_PATHS_PER_TOOL", "6"))
GLOBAL_TIME_BUDGET = int(os.getenv("GLOBAL_TIME_BUDGET", "520"))
NAV_TIMEOUT_MS = int(os.getenv("NAV_TIMEOUT_MS", "25000"))
POST_WAIT_MS = int(os.getenv("POST_WAIT_MS", "350"))

# ===== FREE ONLY SIGNALS =====
FREE_KEYWORDS = [
    "free trial",
    "try for free",
    "start free",
    "get started free",
    "no credit card",
    "free tier",
    "free plan",
    "free forever",
    "100% off",
    "free to use"
]

# Reject discounts unless 100% off
DISCOUNT_PATTERNS = [
    r"\b\d{1,2}%\s*off\b",        # 10% off, 50% off, etc
    r"\bsave\s+\d{1,2}%\b",
    r"\bdiscount\b",
    r"\boff first month\b",
    r"\bpromo\b.*\bdiscount\b"
]

PROMO_REGEX = re.compile(r"\b[A-Z0-9]{6,16}\b")

COMMON_PATHS = [
    "",
    "/pricing",
    "/plans",
    "/upgrade",
    "/billing",
    "/student",
    "/education",
    "/promo",
    "/offers"
]

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def is_valid_http_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")

def contains_discount(text: str) -> bool:
    if "100% off" in text:
        return False
    for pat in DISCOUNT_PATTERNS:
        if re.search(pat, text):
            return True
    return False

def contains_free_signals(text: str) -> bool:
    return any(k in text for k in FREE_KEYWORDS)

def detect_deal_type(text: str) -> str:
    if "free forever" in text or "free tier" in text or "free plan" in text:
        return "Free Subscription"
    if "free trial" in text or "try for free" in text:
        return "Free Trial"
    if "100% off" in text:
        return "Promo Code"
    return "Free Deal"

def infer_deal_value(text: str) -> str:
    if "free forever" in text:
        return "Free Forever"
    if "no credit card" in text:
        return "No Credit Card Required"
    if "30-day" in text or "30 day" in text:
        return "30-Day Free Trial"
    if "14-day" in text or "14 day" in text:
        return "14-Day Free Trial"
    if "7-day" in text or "7 day" in text:
        return "7-Day Free Trial"
    if "free tier" in text or "free plan" in text:
        return "Free Subscription Available"
    if "free trial" in text:
        return "Free Trial Available"
    if "100% off" in text:
        return "100% Off Detected"
    return "Free offer detected"

def extract_promo_code(raw_text: str):
    # only accept promo code if it appears near "free" or "100% off"
    promo_candidates = list(set(PROMO_REGEX.findall(raw_text)))
    banned = {"PRICING", "UPGRADE", "ACCOUNT", "SIGNUP", "SUBSCRIBE", "CONTENT", "PRIVACY"}
    for c in promo_candidates:
        if c in banned:
            continue
        if c.isdigit():
            continue
        return c
    return None

def safe_goto(page, url: str) -> str:
    page.goto(url, wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)
    page.wait_for_timeout(POST_WAIT_MS)
    return page.inner_text("body")

def fetch_tools_batch():
    # Rotate by scanning tools with NULL last_scanned first, then oldest scanned
    endpoint = (
        f"{SUPABASE_URL}/rest/v1/tools"
        f"?select=tool_name,category,url"
        f"&order=last_scanned.asc.nullsfirst"
        f"&order=scan_priority.desc"
        f"&limit={MAX_TOOLS_PER_RUN}"
    )
    res = requests.get(endpoint, headers=REST_HEADERS, timeout=25)
    if res.status_code != 200:
        print("❌ Failed to fetch tools:", res.text)
        return []
    return res.json()

def mark_tool_scanned(url: str):
    endpoint = f"{SUPABASE_URL}/rest/v1/tools?url=eq.{url}"
    payload = {"last_scanned": now_iso()}
    try:
        requests.patch(endpoint, headers=REST_HEADERS, data=json.dumps(payload), timeout=20)
    except:
        pass

def supabase_upsert_deals(deals):
    endpoint = f"{SUPABASE_URL}/rest/v1/deals?on_conflict=tool_name,deal_type,deal_value"
    res = requests.post(endpoint, headers=REST_HEADERS, data=json.dumps(deals), timeout=25)
    if res.status_code not in [200, 201, 204]:
        print("❌ Supabase upsert failed:", res.text)
        return False
    print(f"✅ Upserted {len(deals)} free deals")
    return True

def extract_deal_from_url(tool, category, target_url, page):
    try:
        raw_text = safe_goto(page, target_url)
    except PlaywrightTimeoutError:
        print(f"⏭️ Timeout skip: {target_url}")
        return []
    except Exception as e:
        print(f"⏭️ Error skip: {target_url} | {e}")
        return []

    text = raw_text.lower()

    # must have free signals
    if not contains_free_signals(text):
        return []

    # reject discount-only pages
    if contains_discount(text):
        return []

    deal_type = detect_deal_type(text)
    deal_value = infer_deal_value(text)

    promo_code = None
    if "100% off" in text:
        promo_code = extract_promo_code(raw_text)

    if deal_type not in {"Free Subscription", "Free Trial", "Promo Code"}:
        return []
    if deal_type == "Promo Code" and "100% off" not in text:
        return []

    deal = {
        "tool_name": tool,
        "category": category,
        "deal_type": deal_type,
        "deal_value": deal_value,
        "promo_code": promo_code,
        "link": target_url,
        "source_url": target_url,
        "confidence_score": 95,
        "status": "active",
        "last_seen": now_iso()
    }

    print(f"✅ FREE FOUND: {tool} | {deal_type} | {deal_value} | code={promo_code or 'none'}")
    return [deal]

def main():
    start = time.time()

    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        print("❌ Missing Supabase secrets.")
        return
    if not is_valid_http_url(SUPABASE_URL):
        print("❌ Invalid SUPABASE_URL (must start with https://)")
        return

    tools = fetch_tools_batch()
    if not tools:
        print("❌ No tools to scan.")
        return

    all_deals = []
    scanned_urls = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(NAV_TIMEOUT_MS)

        for t in tools:
            if time.time() - start > GLOBAL_TIME_BUDGET:
                print("⏹️ Time budget reached. Ending early.")
                break

            tool_name = t.get("tool_name", "Unknown Tool")
            category = t.get("category", "Unknown")
            base_url = (t.get("url") or "").rstrip("/")

            if not base_url or not is_valid_http_url(base_url):
                print(f"⏭️ Invalid URL for {tool_name}: {base_url}")
                continue

            print(f"\n🔥 Scanning (FREE ONLY): {tool_name} ({category})")

            for path in COMMON_PATHS[:MAX_PATHS_PER_TOOL]:
                if time.time() - start > GLOBAL_TIME_BUDGET:
                    break

                target = base_url if path == "" else urljoin(base_url + "/", path.lstrip("/"))
                scanned_urls += 1
                all_deals.extend(extract_deal_from_url(tool_name, category, target, page))

            mark_tool_scanned(base_url)

        browser.close()

    if not all_deals:
        print(f"\n❌ No FREE deals found today. Scanned URLs: {scanned_urls}")
        return

    # Deduplicate
    unique = {}
    for d in all_deals:
        key = (d["tool_name"], d["deal_type"], d["deal_value"])
        unique[key] = d

    supabase_upsert_deals(list(unique.values()))

if __name__ == "__main__":
    main()
