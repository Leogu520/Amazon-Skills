#!/usr/bin/env python3
"""Validate Amazon title candidates without external dependencies."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable


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

EVIDENCE_PATTERNS = {
    "BPA-free": re.compile(r"\bBPA[ -]?free\b", re.I),
    "non-toxic": re.compile(r"\bnon[ -]?toxic\b", re.I),
    "food-safe": re.compile(r"\bfood[ -]?safe\b", re.I),
    "child-safe": re.compile(r"\bchild[ -]?safe\b", re.I),
    "waterproof claim": re.compile(r"\bwaterproof\b|\bIP\d{2}\b", re.I),
    "organic claim": re.compile(r"\borganic\b", re.I),
    "hypoallergenic claim": re.compile(r"\bhypoallergenic\b", re.I),
    "clinical claim": re.compile(r"\bclinically\s+(?:proven|tested)\b", re.I),
    "medical or approval claim": re.compile(r"\b(?:medical[ -]?grade|FDA[ -]?approved)\b", re.I),
    "environmental claim": re.compile(r"\b(?:eco[ -]?friendly|sustainable|recyclable)\b", re.I),
    "antimicrobial claim": re.compile(r"\bantimicrobial\b", re.I),
    "fire performance claim": re.compile(r"\b(?:fireproof|flame[ -]?resistant)\b", re.I),
    "age or life-stage claim": re.compile(
        r"\b(?:newborn|infant|toddler|ages?\s*\d+\+?|\d+\s*(?:months?|mos?|years?|yrs?)\s*(?:and\s+up|\+|old)?)\b",
        re.I,
    ),
    "certification or compliance claim": re.compile(r"\b(?:certified|compliant|tested|approved)\b", re.I),
    "performance duration claim": re.compile(
        r"\b(?:keeps?|lasts?|runtime|battery\s+life)[^,;]{0,30}\d+(?:\.\d+)?\s*(?:hours?|hrs?|minutes?|mins?|days?)\b",
        re.I,
    ),
}

RELATIONSHIP_BRANDS = re.compile(r"\b(?:compatible\s+with|fits?|replacement\s+for|designed\s+for)\b", re.I)
WORD_RE = re.compile(r"[^\W_]+(?:[-'][^\W_]+)*", re.UNICODE)


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


def locale_language(locale: str) -> str:
    language = (locale or "en").split("_")[0].split("-")[0].lower()
    return language if language in STOPWORDS else "en"


def parse_max_chars(value: Any, default: int) -> int:
    text = str(value or "").strip()
    if not text or not text.isdigit():
        return default
    return int(text)


def duplicate_words(title: str, locale: str) -> list[str]:
    stopwords = STOPWORDS[locale_language(locale)]
    counts: dict[str, int] = {}
    for token in WORD_RE.findall(title.casefold()):
        if token in stopwords:
            continue
        counts[token] = counts.get(token, 0) + 1
    return sorted(word for word, count in counts.items() if count > 2)


def contains_verified_claim(label: str, verified_claims: Iterable[str]) -> bool:
    label_key = label.casefold()
    return any(label_key in claim.casefold() or claim.casefold() in label_key for claim in verified_claims)


def analyze_title(row: dict[str, Any], default_max_chars: int = DEFAULT_MAX_CHARS) -> dict[str, Any]:
    title = str(row.get("title") or "")
    stripped = title.strip()
    item_highlights = str(row.get("item_highlights") or "")
    stripped_highlights = item_highlights.strip()
    brand = str(row.get("brand") or "").strip()
    locale = str(row.get("locale") or row.get("marketplace_locale") or "en_US")
    media_exempt = truthy(row.get("media_exempt"))
    max_chars = parse_max_chars(row.get("max_chars"), default_max_chars)
    highlights_max_chars = parse_max_chars(row.get("item_highlights_max_chars"), DEFAULT_ITEM_HIGHLIGHTS_MAX_CHARS)
    required_phrases = split_terms(row.get("required_phrases"))
    verified_claims = split_terms(row.get("verified_claims"))

    errors: list[str] = []
    warnings: list[str] = []

    if not stripped:
        errors.append("Title is empty")

    char_count = len(stripped)
    utf8_bytes = len(stripped.encode("utf-8"))
    item_highlights_char_count = len(stripped_highlights)
    item_highlights_utf8_bytes = len(stripped_highlights.encode("utf-8"))

    if not media_exempt and char_count > max_chars:
        errors.append(f"Title has {char_count} characters; maximum is {max_chars}")
    if stripped_highlights and item_highlights_char_count > highlights_max_chars:
        errors.append(
            f"Item Highlights has {item_highlights_char_count} characters; maximum is {highlights_max_chars}"
        )

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
        if brand_restricted:
            warnings.append("Restricted character appears in brand; verify the brand-name exception: " + " ".join(sorted(brand_restricted)))

    duplicates = duplicate_words(stripped, locale)
    if duplicates:
        errors.append("Words appear more than twice: " + ", ".join(duplicates))

    missing_required = [phrase for phrase in required_phrases if phrase.casefold() not in stripped.casefold()]
    if missing_required:
        errors.append("Missing required phrases: " + " | ".join(missing_required))

    for label, pattern in PROMOTIONAL_PATTERNS.items():
        if pattern.search(stripped):
            errors.append(f"Promotional content detected: {label}")
        if pattern.search(stripped_highlights):
            warnings.append(f"Review promotional content in Item Highlights: {label}")

    for label, pattern in SUBJECTIVE_PATTERNS.items():
        if pattern.search(stripped):
            warnings.append(f"Review subjective content: {label}")

    evidence_claims: list[str] = []
    for label, pattern in EVIDENCE_PATTERNS.items():
        if pattern.search(stripped) or pattern.search(stripped_highlights):
            evidence_claims.append(label)
            if not contains_verified_claim(label, verified_claims):
                warnings.append(f"Evidence-sensitive claim is not marked verified: {label}")

    referenced_brands = split_terms(row.get("referenced_brands"))
    for field_name, field_value in (("Title", stripped), ("Item Highlights", stripped_highlights)):
        if referenced_brands and any(brand_name.casefold() in field_value.casefold() for brand_name in referenced_brands):
            if not RELATIONSHIP_BRANDS.search(field_value):
                warnings.append(
                    f"Referenced third-party brand in {field_name} lacks explicit compatibility or replacement wording"
                )

    letters = [char for char in stripped if char.isalpha()]
    if len(letters) >= 5 and stripped == stripped.upper():
        warnings.append("Title appears to use all caps")

    status = "FAIL" if errors else ("PASS_WITH_WARNINGS" if warnings else "PASS")
    return {
        **row,
        "title": title,
        "item_highlights": item_highlights,
        "char_count": char_count,
        "utf8_bytes": utf8_bytes,
        "item_highlights_char_count": item_highlights_char_count,
        "item_highlights_utf8_bytes": item_highlights_utf8_bytes,
        "max_chars": "EXEMPT" if media_exempt else max_chars,
        "item_highlights_max_chars": highlights_max_chars,
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "duplicate_words": duplicates,
        "missing_required": missing_required,
        "evidence_claims": evidence_claims,
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--title", help="Validate one title")
    source.add_argument("--input", type=Path, help="Validate a CSV or JSON file")
    parser.add_argument("--output", type=Path, help="Write batch results to CSV or JSON")
    parser.add_argument("--brand", default="")
    parser.add_argument("--item-highlights", default="")
    parser.add_argument("--locale", default="en_US")
    parser.add_argument("--required", action="append", default=[], help="Required phrase; repeat as needed")
    parser.add_argument("--verified-claim", action="append", default=[], help="Verified claim label; repeat as needed")
    parser.add_argument("--referenced-brand", action="append", default=[], help="Third-party brand referenced for compatibility")
    parser.add_argument("--media-exempt", action="store_true")
    parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
    parser.add_argument("--fail-on-error", action="store_true", help="Exit 1 when any title fails")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.title is not None:
        row = {
            "title": args.title,
            "brand": args.brand,
            "item_highlights": args.item_highlights,
            "locale": args.locale,
            "required_phrases": args.required,
            "verified_claims": args.verified_claim,
            "referenced_brands": args.referenced_brand,
            "media_exempt": args.media_exempt,
        }
        results = [analyze_title(row, args.max_chars)]
    else:
        results = [analyze_title(row, args.max_chars) for row in read_rows(args.input)]

    if args.output:
        write_rows(args.output, results)
    else:
        print(json.dumps(results[0] if args.title is not None else results, ensure_ascii=False, indent=2))

    failed = any(result["status"] == "FAIL" for result in results)
    return 1 if args.fail_on_error and failed else 0


if __name__ == "__main__":
    sys.exit(main())
