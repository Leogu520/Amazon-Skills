#!/usr/bin/env python3

import tempfile
import unittest
from pathlib import Path

from validate_titles import analyze_title, read_rows, write_rows


class AnalyzeTitleTests(unittest.TestCase):
    def test_valid_title_and_exact_count(self):
        result = analyze_title({
            "title": "NovaTrail Stainless Steel Water Bottle, 32 oz, Leakproof, BPA-Free",
            "brand": "NovaTrail",
            "locale": "en_US",
            "required_phrases": ["Water Bottle", "32 oz"],
            "verified_claims": ["BPA-free"],
        })
        self.assertEqual(result["char_count"], 66)
        self.assertEqual(result["status"], "PASS")

    def test_over_limit_fails(self):
        result = analyze_title({"title": "X" * 76})
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("maximum is 75", result["errors"][0])

    def test_media_exemption_skips_length_failure(self):
        result = analyze_title({"title": "X" * 120, "media_exempt": True})
        self.assertNotEqual(result["status"], "FAIL")
        self.assertEqual(result["max_chars"], "EXEMPT")

    def test_missing_required_phrase_fails(self):
        result = analyze_title({"title": "Brand Water Bottle", "required_phrases": "32 oz|2-Pack"})
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["missing_required"], ["32 oz", "2-Pack"])

    def test_duplicate_word_fails(self):
        result = analyze_title({"title": "Brand Water Bottle Water Cup Water Flask"})
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("water", result["duplicate_words"])

    def test_stopword_repetition_is_exempt(self):
        result = analyze_title({"title": "Case for Phone for Travel for Work", "locale": "en_US"})
        self.assertNotEqual(result["status"], "FAIL")

    def test_restricted_character_fails(self):
        result = analyze_title({"title": "Brand Bottle! 32 oz"})
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("Restricted characters", " ".join(result["errors"]))

    def test_brand_character_exception_is_warning(self):
        result = analyze_title({"title": "A_Brand Water Bottle", "brand": "A_Brand"})
        self.assertEqual(result["status"], "PASS_WITH_WARNINGS")
        self.assertIn("brand-name exception", " ".join(result["warnings"]))

    def test_brand_exception_does_not_hide_other_restricted_character(self):
        result = analyze_title({"title": "A_Brand Water_Bottle", "brand": "A_Brand"})
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("Restricted characters", " ".join(result["errors"]))

    def test_unverified_claim_warns(self):
        result = analyze_title({"title": "Brand Water Bottle, BPA-Free"})
        self.assertEqual(result["status"], "PASS_WITH_WARNINGS")
        self.assertIn("BPA-free", " ".join(result["warnings"]))

    def test_item_highlights_count_and_claim_review(self):
        result = analyze_title({
            "title": "Brand Water Bottle, 32 oz",
            "item_highlights": "BPA-free bottle for gym and office use.",
        })
        self.assertEqual(result["item_highlights_char_count"], 39)
        self.assertEqual(result["status"], "PASS_WITH_WARNINGS")
        self.assertIn("BPA-free", result["evidence_claims"])

    def test_item_highlights_over_limit_fails(self):
        result = analyze_title({"title": "Brand Water Bottle", "item_highlights": "X" * 126})
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("Item Highlights has 126", " ".join(result["errors"]))

    def test_missing_relationship_word_warns(self):
        result = analyze_title({"title": "Brand Battery for Dyson V11", "referenced_brands": ["Dyson"]})
        self.assertEqual(result["status"], "PASS_WITH_WARNINGS")
        self.assertIn("third-party brand", " ".join(result["warnings"]))

    def test_explicit_relationship_word_passes(self):
        result = analyze_title({"title": "Brand Battery Compatible with Dyson V11", "referenced_brands": ["Dyson"]})
        self.assertEqual(result["status"], "PASS")

    def test_promotional_language_fails(self):
        result = analyze_title({"title": "Brand Water Bottle, Limited Time Deal"})
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("Promotional content", " ".join(result["errors"]))

    def test_subjective_language_warns(self):
        result = analyze_title({"title": "Brand Premium Quality Water Bottle"})
        self.assertEqual(result["status"], "PASS_WITH_WARNINGS")

    def test_reprocessing_media_audit_output_uses_default_without_crashing(self):
        result = analyze_title({"title": "X" * 120, "media_exempt": True, "max_chars": "EXEMPT"})
        self.assertNotEqual(result["status"], "FAIL")

    def test_utf8_byte_count_is_reported(self):
        result = analyze_title({"title": "品牌 水杯"})
        self.assertEqual(result["char_count"], 5)
        self.assertGreater(result["utf8_bytes"], result["char_count"])

    def test_representative_category_candidates(self):
        cases = [
            {
                "profile": "home",
                "title": "NovaTrail Stainless Steel Water Bottle, 32 oz, Leakproof, BPA-Free",
                "verified_claims": ["BPA-free"],
                "expected": "PASS",
            },
            {
                "profile": "electronics",
                "title": "VoltEdge USB-C Charger, 65W GaN, 3-Port, for Laptop and Phone",
                "expected": "PASS",
            },
            {
                "profile": "automotive",
                "title": "RoadForge Front Wheel Bearing Hub, Compatible with Audi A1 2010-2019",
                "referenced_brands": ["Audi"],
                "expected": "PASS",
            },
            {
                "profile": "industrial",
                "title": "BoltCore M8 x 1.25 Stainless Steel Hex Bolts, 20-Pack",
                "expected": "PASS",
            },
            {
                "profile": "beauty",
                "title": "GlowKind Face Moisturizer, Hyaluronic Acid, 1.7 fl oz",
                "expected": "PASS",
            },
            {
                "profile": "baby",
                "title": "MellowNest Baby Carrier, Newborn to Toddler, Black",
                "expected": "PASS_WITH_WARNINGS",
            },
            {
                "profile": "apparel",
                "title": "NorthPeak Men's Running Jacket, Waterproof, Size M, Black",
                "expected": "PASS_WITH_WARNINGS",
            },
            {
                "profile": "toys",
                "title": "PlayArc Building Blocks, Ages 6+, 500 Pieces",
                "expected": "PASS_WITH_WARNINGS",
            },
        ]
        for case in cases:
            with self.subTest(profile=case["profile"]):
                result = analyze_title(case)
                self.assertLessEqual(result["char_count"], 75)
                self.assertEqual(result["status"], case["expected"])


class BatchIoTests(unittest.TestCase):
    def test_csv_round_trip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "audit.csv"
            rows = [analyze_title({"sku": "SKU-1", "title": "Brand Water Bottle, 32 oz"})]
            write_rows(output, rows)
            restored = read_rows(output)
            self.assertEqual(restored[0]["sku"], "SKU-1")
            self.assertEqual(restored[0]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
