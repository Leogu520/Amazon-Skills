#!/usr/bin/env python3
"""Export forward-test inputs without held-out grading fields."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "evals" / "rewrite_quality.json"
VISIBLE_FIELDS = (
    "id",
    "category",
    "marketplace",
    "locale",
    "product_type",
    "parentage_level",
    "current_title",
    "facts",
    "keyword_priority",
    "verified_claims",
    "referenced_brands",
)


def blind_projection(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": data["schema_version"],
        "cases": [{field: case[field] for field in VISIBLE_FIELDS} for case in data["cases"]],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(blind_projection(data), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
