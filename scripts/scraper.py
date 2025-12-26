import os
import json
import re
import time
import requests
from datetime import datetime, timezone
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# =========================
# ENV / CONFIG
# =========================
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

# Max tools to scan per run (prevents GitHub cancel)
MAX_TOOLS_PER_RUN = int(os.getenv("MAX_TOOLS_PER_RUN", "6"))

# Max paths per tool to scan (prevents runaway)
MAX_PATHS_PER_TOOL = int(os.getenv("MAX_PATHS_PER_TOOL", "6"))

# Hard global time budget for the whole run (seconds)
GLOBAL_TIME_BUDGET = int(os.getenv("GLOBAL_TIME_BUDGET", "520"))  # ~8.5 mins

# Page navigation timeout (ms)
NAV_TIMEOUT_MS = int(os.getenv("NAV_TIMEOUT_MS", "25000"))

# Additional "post-load" wait (ms)
POST_WAIT_MS = int(os.getenv("POST_WAIT_MS", "400"))

# =========================
# SUPABASE REST HEADERS
# =========================
REST_HEADERS = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

# =========================
# KEYWORDS / DETECTION
# =========================
KEYWORDS = [
    "free trial",
    "promo code",
    "discount",
    "coupon",
    "free tier",
    "credits",
    "get started free",
    "try for free",
    "trial",
    "limited offer",
    "student discount",
    "education discount",
    "free plan",
    "sign up free",
    "start free",
    "first month free",
]

DEAL_TYPE_MAP = [
    ("student discount", "Student Discount"),
    ("education discount", "Student Discount"),
    ("promo code", "Promo Code"),
    ("coupon", "Promo Code"),
    ("free trial", "Free Trial"),
    ("try for free", "Free Trial"),
    ("first month free", "Free Trial"),
    ("free tier", "Free Tier"),
    ("free plan", "Free Tier"),
    ("credits", "Credits"),
    ("discount", "Discount"),
]

PROMO_REGEX = re.compile(r"\b[A-Z0-9]{6,16}\b")  # slightly stricter

# Most useful paths (keep short)
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

# =========================
# HELPERS
# =========================
def now_iso():
    return datetime.now(timezone.utc).isoformat()

def is_valid_http_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")

def confidence_score(url: str) -> int:
    # domain-based heuristic
    official_domains = [
        "claude.ai", "midjourney.com", "perplexity.ai",
        "elevenlabs.io", "runwayml.com", "notion.so",
        "huggingface.co", "openai.com"
    ]
    if any(d in url for d in official_domains):
        return 95
    if "producthunt" in url or "appsumo" in url:
        return 80
    return 65

def detect_deal_type(text: str) -> str:
    for kw, label in DEAL_TYPE_MAP:
        if kw in text:
            return label
    return "Deal"

def infer_deal_value(text: str) -> str:
    # Simple heuristics
    if "30-day" in text or "30 day" in text:
        return "30-Day Free Trial"
    if "14-day" in text or "14 day" in text:
        return "14-Day Free Trial"
    if "7-day" in text or "7 day" in text:
        return "7-Day Free Trial"
    if "50%" in text:
        return "50% Discount Detected"
    if "first month free" in text:
        return "First Month Free"
    if "free trial" in text or "try for free" in text:
        return "Free Trial Detected"
    if "free tier" in text or "free plan" in text:
        return "Free Tier Available"
    if "credits" in text:
        return "Free Credits Available"
    if "student discount" in text or "education discount" in text:
        return "Student Discount Mentioned"
    return "Offer detected on site"

def extract_promo_code(raw_text: str):
    candidates = list(set(PROMO_REGEX.findall(raw_text)))
    # filter obvious junk
    banned = {"PRICING", "UPGRADE", "SUBSCRIBE", "SIGNUP", "ACCOUNT", "SUPABASE"}
    cleaned = []
    for c in candidates:
        if c.isdigit():
            continue
        if c in banned:
            continue
        if len(c) < 6:
            continue
        cleaned.append(c)
    return cleaned[:1]  # only keep best candidate

def supabase_upsert(deals):
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY (Secrets misconfigured)")
        return

    if not is_valid_http_url(SUPABASE_URL):
        print("❌ Invalid SUPABASE_URL. Must start with https://")
        return

    endpoint = f"{SUPABASE_URL}/rest/v1/deals?on_conflict=tool_name,deal_type,deal_value"

    try:
        res = requests.post(endpoint, headers=REST_HEADERS, data=json.dumps(deals), timeout=25)
        if res.status_code not in [200, 201, 204]:
            print("❌ Supabase error:", res.status_code, res.text)
            return
        print(f"✅ Upserted {len(deals)} deals into Supabase")
    except Exception as e:
        print("❌ Supabase request failed:", str(e))

# =========================
# SCRAPING
# =========================
def safe_goto(page, url: str) -> str:
    """
    Faster + safer navigation:
    - domcontentloaded avoids networkidle hangs
    - strict timeout
    """
    page.goto(url, wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)
    page.wait_for_timeout(POST_WAIT_MS)
    return page.inner_text("body")

def extract_deal_from_url(tool_name, category, target_url, page):
    try:
        raw_text = safe_goto(page, target_url)
    except PlaywrightTimeoutError:
        print(f"⏭️ Timeout skip: {target_url}")
        return []
    except Exception as e:
        print(f"⏭️ Error skip: {target_url} | {e}")
        return []

    text = raw_text.lower()

    found = [kw for kw in KEYWORDS if kw in text]
    if not found:
        return []

    deal_type = detect_deal_type(text)
    deal_value = infer_deal_value(text)
    promo = extract_promo_code(raw_text)
    promo_code = promo[0] if promo else None

    deal = {
        "tool_name": tool_name,
        "category": category,
        "deal_type": deal_type,
        "deal_value": deal_value,
        "promo_code": promo_code,
        "link": target_url,
        "source_url": target_url,
        "confidence_score": confidence_score(target_url),
        "status": "active",
        "last_seen": now_iso()
    }

    print(f"✅ FOUND: {tool_name} | {deal_type} | {deal_value} | code={promo_code or 'none'}")
    return [deal]

def main():
    start_time = time.time()

    # Validate secrets
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        print("❌ Missing Supabase secrets. Add them in GitHub → Settings → Actions → Secrets.")
        return

    if not is_valid_http_url(SUPABASE_URL):
        print("❌ Invalid SUPABASE_URL: must start with https://")
        return

    # Load sources
    with open("sources.json", "r", encoding="utf-8") as f:
        sources = json.load(f)

    # Limit total work per run (prevents GH cancel)
    sources = sources[:MAX_TOOLS_PER_RUN]

    all_deals = []
    scanned = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(NAV_TIMEOUT_MS)

        for src in sources:
            # Global time budget check
            if time.time() - start_time > GLOBAL_TIME_BUDGET:
                print("⏹️ Global time budget reached. Ending run early to avoid GitHub cancel.")
                break

            tool_name = src.get("tool_name", "Unknown Tool")
            category = src.get("category", "Unknown")
            base_url = (src.get("url") or "").strip().rstrip("/")

            if not base_url or not is_valid_http_url(base_url):
                print(f"⏭️ Invalid base URL for {tool_name}: {base_url}")
                continue

            print(f"\n🔥 Scanning: {tool_name} ({category})")

            paths = COMMON_PATHS[:MAX_PATHS_PER_TOOL]

            for path in paths:
                if time.time() - start_time > GLOBAL_TIME_BUDGET:
                    print("⏹️ Global time budget reached mid-scan. Exiting.")
                    break

                target_url = base_url if path == "" else urljoin(base_url + "/", path.lstrip("/"))
                scanned += 1

                deals = extract_deal_from_url(tool_name, category, target_url, page)
                if deals:
                    all_deals.extend(deals)

        browser.close()

    if not all_deals:
        print("\n❌ No deals detected in this run.")
        print(f"Scanned URLs: {scanned}")
        return

    # Deduplicate
    unique = {}
    for d in all_deals:
        key = (d["tool_name"], d["deal_type"], d["deal_value"])
        unique[key] = d

    print(f"\n✅ Deals found (unique): {len(unique)} | scanned URLs: {scanned}")
    supabase_upsert(list(unique.values()))

if __name__ == "__main__":
    main()