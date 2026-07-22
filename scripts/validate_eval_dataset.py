#!/usr/bin/env python3
"""Validate the rewrite-quality forward-test dataset."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "evals" / "rewrite_quality.json"
REQUIRED_DIMENSIONS = {
    "character_compliance",
    "anti_misbuy_attribute_retention",
    "keyword_tradeoffs",
    "claim_evidence",
    "field_migration",
}
REQUIRED_CATEGORIES = {
    "consumer_goods",
    "automotive",
    "industrial",
    "electronics",
    "beauty",
    "baby",
    "apparel_parent",
    "apparel_child",
    "toys",
    "bundles",
}
REQUIRED_CASE_FIELDS = {
    "id",
    "category",
    "marketplace",
    "locale",
    "product_type",
    "parentage_level",
    "current_title",
    "facts",
    "keyword_priority",
    "required_in_title",
    "verified_claims",
    "referenced_brands",
    "forbidden_in_title",
    "expected_moved_terms",
    "reference_title",
    "reference_item_highlights",
    "expected_review_status",
}


def main() -> int:
    data = json.loads(DATASET.read_text(encoding="utf-8"))
    problems: list[str] = []
    cases = data.get("cases", [])
    if data.get("schema_version") != "1.1":
        problems.append("Dataset schema_version must be 1.1")
    if set(data.get("rubric", {})) != REQUIRED_DIMENSIONS:
        problems.append("Rubric must contain the five v1.1 scoring dimensions")
    if len(cases) < 10:
        problems.append("Dataset must contain at least 10 cases")
    if {case.get("category") for case in cases} != REQUIRED_CATEGORIES:
        problems.append("Dataset category coverage is incomplete")

    ids: set[str] = set()
    for case in cases:
        case_id = case.get("id", "<missing>")
        missing = REQUIRED_CASE_FIELDS - set(case)
        if missing:
            problems.append(f"{case_id}: missing fields {sorted(missing)}")
        if case_id in ids:
            problems.append(f"Duplicate case ID: {case_id}")
        ids.add(case_id)
        title = case.get("reference_title", "")
        highlights = case.get("reference_item_highlights", "")
        if len(title) > 75:
            problems.append(f"{case_id}: reference title exceeds 75 characters")
        if len(highlights) > 125:
            problems.append(f"{case_id}: reference Item Highlights exceeds 125 characters")
        for phrase in case.get("required_in_title", []):
            if phrase.casefold() not in title.casefold():
                problems.append(f"{case_id}: reference title is missing required phrase {phrase!r}")
        for phrase in case.get("forbidden_in_title", []):
            if phrase.casefold() in title.casefold():
                problems.append(f"{case_id}: reference title retains forbidden phrase {phrase!r}")
        if case.get("expected_review_status") not in {"READY", "READY_WITH_WARNINGS", "MANUAL_REVIEW"}:
            problems.append(f"{case_id}: invalid expected_review_status")

    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1
    print(f"Rewrite-quality dataset passed: {len(cases)} cases, {len(REQUIRED_DIMENSIONS)} scoring dimensions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
