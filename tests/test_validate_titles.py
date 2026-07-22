#!/usr/bin/env python3

import csv
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "optimize-amazon-titles" / "scripts" / "validate_titles.py"


def load_validator(path: Path = VALIDATOR_PATH):
    spec = importlib.util.spec_from_file_location("amazon_title_validator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


validator = load_validator()


def complete_row(**overrides):
    row = {
        "title": "Brand Water Bottle, 32 oz",
        "marketplace": "US",
        "locale": "en_US",
        "product_type": "DRINKING_CUP",
        "parentage_level": "standalone",
    }
    row.update(overrides)
    return row


class AnalyzeTitleTests(unittest.TestCase):
    def test_01_valid_title_is_ready_and_preserves_legacy_status(self):
        result = validator.analyze_title(complete_row(
            title="NovaTrail Stainless Steel Water Bottle, 32 oz, Leakproof, BPA-Free",
            brand="NovaTrail",
            required_phrases=["Water Bottle", "32 oz"],
            verified_claims=["bpa_free"],
        ))
        self.assertEqual(result["char_count"], 66)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["review_status"], "READY")

    def test_02_output_contains_v11_contract(self):
        result = validator.analyze_title(complete_row())
        self.assertEqual(result["schema_version"], "1.1")
        for key in ("status", "errors", "warnings", "review_status", "review_reasons", "risk_codes", "policy_context"):
            self.assertIn(key, result)

    def test_03_over_limit_is_fail_and_manual_review(self):
        result = validator.analyze_title(complete_row(title="X" * 76))
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["review_status"], "MANUAL_REVIEW")
        self.assertIn("TITLE_LENGTH_EXCEEDED", result["risk_codes"])

    def test_04_item_highlights_over_limit_is_manual_review(self):
        result = validator.analyze_title(complete_row(item_highlights="X" * 126))
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("ITEM_HIGHLIGHTS_LENGTH_EXCEEDED", result["risk_codes"])

    def test_05_missing_required_phrase_is_manual_review(self):
        result = validator.analyze_title(complete_row(required_phrases="32 oz|2-Pack"))
        self.assertEqual(result["missing_required"], ["2-Pack"])
        self.assertIn("MISSING_REQUIRED_ATTRIBUTE", result["risk_codes"])

    def test_06_duplicate_word_is_hard_error(self):
        result = validator.analyze_title(complete_row(title="Brand Water Bottle Water Cup Water Flask"))
        self.assertIn("water", result["duplicate_words"])
        self.assertIn("DUPLICATE_WORDS", result["risk_codes"])

    def test_07_stopword_repetition_is_exempt(self):
        result = validator.analyze_title(complete_row(title="Case for Phone for Travel for Work"))
        self.assertNotIn("DUPLICATE_WORDS", result["risk_codes"])

    def test_08_restricted_character_is_hard_error(self):
        result = validator.analyze_title(complete_row(title="Brand Bottle! 32 oz"))
        self.assertIn("RESTRICTED_CHARACTERS", result["risk_codes"])

    def test_09_brand_character_exception_is_nonblocking_warning(self):
        result = validator.analyze_title(complete_row(title="A_Brand Water Bottle", brand="A_Brand"))
        self.assertEqual(result["status"], "PASS_WITH_WARNINGS")
        self.assertEqual(result["review_status"], "READY_WITH_WARNINGS")

    def test_10_brand_exception_does_not_hide_other_restricted_character(self):
        result = validator.analyze_title(complete_row(title="A_Brand Water_Bottle", brand="A_Brand"))
        self.assertEqual(result["status"], "FAIL")

    def test_11_unverified_claim_requires_manual_review(self):
        result = validator.analyze_title(complete_row(title="Brand Water Bottle, BPA-Free"))
        self.assertEqual(result["status"], "PASS_WITH_WARNINGS")
        self.assertEqual(result["review_status"], "MANUAL_REVIEW")
        self.assertIn("UNVERIFIED_CLAIM", result["risk_codes"])

    def test_12_canonical_claim_id_verifies_claim(self):
        result = validator.analyze_title(complete_row(title="Brand Water Bottle, BPA-Free", verified_claims=["bpa_free"]))
        self.assertEqual(result["review_status"], "READY")

    def test_13_exact_claim_alias_verifies_claim(self):
        result = validator.analyze_title(complete_row(title="Brand Waterproof Watch", verified_claims=["waterproof claim"]))
        self.assertNotIn("UNVERIFIED_CLAIM", result["risk_codes"])

    def test_14_fuzzy_claim_string_cannot_bypass_verification(self):
        result = validator.analyze_title(complete_row(title="Brand Waterproof Watch", verified_claims=["claim"]))
        self.assertIn("UNVERIFIED_CLAIM", result["risk_codes"])

    def test_15_longer_unknown_claim_string_cannot_bypass_verification(self):
        result = validator.analyze_title(complete_row(title="Brand Waterproof Watch", verified_claims=["verified waterproof claim evidence"]))
        self.assertIn("UNVERIFIED_CLAIM", result["risk_codes"])

    def test_16_ambiguous_compatibility_requires_manual_review(self):
        result = validator.analyze_title(complete_row(title="Brand Battery for Dyson V11", referenced_brands=["Dyson"]))
        self.assertIn("AMBIGUOUS_COMPATIBILITY", result["risk_codes"])
        self.assertEqual(result["review_status"], "MANUAL_REVIEW")

    def test_17_explicit_compatibility_wording_is_ready(self):
        result = validator.analyze_title(complete_row(title="Brand Battery Compatible with Dyson V11", referenced_brands=["Dyson"]))
        self.assertEqual(result["review_status"], "READY")

    def test_18_promotional_language_is_hard_error(self):
        result = validator.analyze_title(complete_row(title="Brand Water Bottle, Limited Time Deal"))
        self.assertIn("PROMOTIONAL_CONTENT", result["risk_codes"])

    def test_19_subjective_language_is_nonblocking_warning(self):
        result = validator.analyze_title(complete_row(title="Brand Premium Quality Water Bottle"))
        self.assertEqual(result["review_status"], "READY_WITH_WARNINGS")

    def test_20_cjk_title_is_not_misclassified_as_all_caps(self):
        result = validator.analyze_title(complete_row(title="品牌 水杯 限时优惠", locale="zh_CN"))
        self.assertNotIn("all caps", " ".join(result["warnings"]))

    def test_21_cjk_title_requires_language_review(self):
        result = validator.analyze_title(complete_row(title="品牌 水杯", locale="zh_CN"))
        self.assertIn("UNSUPPORTED_TITLE_LANGUAGE", result["risk_codes"])
        self.assertEqual(result["review_status"], "MANUAL_REVIEW")

    def test_22_cjk_length_still_enforced(self):
        result = validator.analyze_title(complete_row(title="杯" * 76, locale="zh_CN"))
        self.assertIn("TITLE_LENGTH_EXCEEDED", result["risk_codes"])

    def test_23_cyrillic_title_requires_language_review(self):
        result = validator.analyze_title(complete_row(title="Бренд бутылка", locale="en_US"))
        self.assertIn("UNSUPPORTED_TITLE_LANGUAGE", result["risk_codes"])

    def test_24_missing_marketplace_uses_limit_but_requires_review(self):
        row = complete_row()
        del row["marketplace"]
        result = validator.analyze_title(row)
        self.assertEqual(result["max_chars"], 75)
        self.assertIn("MISSING_MARKETPLACE", result["risk_codes"])

    def test_25_missing_locale_requires_review(self):
        row = complete_row()
        del row["locale"]
        result = validator.analyze_title(row)
        self.assertIn("MISSING_LOCALE", result["risk_codes"])

    def test_26_missing_product_type_requires_review(self):
        row = complete_row()
        del row["product_type"]
        result = validator.analyze_title(row)
        self.assertIn("MISSING_PRODUCT_TYPE", result["risk_codes"])

    def test_27_missing_parentage_level_requires_review(self):
        row = complete_row()
        del row["parentage_level"]
        result = validator.analyze_title(row)
        self.assertIn("MISSING_PARENTAGE_LEVEL", result["risk_codes"])

    def test_28_invalid_parentage_level_requires_review(self):
        result = validator.analyze_title(complete_row(parentage_level="variation"))
        self.assertIn("INVALID_PARENTAGE_LEVEL", result["risk_codes"])

    def test_29_unknown_marketplace_requires_policy_review(self):
        result = validator.analyze_title(complete_row(marketplace="CA", locale="en_CA"))
        self.assertIn("POLICY_CONTEXT_UNVERIFIED", result["risk_codes"])

    def test_30_false_media_exemption_does_not_skip_length(self):
        result = validator.analyze_title(complete_row(title="X" * 120, media_exempt=True))
        self.assertEqual(result["max_chars"], 75)
        self.assertIn("MEDIA_EXEMPTION_UNVERIFIED", result["risk_codes"])
        self.assertIn("TITLE_LENGTH_EXCEEDED", result["risk_codes"])

    def test_31_verified_book_product_type_applies_exemption(self):
        result = validator.analyze_title(complete_row(title="X" * 120, product_type="BOOK"))
        self.assertEqual(result["max_chars"], "EXEMPT")
        self.assertTrue(result["policy_context"]["media_exemption_applied"])
        self.assertNotIn("TITLE_LENGTH_EXCEEDED", result["risk_codes"])

    def test_32_media_product_with_mismatched_policy_does_not_skip_length(self):
        result = validator.analyze_title(complete_row(title="X" * 120, marketplace="DE", locale="de_DE", product_type="BOOK"))
        self.assertEqual(result["max_chars"], 75)
        self.assertIn("TITLE_LENGTH_EXCEEDED", result["risk_codes"])

    def test_33_uk_english_context_is_verified(self):
        result = validator.analyze_title(complete_row(marketplace="UK", locale="en_GB"))
        self.assertTrue(result["policy_context"]["verified"])
        self.assertEqual(result["review_status"], "READY")

    def test_34_marketplace_id_alias_is_supported(self):
        result = validator.analyze_title(complete_row(marketplace="ATVPDKIKX0DER"))
        self.assertEqual(result["policy_context"]["marketplace"], "US")
        self.assertTrue(result["policy_context"]["verified"])

    def test_35_locale_hyphen_and_case_are_normalized(self):
        result = validator.analyze_title(complete_row(locale="EN-us"))
        self.assertEqual(result["policy_context"]["locale"], "en_US")
        self.assertTrue(result["policy_context"]["verified"])

    def test_36_invalid_max_chars_defaults_and_requires_review(self):
        result = validator.analyze_title(complete_row(max_chars="invalid"))
        self.assertEqual(result["max_chars"], 75)
        self.assertIn("INVALID_MAX_CHARS", result["risk_codes"])

    def test_37_invalid_item_highlights_limit_defaults_and_requires_review(self):
        result = validator.analyze_title(complete_row(item_highlights_max_chars="zero"))
        self.assertEqual(result["item_highlights_max_chars"], 125)
        self.assertIn("INVALID_ITEM_HIGHLIGHTS_MAX_CHARS", result["risk_codes"])

    def test_38_empty_title_is_fail_and_manual_review(self):
        result = validator.analyze_title(complete_row(title=""))
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["review_status"], "MANUAL_REVIEW")

    def test_39_utf8_byte_count_is_reported(self):
        result = validator.analyze_title(complete_row(title="品牌 水杯", locale="zh_CN"))
        self.assertEqual(result["char_count"], 5)
        self.assertGreater(result["utf8_bytes"], result["char_count"])

    def test_40_leading_whitespace_is_nonblocking_warning(self):
        result = validator.analyze_title(complete_row(title=" Brand Water Bottle"))
        self.assertEqual(result["status"], "PASS_WITH_WARNINGS")
        self.assertEqual(result["review_status"], "READY_WITH_WARNINGS")

    def test_41_all_caps_only_counts_cased_letters(self):
        result = validator.analyze_title(complete_row(title="BRAND 水杯 32 OZ"))
        self.assertIn("all caps", " ".join(result["warnings"]))

    def test_42_reprocessing_exempt_output_keeps_safe_fallback(self):
        result = validator.analyze_title(complete_row(title="X" * 120, product_type="ABIS_BOOK", max_chars="EXEMPT"))
        self.assertEqual(result["max_chars"], "EXEMPT")
        self.assertNotIn("INVALID_MAX_CHARS", result["risk_codes"])

    def test_43_charging_adapter_requires_safety_review(self):
        result = validator.analyze_title(complete_row(title="Brand USB-C Charger, 65W", product_type="CHARGING_ADAPTER"))
        self.assertIn("SAFETY_SENSITIVE_PRODUCT_TYPE", result["risk_codes"])
        self.assertEqual(result["review_status"], "MANUAL_REVIEW")

    def test_44_baby_carrier_requires_safety_review(self):
        result = validator.analyze_title(complete_row(title="Brand Baby Carrier, 7-45 lb", product_type="BABY_CARRIER"))
        self.assertIn("SAFETY_SENSITIVE_PRODUCT_TYPE", result["risk_codes"])

    def test_45_unverified_stem_positioning_requires_review(self):
        result = validator.analyze_title(complete_row(title="Brand STEM Building Tiles, 64-Piece", product_type="TOYS_AND_GAMES"))
        self.assertIn("UNVERIFIED_CLAIM", result["risk_codes"])

    def test_46_exact_educational_claim_id_is_accepted(self):
        result = validator.analyze_title(complete_row(
            title="Brand STEM Building Tiles, 64-Piece",
            product_type="TOYS_AND_GAMES",
            verified_claims=["educational_positioning"],
        ))
        self.assertNotIn("UNVERIFIED_CLAIM", result["risk_codes"])

    def test_47_fda_approval_does_not_require_two_claim_ids(self):
        result = validator.analyze_title(complete_row(
            title="Brand FDA-Approved Device",
            verified_claims=["medical_approval"],
        ))
        self.assertNotIn("UNVERIFIED_CLAIM", result["risk_codes"])
        self.assertEqual(result["evidence_claims"], ["medical or approval claim"])

    def test_48_clinically_tested_does_not_require_two_claim_ids(self):
        result = validator.analyze_title(complete_row(
            title="Brand Clinically Tested Face Cream",
            verified_claims=["clinical"],
        ))
        self.assertNotIn("UNVERIFIED_CLAIM", result["risk_codes"])
        self.assertEqual(result["evidence_claims"], ["clinical claim"])


class BatchIoTests(unittest.TestCase):
    def test_49_json_round_trip_preserves_policy_object(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result.json"
            validator.write_rows(output, [validator.analyze_title(complete_row())])
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertIsInstance(data[0]["policy_context"], dict)

    def test_50_csv_serializes_policy_object_as_json(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result.csv"
            validator.write_rows(output, [validator.analyze_title(complete_row())])
            with output.open("r", encoding="utf-8-sig", newline="") as handle:
                row = next(csv.DictReader(handle))
            self.assertTrue(json.loads(row["policy_context"])["verified"])

    def test_51_read_json_object_as_single_row(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_text(json.dumps(complete_row()), encoding="utf-8")
            self.assertEqual(len(validator.read_rows(path)), 1)

    def test_52_read_json_items_wrapper(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_text(json.dumps({"items": [complete_row(), complete_row()]}), encoding="utf-8")
            self.assertEqual(len(validator.read_rows(path)), 2)

    def test_53_invalid_input_extension_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                validator.read_rows(Path(directory) / "input.txt")

    def test_54_invalid_output_extension_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                validator.write_rows(Path(directory) / "output.txt", [complete_row()])


class CliTests(unittest.TestCase):
    def run_cli(self, *arguments):
        return subprocess.run(
            [sys.executable, str(VALIDATOR_PATH), *map(str, arguments)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

    def test_55_same_input_output_is_rejected_by_default(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "titles.json"
            path.write_text(json.dumps([complete_row()]), encoding="utf-8")
            result = self.run_cli("--input", path, "--output", path)
            self.assertEqual(result.returncode, 2)
            self.assertIn("--allow-overwrite", result.stderr)

    def test_56_allow_overwrite_replaces_batch_source(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "titles.json"
            path.write_text(json.dumps([complete_row()]), encoding="utf-8")
            result = self.run_cli("--input", path, "--output", path, "--allow-overwrite")
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))[0]["schema_version"], "1.1")

    def test_57_fail_on_manual_review_exits_one(self):
        result = self.run_cli("--title", "Brand Water Bottle")
        self.assertEqual(result.returncode, 0)
        result = self.run_cli("--title", "Brand Water Bottle", "--fail-on-manual-review")
        self.assertEqual(result.returncode, 1)

    def test_58_fail_on_error_retains_legacy_behavior(self):
        result = self.run_cli("--title", "X" * 76, "--fail-on-error")
        self.assertEqual(result.returncode, 1)

    def test_59_single_cli_context_can_be_ready(self):
        result = self.run_cli(
            "--title", "Brand Water Bottle, 32 oz",
            "--marketplace", "US",
            "--locale", "en_US",
            "--product-type", "DRINKING_CUP",
            "--parentage-level", "standalone",
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["review_status"], "READY")

    def test_60_batch_cli_context_fills_missing_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "titles.json"
            output = Path(directory) / "audit.json"
            source.write_text(json.dumps([{"title": "Brand Water Bottle"}]), encoding="utf-8")
            result = self.run_cli(
                "--input", source,
                "--output", output,
                "--marketplace", "US",
                "--locale", "en_US",
                "--product-type", "DRINKING_CUP",
                "--parentage-level", "standalone",
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))[0]["review_status"], "READY")


if __name__ == "__main__":
    unittest.main()
