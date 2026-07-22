#!/usr/bin/env python3

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_validator():
    path = ROOT / "optimize-amazon-titles" / "scripts" / "validate_titles.py"
    spec = importlib.util.spec_from_file_location("eval_title_validator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_blind_exporter():
    path = ROOT / "scripts" / "export_blind_eval.py"
    spec = importlib.util.spec_from_file_location("blind_eval_exporter", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class RewriteQualityDatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = load_validator()
        cls.data = json.loads((ROOT / "evals" / "rewrite_quality.json").read_text(encoding="utf-8"))

    def test_dataset_has_ten_unique_cases(self):
        cases = self.data["cases"]
        self.assertEqual(len(cases), 10)
        self.assertEqual(len({case["id"] for case in cases}), 10)

    def test_rubric_has_five_dimensions(self):
        self.assertEqual(len(self.data["rubric"]), 5)

    def test_blind_projection_excludes_all_grading_fields(self):
        projection = load_blind_exporter().blind_projection(self.data)
        forbidden = {
            "required_in_title",
            "forbidden_in_title",
            "expected_moved_terms",
            "reference_title",
            "reference_item_highlights",
            "expected_review_status",
        }
        self.assertEqual(len(projection["cases"]), 10)
        for case in projection["cases"]:
            self.assertFalse(forbidden & set(case), case["id"])

    def test_reference_titles_pass_expected_deterministic_checks(self):
        for case in self.data["cases"]:
            row = {
                "title": case["reference_title"],
                "item_highlights": case["reference_item_highlights"],
                "marketplace": case["marketplace"],
                "locale": case["locale"],
                "product_type": case["product_type"],
                "parentage_level": case["parentage_level"],
                "required_phrases": case["required_in_title"],
                "verified_claims": case["verified_claims"],
                "referenced_brands": case["referenced_brands"],
            }
            result = self.validator.analyze_title(row)
            self.assertNotEqual(result["status"], "FAIL", case["id"])
            self.assertEqual(result["review_status"], case["expected_review_status"], case["id"])


if __name__ == "__main__":
    unittest.main()
