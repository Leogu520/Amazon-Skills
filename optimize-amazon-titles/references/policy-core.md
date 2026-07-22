# Amazon Title Policy Core

Last verified: 2026-07-21

Use this file as a policy baseline, not as a substitute for the current marketplace help page or Product Type Definition schema.

Bundled validator baseline: `US`/`en_US` and `UK`/`en_GB`. These contexts still require `marketplace`, `locale`, `product_type`, and `parentage_level`. Other contexts retain the 75/125 fallback checks but return `MANUAL_REVIEW` until the current target schema is verified.

## Current Baseline

- Starting July 27, 2026, product titles in all categories except media must be 75 characters or fewer, including spaces.
- Item Highlights provides another 125 characters for materials, recommended uses, and comparison information.
- Amazon states that Item Highlights is searchable and visible with titles in search results and on product detail pages.
- Titles still over 75 characters after the effective date may be gradually updated to Amazon's AI recommendation.
- Listings remain active during that process.
- Brand owners receive a 14-day review period before recommended changes are implemented.
- Books and DVDs are not affected by the 75-character change at the time of verification.
- Item Highlights was still rolling out at the time of verification, and Amazon moderators acknowledged that some sellers experienced errors or changes not saving. When the field is unavailable, keep the proposed text in the audit output and mark publication pending rather than retaining a noncompliant long title.

Primary sources:

- US announcement: https://sellercentral.amazon.com/seller-forums/discussions/t/145b6d0f-999c-4555-896c-c694bda2e470
- Amazon Q&A: https://sellercentral.amazon.com/seller-forums/discussions/t/ac660707-60c7-43e3-a3fd-420d7321cc4e
- Media clarification: https://sellercentral.amazon.com/seller-forums/discussions/t/ae5ffd79-c7f5-4f3e-8739-fb87bb77b6f4
- UK announcement: https://sellercentral.amazon.co.uk/seller-forums/discussions/t/33f0a42a-17f1-46ef-b110-ba7512a3c881
- Germany announcement: https://sellercentral.amazon.de/seller-forums/discussions/t/d24be94b-9ca5-437f-a7c2-1f4f7462a15f
- Item Highlights rollout issue: https://sellercentral.amazon.com/seller-forums/discussions/t/03248ae4-c13b-4c63-aa37-03b42b285d70

## Existing General Title Rules

The January 21, 2025 policy established these general requirements:

- Most product categories had a maximum of 200 characters including spaces before the 2026 field split.
- The characters `!`, `$`, `?`, `_`, `{`, `}`, `^`, `¬`, and `¦` are not allowed unless part of the brand name.
- A title may not contain the same word more than twice. Prepositions, articles, and conjunctions are exceptions.

The 2026 announcement changes the length and field allocation. It does not state that the other rules were repealed. Continue applying them unless current Seller Central guidance or a product-type schema says otherwise.

Source: https://sellercentral.amazon.com/seller-forums/discussions/t/b2b15728-0d43-453e-974f-59eb63f73059/

## Schema and Marketplace Checks

Use the Product Type Definitions API when authenticated access is available:

- Search product types for the marketplace.
- Retrieve the exact schema with `marketplaceIds`, `locale`, and `parentageLevel`.
- Use `requirementsEnforced=ENFORCED` for submission-level validation.
- Inspect string length, enum, required-property, and variation constraints.
- Compute both visible character count and UTF-8 byte length. Amazon's meta-schema supports `maxUtf8ByteLength`, so byte constraints can matter for non-ASCII text.

Official documentation:

- https://developer-docs.amazon.com/sp-api/docs/search-available-product-type-definitions
- https://developer-docs.amazon.com/sp-api/lang-en_EN/docs/retrieve-a-product-type-definition
- https://developer-docs.amazon.com/sp-api/docs/product-type-definition-meta-schema

## Policy Refresh Rule

Re-verify official sources when any of these are true:

- The task occurs after the last verified date and involves bulk or production-sensitive changes.
- Seller Central rejects a title that passes the local validator.
- The marketplace, product type, or title field behavior differs from the baseline.
- Item Highlights is unavailable, fails to save, or displays differently.

Do not promise that Item Highlights and Title have identical ranking weight. Amazon states that both are searchable but does not publish equivalent field weighting.

The bundled validator counts Unicode code points and UTF-8 bytes. Repeated-word detection is best-effort for space-delimited languages. Seller Central and the current product-type schema remain authoritative for final acceptance, especially for CJK text, combining characters, and marketplace-specific tokenization.

The validator's full promotional, repeated-word, compatibility, and evidence-claim patterns are English-first. Non-English titles receive length and hard-character checks plus `UNSUPPORTED_TITLE_LANGUAGE`; they must not be described as fully audited.

`media_exempt` is not proof. The bundled validator applies a local exemption only for recognized `ABIS_BOOK`, `BOOK`, `BOOKS`, or `DVD` Product Types in a complete matching policy context. All other exemption requests remain subject to the 75-character fallback and manual review.
