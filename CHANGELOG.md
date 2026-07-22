# Changelog

## v1.1.0 - 2026-07-21

- Add `schema_version`, `review_status`, `review_reasons`, `risk_codes`, and `policy_context` while preserving legacy validator fields.
- Route deterministic errors, unverified claims, ambiguous compatibility, incomplete policy context, unsupported title languages, and unverified exemptions to `MANUAL_REVIEW`.
- Replace fuzzy claim verification with canonical IDs and exact aliases.
- Restrict media exemptions to recognized Product Types in matching policy contexts.
- Add source overwrite protection and `--fail-on-manual-review`.
- Move duplicate package tests into a 64-scenario shared suite and add byte-parity CI checks.
- Add a blind-eval exporter so fresh agents cannot read held-out reference fields.
- Add a 10-case, five-dimension rewrite-quality forward-test dataset.
- Clarify that the Simplified Chinese package is a Chinese operator interface, not a complete Chinese-title compliance engine.
