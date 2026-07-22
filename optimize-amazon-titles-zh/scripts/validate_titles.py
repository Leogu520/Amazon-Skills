#!/usr/bin/env python3
"""Validate Amazon title candidates without external dependencies."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.1"
POLICY_BASELINE_DATE = "2026-07-21"
DEFAULT_MAX_CHARS = 75
DEFAULT_ITEM_HIGHLIGHTS_MAX_CHARS = 125
RESTRICTED_CHARACTERS = set("!$?_{}^¬¦")

STOPWORDS = {
    "en": {"a", "an", "and", "or", "for", "the", "of", "in", "on", "with", "to", "by", "from", "at"},
    "de": {"der", "die", "das", "den", "dem", "des", "ein", "eine", "und", "oder", "für", "mit", "von", "zu", "im", "in", "auf"},
    "fr": {"le", "la", "les", "un", "une", "des", "de", "du", "et", "ou", "pour", "avec", "dans", "sur"},
    "es": {"el", "la", "los", "las", "un", "una", "de", "del", "y", "o", "para", "con", "en", "por"},
    "it": {"il", "lo", "la", "i", "gli", "le", "un", "una", "di", "del", "e", "o", "per", "con", "in", "su"},
}

PROMOTIONAL_PATTERNS = {
    "price or discount language": re.compile(r"\b(?:sale|discount|coupon|deal|save\s+\d+%|\d+%\s+off)\b", re.I),
    "urgency language": re.compile(r"\b(?:limited\s+time|today\s+only|last\s+chance|hurry)\b", re.I),
    "shipping promotion": re.compile(r"\b(?:free\s+shipping|ships?\s+free)\b", re.I),
    "ranking claim": re.compile(r"\b(?:best\s*seller|no\.?\s*1|#1|top[- ]rated)\b", re.I),
}

SUBJECTIVE_PATTERNS = {
    "subjective quality claim": re.compile(r"\b(?:best|amazing|perfect|ultimate|premium\s+quality|high\s+quality|superior)\b", re.I),
}

CLAIM_DEFINITIONS = {
    "bpa_free": ("BPA-free", re.compile(r"\bBPA[ -]?free\b", re.I), {"bpa-free", "bpa free"}),
    "non_toxic": ("non-toxic", re.compile(r"\bnon[ -]?toxic\b", re.I), {"non-toxic", "non toxic"}),
    "food_safe": ("food-safe", re.compile(r"\bfood[ -]?safe\b", re.I), {"food-safe", "food safe"}),
    "child_safe": ("child-safe", re.compile(r"\bchild[ -]?safe\b", re.I), {"child-safe", "child safe"}),
    "waterproof": ("waterproof claim", re.compile(r"\bwaterproof\b|\bIP\d{2}\b", re.I), {"waterproof", "waterproof claim"}),
    "organic": ("organic claim", re.compile(r"\borganic\b", re.I), {"organic", "organic claim"}),
    "hypoallergenic": ("hypoallergenic claim", re.compile(r"\bhypoallergenic\b", re.I), {"hypoallergenic", "hypoallergenic claim"}),
    "clinical": ("clinical claim", re.compile(r"\bclinically\s+(?:proven|tested)\b", re.I), {"clinical", "clinical claim"}),
    "medical_approval": ("medical or approval claim", re.compile(r"\b(?:medical[ -]?grade|FDA[ -]?approved)\b", re.I), {"medical approval", "medical or approval claim"}),
    "environmental": ("environmental claim", re.compile(r"\b(?:eco[ -]?friendly|sustainable|recyclable)\b", re.I), {"environmental", "environmental claim"}),
    "antimicrobial": ("antimicrobial claim", re.compile(r"\bantimicrobial\b", re.I), {"antimicrobial", "antimicrobial claim"}),
    "fire_performance": ("fire performance claim", re.compile(r"\b(?:fireproof|flame[ -]?resistant)\b", re.I), {"fire performance", "fire performance claim"}),
    "age_life_stage": (
        "age or life-stage claim",
        re.compile(r"\b(?:newborn|infant|toddler|ages?\s*\d+\+?|\d+\s*(?:months?|mos?|years?|yrs?)\s*(?:and\s+up|\+|old)?)\b", re.I),
        {"age", "life stage", "age or life-stage claim"},
    ),
    "certification_compliance": (
        "certification or compliance claim",
        re.compile(r"\b(?:certified|compliant|(?<!clinically )tested|(?<!FDA[ -])approved)\b", re.I),
        {"certification", "compliance", "certification or compliance claim"},
    ),
    "educational_positioning": (
        "educational or STEM claim",
        re.compile(r"\b(?:educational|STEM)(?:-focused)?\b", re.I),
        {"educational", "stem", "educational or stem claim"},
    ),
    "performance_duration": (
        "performance duration claim",
        re.compile(r"\b(?:keeps?|lasts?|runtime|battery\s+life)[^,;]{0,30}\d+(?:\.\d+)?\s*(?:hours?|hrs?|minutes?|mins?|days?)\b", re.I),
        {"performance duration", "performance duration claim"},
    ),
}

RELATIONSHIP_BRANDS = re.compile(r"\b(?:compatible\s+with|fits?|replacement\s+for|designed\s+for)\b", re.I)
WORD_RE = re.compile(r"[^\W_]+(?:[-'][^\W_]+)*", re.UNICODE)
NON_ENGLISH_SCRIPT_PREFIXES = (
    "ARABIC",
    "ARMENIAN",
    "BENGALI",
    "CYRILLIC",
    "DEVANAGARI",
    "GEORGIAN",
    "GREEK",
    "GUJARATI",
    "GURMUKHI",
    "HANGUL",
    "HEBREW",
    "HIRAGANA",
    "KATAKANA",
    "THAI",
)
MEDIA_PRODUCT_TYPES = {"ABIS_BOOK", "BOOK", "BOOKS", "DVD"}
SAFETY_SENSITIVE_PRODUCT_TYPES = {
    "BABY_CARRIER": "Baby carrier Product Type requires safety and source-data review",
    "BABY_CRIB": "Baby sleep Product Type requires safety and source-data review",
    "BATTERY": "Battery Product Type requires electrical-safety and performance review",
    "BATTERY_CHARGER": "Battery charger Product Type requires electrical-safety and compatibility review",
    "CHARGING_ADAPTER": "Charging adapter Product Type requires electrical-safety and protocol review",
    "DIETARY_SUPPLEMENT": "Supplement Product Type requires regulated-claim review",
    "HIGH_CHAIR": "Baby feeding Product Type requires safety and source-data review",
    "INFANT_CAR_SEAT": "Child-restraint Product Type requires safety and fitment review",
    "MEDICAL_DEVICE": "Medical-device Product Type requires regulated-claim review",
}
MARKETPLACE_ALIASES = {
    "US": "US",
    "USA": "US",
    "ATVPDKIKX0DER": "US",
    "UK": "UK",
    "GB": "UK",
    "A1F83G8C2ARO7P": "UK",
}
VERIFIED_POLICY_CONTEXTS = {
    ("US", "en_US"): "https://sellercentral.amazon.com/seller-forums/discussions/t/145b6d0f-999c-4555-896c-c694bda2e470",
    ("UK", "en_GB"): "https://sellercentral.amazon.co.uk/seller-forums/discussions/t/33f0a42a-17f1-46ef-b110-ba7512a3c881",
}


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def split_terms(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [part.strip() for part in re.split(r"[|;\n]+", str(value)) if part.strip()]


def normalize_identifier(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold().strip()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def normalize_locale(value: Any) -> str:
    parts = str(value or "").strip().replace("-", "_").split("_")
    if len(parts) == 2 and all(parts):
        return f"{parts[0].lower()}_{parts[1].upper()}"
    return str(value or "").strip().replace("-", "_")


def canonical_claim_ids(values: list[str]) -> set[str]:
    aliases: dict[str, str] = {}
    for claim_id, (label, _pattern, claim_aliases) in CLAIM_DEFINITIONS.items():
        for alias in {claim_id, label, *claim_aliases}:
            aliases[normalize_identifier(alias)] = claim_id
    return {aliases[key] for value in values if (key := normalize_identifier(value)) in aliases}


def locale_language(locale: str) -> str:
    language = (locale or "en").split("_")[0].split("-")[0].lower()
    return language if language in STOPWORDS else "en"


def parse_positive_int(value: Any, default: int) -> tuple[int, bool]:
    text = str(value or "").strip()
    safe_default = default if isinstance(default, int) and default > 0 else DEFAULT_MAX_CHARS
    if not text:
        return safe_default, True
    if text.casefold() == "exempt":
        return safe_default, True
    if not text.isdigit() or int(text) <= 0:
        return safe_default, False
    return int(text), True


def duplicate_words(title: str, locale: str) -> list[str]:
    stopwords = STOPWORDS[locale_language(locale)]
    counts: dict[str, int] = {}
    for token in WORD_RE.findall(title.casefold()):
        if token in stopwords:
            continue
        counts[token] = counts.get(token, 0) + 1
    return sorted(word for word, count in counts.items() if count > 2)


def is_deterministic_english(title: str, locale: str) -> bool:
    if not locale.lower().replace("-", "_").startswith("en_"):
        return False
    for char in title:
        if "CJK" in unicodedata.name(char, ""):
            return False
        if unicodedata.name(char, "").startswith(NON_ENGLISH_SCRIPT_PREFIXES):
            return False
    return True


def policy_context(row: dict[str, Any], max_chars: int, highlights_max_chars: int) -> dict[str, Any]:
    marketplace_raw = str(row.get("marketplace") or "").strip()
    marketplace = MARKETPLACE_ALIASES.get(marketplace_raw.upper(), marketplace_raw.upper())
    locale = normalize_locale(row.get("locale") or row.get("marketplace_locale"))
    product_type = normalize_identifier(row.get("product_type")).upper()
    parentage_level = normalize_identifier(row.get("parentage_level"))
    source = VERIFIED_POLICY_CONTEXTS.get((marketplace, locale))
    complete = bool(marketplace and locale and product_type and parentage_level)
    parentage_valid = parentage_level in {"standalone", "parent", "child"}
    verified = bool(source and complete and parentage_valid)
    return {
        "marketplace": marketplace or None,
        "locale": locale or None,
        "product_type": product_type or None,
        "parentage_level": parentage_level or None,
        "title_max_chars": max_chars,
        "item_highlights_max_chars": highlights_max_chars,
        "baseline_verified_at": POLICY_BASELINE_DATE,
        "verified": verified,
        "source": source,
    }


def analyze_title(row: dict[str, Any], default_max_chars: int = DEFAULT_MAX_CHARS) -> dict[str, Any]:
    title = str(row.get("title") or "")
    stripped = title.strip()
    item_highlights = str(row.get("item_highlights") or "")
    stripped_highlights = item_highlights.strip()
    brand = str(row.get("brand") or "").strip()
    locale = normalize_locale(row.get("locale") or row.get("marketplace_locale"))
    analysis_locale = locale or "en_US"
    requested_media_exempt = truthy(row.get("media_exempt"))
    max_chars, max_chars_valid = parse_positive_int(row.get("max_chars"), default_max_chars)
    highlights_max_chars, highlights_max_valid = parse_positive_int(
        row.get("item_highlights_max_chars"), DEFAULT_ITEM_HIGHLIGHTS_MAX_CHARS
    )
    required_phrases = split_terms(row.get("required_phrases"))
    verified_claim_values = split_terms(row.get("verified_claims"))
    verified_claim_ids = canonical_claim_ids(verified_claim_values)
    context = policy_context(row, max_chars, highlights_max_chars)
    deterministic_english = is_deterministic_english(stripped, analysis_locale)
    recognized_media = context["product_type"] in MEDIA_PRODUCT_TYPES
    media_exemption_applied = bool(recognized_media and context["verified"])

    errors: list[str] = []
    warnings: list[str] = []
    risk_codes: list[str] = []
    review_reasons: list[str] = []

    def add_risk(code: str, reason: str) -> None:
        if code not in risk_codes:
            risk_codes.append(code)
        if reason not in review_reasons:
            review_reasons.append(reason)

    if not context["marketplace"]:
        add_risk("MISSING_MARKETPLACE", "Marketplace is required to verify the applicable title policy")
    if not context["locale"]:
        add_risk("MISSING_LOCALE", "Locale is required to verify language and marketplace rules")
    if not context["product_type"]:
        add_risk("MISSING_PRODUCT_TYPE", "Product Type is required to verify schema and media treatment")
    if not context["parentage_level"]:
        add_risk("MISSING_PARENTAGE_LEVEL", "Parentage level is required to review variation-specific title facts")
    elif context["parentage_level"] not in {"standalone", "parent", "child"}:
        add_risk("INVALID_PARENTAGE_LEVEL", "Parentage level must be standalone, parent, or child")
    if not context["verified"]:
        add_risk("POLICY_CONTEXT_UNVERIFIED", "Policy context does not match a complete bundled marketplace baseline")
    if context["product_type"] in SAFETY_SENSITIVE_PRODUCT_TYPES:
        add_risk("SAFETY_SENSITIVE_PRODUCT_TYPE", SAFETY_SENSITIVE_PRODUCT_TYPES[context["product_type"]])
    if stripped and not deterministic_english:
        add_risk("UNSUPPORTED_TITLE_LANGUAGE", "Non-English titles require manual language and tokenization review")
    if requested_media_exempt and not media_exemption_applied:
        add_risk("MEDIA_EXEMPTION_UNVERIFIED", "Requested media exemption was not applied because Product Type and policy context were not verified")

    if not max_chars_valid:
        warnings.append(f"Invalid max_chars value; defaulted to {default_max_chars}")
        add_risk("INVALID_MAX_CHARS", "Custom title limit is invalid and requires policy confirmation")
    if not highlights_max_valid:
        warnings.append(f"Invalid item_highlights_max_chars value; defaulted to {DEFAULT_ITEM_HIGHLIGHTS_MAX_CHARS}")
        add_risk("INVALID_ITEM_HIGHLIGHTS_MAX_CHARS", "Custom Item Highlights limit is invalid and requires policy confirmation")

    if not stripped:
        errors.append("Title is empty")

    char_count = len(stripped)
    utf8_bytes = len(stripped.encode("utf-8"))
    item_highlights_char_count = len(stripped_highlights)
    item_highlights_utf8_bytes = len(stripped_highlights.encode("utf-8"))

    if not media_exemption_applied and char_count > max_chars:
        errors.append(f"Title has {char_count} characters; maximum is {max_chars}")
        add_risk("TITLE_LENGTH_EXCEEDED", errors[-1])
    if stripped_highlights and item_highlights_char_count > highlights_max_chars:
        errors.append(f"Item Highlights has {item_highlights_char_count} characters; maximum is {highlights_max_chars}")
        add_risk("ITEM_HIGHLIGHTS_LENGTH_EXCEEDED", errors[-1])

    if title != stripped:
        warnings.append("Title has leading or trailing whitespace")
    if re.search(r"\s{2,}", stripped):
        warnings.append("Title contains repeated whitespace")
    if re.search(r"([,./&+\-])\1+", stripped):
        warnings.append("Title contains repeated punctuation")

    restricted = sorted(set(stripped) & RESTRICTED_CHARACTERS)
    if restricted:
        without_brand = re.sub(re.escape(brand), "", stripped, flags=re.I) if brand else stripped
        not_brand = set(without_brand) & set(restricted)
        brand_restricted = (set(brand) & set(restricted)) if brand.casefold() in stripped.casefold() else set()
        if not_brand:
            errors.append("Restricted characters: " + " ".join(sorted(not_brand)))
            add_risk("RESTRICTED_CHARACTERS", errors[-1])
        if brand_restricted:
            warnings.append("Restricted character appears in brand; verify the brand-name exception: " + " ".join(sorted(brand_restricted)))

    duplicates: list[str] = []
    if deterministic_english:
        duplicates = duplicate_words(stripped, analysis_locale)
        if duplicates:
            errors.append("Words appear more than twice: " + ", ".join(duplicates))
            add_risk("DUPLICATE_WORDS", errors[-1])

    missing_required = [phrase for phrase in required_phrases if phrase.casefold() not in stripped.casefold()]
    if missing_required:
        errors.append("Missing required phrases: " + " | ".join(missing_required))
        add_risk("MISSING_REQUIRED_ATTRIBUTE", errors[-1])

    if deterministic_english:
        for label, pattern in PROMOTIONAL_PATTERNS.items():
            if pattern.search(stripped):
                errors.append(f"Promotional content detected: {label}")
                add_risk("PROMOTIONAL_CONTENT", errors[-1])
            if pattern.search(stripped_highlights):
                warnings.append(f"Review promotional content in Item Highlights: {label}")

        for label, pattern in SUBJECTIVE_PATTERNS.items():
            if pattern.search(stripped):
                warnings.append(f"Review subjective content: {label}")

    evidence_claims: list[str] = []
    if deterministic_english:
        for claim_id, (label, pattern, _aliases) in CLAIM_DEFINITIONS.items():
            if pattern.search(stripped) or pattern.search(stripped_highlights):
                evidence_claims.append(label)
                if claim_id not in verified_claim_ids:
                    warnings.append(f"Evidence-sensitive claim is not marked verified: {label}")
                    add_risk("UNVERIFIED_CLAIM", f"Evidence-sensitive claim requires verification: {label}")

    referenced_brands = split_terms(row.get("referenced_brands"))
    if deterministic_english:
        for field_name, field_value in (("Title", stripped), ("Item Highlights", stripped_highlights)):
            if referenced_brands and any(name.casefold() in field_value.casefold() for name in referenced_brands):
                if not RELATIONSHIP_BRANDS.search(field_value):
                    warnings.append(f"Referenced third-party brand in {field_name} lacks explicit compatibility or replacement wording")
                    add_risk("AMBIGUOUS_COMPATIBILITY", warnings[-1])

    cased_letters = [char for char in stripped if char.lower() != char.upper()]
    if len(cased_letters) >= 5 and all(char.isupper() for char in cased_letters):
        warnings.append("Title appears to use all caps")

    if errors:
        add_risk("HARD_VALIDATION_ERROR", "One or more deterministic validation errors must be resolved")

    status = "FAIL" if errors else ("PASS_WITH_WARNINGS" if warnings else "PASS")
    if errors or risk_codes:
        review_status = "MANUAL_REVIEW"
    elif warnings:
        review_status = "READY_WITH_WARNINGS"
    else:
        review_status = "READY"

    return {
        **row,
        "schema_version": SCHEMA_VERSION,
        "title": title,
        "item_highlights": item_highlights,
        "char_count": char_count,
        "utf8_bytes": utf8_bytes,
        "item_highlights_char_count": item_highlights_char_count,
        "item_highlights_utf8_bytes": item_highlights_utf8_bytes,
        "max_chars": "EXEMPT" if media_exemption_applied else max_chars,
        "item_highlights_max_chars": highlights_max_chars,
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "review_status": review_status,
        "review_reasons": review_reasons,
        "risk_codes": risk_codes,
        "policy_context": {
            **context,
            "media_exempt_requested": requested_media_exempt,
            "media_exemption_applied": media_exemption_applied,
            "deterministic_language_support": deterministic_english,
        },
        "duplicate_words": duplicates,
        "missing_required": missing_required,
        "evidence_claims": evidence_claims,
        "verified_claim_ids": sorted(verified_claim_ids),
    }


def read_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = data.get("items", [data])
        if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
            raise ValueError("JSON input must be an object, a list of objects, or an object with an 'items' list")
        return data
    raise ValueError("Input must be .csv or .json")


def serialize_cell(value: Any) -> Any:
    if isinstance(value, list):
        return " | ".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, bool):
        return "true" if value else "false"
    return value


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".json":
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return
    if path.suffix.lower() == ".csv":
        fieldnames: list[str] = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows({key: serialize_cell(value) for key, value in row.items()} for row in rows)
        return
    raise ValueError("Output must be .csv or .json")


def same_path(left: Path, right: Path) -> bool:
    return os.path.normcase(str(left.resolve())) == os.path.normcase(str(right.resolve()))


def apply_cli_context(row: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    merged = dict(row)
    for field in ("marketplace", "locale", "product_type", "parentage_level"):
        value = getattr(args, field, None)
        if value and not merged.get(field):
            merged[field] = value
    if args.media_exempt and not merged.get("media_exempt"):
        merged["media_exempt"] = True
    return merged


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--title", help="Validate one title")
    source.add_argument("--input", type=Path, help="Validate a CSV or JSON file")
    parser.add_argument("--output", type=Path, help="Write batch results to CSV or JSON")
    parser.add_argument("--brand", default="")
    parser.add_argument("--item-highlights", default="")
    parser.add_argument("--marketplace")
    parser.add_argument("--locale")
    parser.add_argument("--product-type")
    parser.add_argument("--parentage-level", choices=("standalone", "parent", "child"))
    parser.add_argument("--required", action="append", default=[], help="Required phrase; repeat as needed")
    parser.add_argument("--verified-claim", action="append", default=[], help="Exact verified claim ID or alias; repeat as needed")
    parser.add_argument("--referenced-brand", action="append", default=[], help="Third-party brand referenced for compatibility")
    parser.add_argument("--media-exempt", action="store_true", help="Request a media exemption; Product Type and policy context still control it")
    parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
    parser.add_argument("--allow-overwrite", action="store_true", help="Allow output to replace the input file")
    parser.add_argument("--fail-on-error", action="store_true", help="Exit 1 when any title fails deterministic checks")
    parser.add_argument("--fail-on-manual-review", action="store_true", help="Exit 1 when any title requires manual review")
    return parser


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = build_parser()
    args = parser.parse_args()
    if args.input and args.output and same_path(args.input, args.output) and not args.allow_overwrite:
        parser.error("input and output paths are the same; use --allow-overwrite to replace the source")

    if args.title is not None:
        row = {
            "title": args.title,
            "brand": args.brand,
            "item_highlights": args.item_highlights,
            "marketplace": args.marketplace,
            "locale": args.locale,
            "product_type": args.product_type,
            "parentage_level": args.parentage_level,
            "required_phrases": args.required,
            "verified_claims": args.verified_claim,
            "referenced_brands": args.referenced_brand,
            "media_exempt": args.media_exempt,
        }
        results = [analyze_title(row, args.max_chars)]
    else:
        rows = [apply_cli_context(row, args) for row in read_rows(args.input)]
        results = [analyze_title(row, args.max_chars) for row in rows]

    if args.output:
        write_rows(args.output, results)
    else:
        print(json.dumps(results[0] if args.title is not None else results, ensure_ascii=False, indent=2))

    failed = any(result["status"] == "FAIL" for result in results)
    manual_review = any(result["review_status"] == "MANUAL_REVIEW" for result in results)
    if args.fail_on_manual_review and manual_review:
        return 1
    return 1 if args.fail_on_error and failed else 0


if __name__ == "__main__":
    sys.exit(main())
