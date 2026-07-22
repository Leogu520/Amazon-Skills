#!/usr/bin/env python3
"""Synchronize or verify the duplicated self-contained package runtime."""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENGLISH = ROOT / "optimize-amazon-titles"
CHINESE = ROOT / "optimize-amazon-titles-zh"
RUNTIME_FILES = (Path("scripts/validate_titles.py"),)
REQUIRED_PACKAGE_FILES = (
    Path("SKILL.md"),
    Path("agents/openai.yaml"),
    Path("references/policy-core.md"),
    Path("references/category-profiles.md"),
    Path("references/keyword-priority.md"),
    Path("references/risk-and-claims.md"),
    Path("scripts/validate_titles.py"),
)
POLICY_MARKERS = (
    "2026-07-21",
    "145b6d0f-999c-4555-896c-c694bda2e470",
    "ae5ffd79-c7f5-4f3e-8739-fb87bb77b6f4",
)


def check_structure() -> list[str]:
    problems: list[str] = []
    for package in (ENGLISH, CHINESE):
        for relative in REQUIRED_PACKAGE_FILES:
            if not (package / relative).is_file():
                problems.append(f"Missing package file: {(package / relative).relative_to(ROOT)}")
        policy_text = (package / "references/policy-core.md").read_text(encoding="utf-8")
        for marker in POLICY_MARKERS:
            if marker not in policy_text:
                problems.append(f"Missing policy marker {marker}: {package.name}/references/policy-core.md")

    english_skill = (ENGLISH / "SKILL.md").read_text(encoding="utf-8")
    chinese_skill = (CHINESE / "SKILL.md").read_text(encoding="utf-8")
    if "name: optimize-amazon-titles\n" not in english_skill:
        problems.append("English package skill name is incorrect")
    if "name: optimize-amazon-titles-zh\n" not in chinese_skill:
        problems.append("Chinese package skill name is incorrect")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Only check parity; do not copy files")
    args = parser.parse_args()

    if not args.check:
        for relative in RUNTIME_FILES:
            target = CHINESE / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ENGLISH / relative, target)

    problems = check_structure()
    for relative in RUNTIME_FILES:
        if not filecmp.cmp(ENGLISH / relative, CHINESE / relative, shallow=False):
            problems.append(f"Runtime drift: {relative.as_posix()}")

    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1
    print("Package runtime parity and structure checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
