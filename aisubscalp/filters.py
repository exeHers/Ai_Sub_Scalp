from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Tuple

AI_KEYWORDS = [
    "ai",
    "artificial intelligence",
    "llm",
    "machine learning",
    "generative",
    "chatgpt",
]

FREE_SIGNALS = [
    "free trial",
    "try free",
    "free for",
    "free forever",
    "free tier",
    "free plan",
    "100% off",
    "free credits",
    "limited time free",
    "free to use",
]

OPEN_SOURCE_SIGNALS = [
    "open source",
    "self-hosted",
    "self hosted",
    "selfhosted",
]

STUDENT_SIGNALS = [
    "student",
    "edu discount",
    "education discount",
]

REFERRAL_SIGNALS = [
    "refer",
    "referral",
    "invite friends",
]

DISCOUNT_REGEX = re.compile(r"\b([1-9][0-9]?)%\s*(off|discount)\b")
SAVE_REGEX = re.compile(r"\bsave\s+[1-9][0-9]?%")
TRIAL_REGEX = re.compile(r"\b(\d{1,2})\s*(day|week|month)s?\b")
PROMO_CODE_REGEX = re.compile(r"\b[A-Z0-9]{6,16}\b")


@dataclass
class FilterResult:
    allowed: bool
    reason: str
    promo_type: Optional[str]
    trial_length: Optional[str]
    promo_code: Optional[str]


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _contains_discount(text: str) -> bool:
    if "100% off" in text:
        return False
    return bool(DISCOUNT_REGEX.search(text) or SAVE_REGEX.search(text))


def extract_trial_length(text: str) -> Optional[str]:
    match = TRIAL_REGEX.search(text)
    if not match:
        return None
    length, unit = match.groups()
    return f"{length} {unit}"


def extract_promo_code(text: str) -> Optional[str]:
    for code in PROMO_CODE_REGEX.findall(text.upper()):
        if code.isdigit():
            continue
        if code in {"PRICING", "SIGNUP", "ACCOUNT", "SUBSCRIBE"}:
            continue
        return code
    return None


def detect_promo_type(text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    if _contains_any(text, OPEN_SOURCE_SIGNALS):
        return "Open-Source", None, None
    if "free trial" in text or "try free" in text:
        return "Free Trial", extract_trial_length(text), None
    if "100% off" in text:
        return "100% Off", None, extract_promo_code(text)
    if "limited time free" in text:
        return "Free (Limited Time)", None, None
    if "free credits" in text:
        return "Free Credits", None, None
    if "free plan" in text or "free tier" in text or "free forever" in text:
        return "Free", None, None
    if "free to use" in text:
        return "Free", None, None
    return None, None, None


def apply_filters(text: str) -> FilterResult:
    lowered = text.lower()
    if not _contains_any(lowered, AI_KEYWORDS):
        return FilterResult(False, "Not AI-related", None, None, None)
    if _contains_any(lowered, STUDENT_SIGNALS):
        return FilterResult(False, "Student-only offer", None, None, None)
    if _contains_any(lowered, REFERRAL_SIGNALS):
        return FilterResult(False, "Referral requirement", None, None, None)
    if _contains_discount(lowered):
        return FilterResult(False, "Non-100% discount detected", None, None, None)
    if not (_contains_any(lowered, FREE_SIGNALS) or _contains_any(lowered, OPEN_SOURCE_SIGNALS)):
        return FilterResult(False, "No free/open-source signal", None, None, None)

    promo_type, trial_length, promo_code = detect_promo_type(lowered)
    if not promo_type:
        return FilterResult(False, "Unable to classify promo type", None, None, None)

    if "first-time" in lowered or "new customer" in lowered:
        if promo_type not in {"Free Trial", "100% Off"}:
            return FilterResult(False, "First-time only restriction", None, None, None)

    return FilterResult(True, "Accepted", promo_type, trial_length, promo_code)
