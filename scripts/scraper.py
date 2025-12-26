import os
import json
import re
import requests
from datetime import datetime, timezone
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

REST_HEADERS = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY or "",
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

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
    "free plan"
]

DEAL_TYPE_MAP = [
    ("free trial", "Free Trial"),
    ("promo code", "Promo Code"),
    ("coupon", "Promo Code"),
    ("discount", "Discount"),
    ("credits", "Credits"),
    ("free tier", "Free Tier"),
    ("free plan", "Free Tier"),
    ("try for free", "Free Trial"),
    ("get started free", "Free Tier"),
    ("student discount", "Student Discount")
]

PROMO_REGEX = re.compile(r"\b[A-Z0-9]{5,15}\b")

COMMON_PATHS = [
    "",
    "/pricing",
    "/plans",
    "/billing",
    "/subscription",
    "/upgrade",
    "/student",
    "/education",
    "/discount",
    "/promo",
    "/deal",
    "/offers"
]


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def confidence_score(url: str) -> int:
    official_domains = [
        "claude.ai", "midjourney.com", "perplexity.ai",
        "elevenlabs.io", "runwayml.com", "notion.so",
        "huggingface.co", "openai.com"
    ]
    if any(d in url for d in official_domains):
        return 95
    if "producthunt" in url or "appsumo" in url:
        return 80
    return 60


def detect_deal_type(text: str) -> str:
    for kw, label in DEAL_TYPE_MAP:
        if kw in text:
            return label
    return "Deal"


def infer_deal_value(text: str) -> str:
    if "7-day" in text or "7 day" in text:
        return "7-Day Free Trial"
    if "14-day" in text or "14 day" in text:
        return "14-Day Free Trial"
    if "30-day" in text or "30 day" in text:
        return "30-Day Free Trial"
    if "50%" in text:
        return "50% Discount Detected"
    if "free" in text and "trial" in text:
        return "Free Trial Detected"
    if "free tier" in text or "free plan" in text:
        return "Free Tier Available"
    if "credits" in text:
        return "Free Credits Available"
    return "Offer detected on site"


def extract_promo_code(raw_text: str):
    candidates = list(set(PROMO_REGEX.findall(raw_text)))
    candidates = [c for c in candidates if not c.isdigit() and len(c) >= 6]
    return candidates[:2] if candidates else []


def scrape_visible_text(page, url: str) -> str:
    page.goto(url, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(1500)
    return page.inner_text("body")


def extract_deal_from_url(tool_name, category, target_url, page):
    deals = []
    try:
        raw_text = scrape_visible_text(page, target_url)
        text = raw_text.lower()

        found_keywords = [kw for kw in KEYWORDS if kw in text]
        if not found_keywords:
            return deals

        deal_type = detect_deal_type(text)
        deal_value = infer_deal_value(text)

        promo_candidates = extract_promo_code(raw_text)
        promo_code = promo_candidates[0] if promo_candidates else None

        deals.append({
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
        })

        print(f"✅ Deal found: {tool_name} | {deal_type} | {deal_value} | code={promo_code}")

    except Exception as e:
        print(f"⚠️ Failed scraping {target_url}: {e}")

    return deals


def supabase_upsert(deals):
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise Exception("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")

    endpoint = f"{SUPABASE_URL}/rest/v1/deals?on_conflict=tool_name,deal_type,deal_value"

    res = requests.post(endpoint, headers=REST_HEADERS, data=json.dumps(deals))
    if res.status_code not in [200, 201, 204]:
        print("❌ Supabase error:", res.text)
        raise Exception("Supabase upsert failed")

    print(f"✅ Upserted {len(deals)} deals")


def main():
    with open("sources.json", "r", encoding="utf-8") as f:
        sources = json.load(f)

    all_deals = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(60000)

        for src in sources:
            tool_name = src["tool_name"]
            category = src["category"]
            base_url = src["url"].rstrip("/")

            print(f"\n🔥 Scanning tool: {tool_name}")

            for path in COMMON_PATHS:
                target_url = base_url if path == "" else urljoin(base_url + "/", path.lstrip("/"))
                all_deals.extend(extract_deal_from_url(tool_name, category, target_url, page))

        browser.close()

    if not all_deals:
        print("❌ No deals detected today.")
        return

    unique = {}
    for d in all_deals:
        key = (d["tool_name"], d["deal_type"], d["deal_value"])
        unique[key] = d

    supabase_upsert(list(unique.values()))


if __name__ == "__main__":
    main()