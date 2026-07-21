# Amazon Title Optimizer Skill

[简体中文](README.zh-CN.md)

An open-source Codex skill for rewriting and auditing Amazon product titles across product categories.

It combines category-aware title composition with deterministic validation for title length, Item Highlights length, duplicate words, restricted characters, required attributes, compatibility wording, promotional content, and evidence-sensitive claims.

> This project is an independent seller operations tool. It is not affiliated with, endorsed by, or sponsored by Amazon.

## Why this exists

Amazon announced that, starting July 27, 2026, titles in non-media categories must be 75 characters or fewer, including spaces. The change also introduces a separate 125-character Item Highlights field. Shortening an existing title mechanically can remove model numbers, variation attributes, fitment information, pack counts, or other details that prevent wrong purchases.

This skill treats title optimization as an information-priority problem rather than a truncation task.

## Capabilities

- Rewrite or audit one listing title
- Process CSV, JSON, and spreadsheet batches
- Select title structures for major product-category families
- Prioritize verified product attributes and high-intent keywords
- Allocate removed content to Item Highlights, bullet points, descriptions, backend search terms, or deletion
- Flag compatibility, variation, regulated-product, and evidence risks
- Validate both Unicode character count and UTF-8 byte length
- Produce `READY`, `READY_WITH_WARNINGS`, or `MANUAL_REVIEW` recommendations

The skill intentionally does not publish changes to Seller Central.

## Included category profiles

- Home, kitchen, office, garden, pet, sports, travel, and tools
- Apparel, footwear, and accessories
- Electronics and electrical products
- Automotive and replacement parts
- Industrial and B2B components
- Beauty and personal care
- Grocery, supplements, and consumables
- Baby and children's products
- Toys and games
- Bundles, multipacks, and kits
- Media exemptions

## Install

Clone the repository, then copy the `optimize-amazon-titles` folder into your Codex skills directory.

Windows PowerShell:

```powershell
Copy-Item -Recurse .\optimize-amazon-titles "$HOME\.codex\skills\optimize-amazon-titles"
```

macOS or Linux:

```bash
cp -R ./optimize-amazon-titles ~/.codex/skills/optimize-amazon-titles
```

Open a new Codex task if the skill does not appear immediately.

## Use with Codex

```text
Use $optimize-amazon-titles to audit and rewrite these Amazon titles.
Preserve purchase-critical attributes and primary keywords.
Return the recommended title, Item Highlights, moved terms, deleted terms,
risk flags, and review status.
```

For a batch:

```text
Use $optimize-amazon-titles to process this spreadsheet.
Keep the source columns and append recommended_title, char_count,
item_highlights, retained_terms, moved_terms, deleted_terms,
errors, warnings, review_status, and review_reason.
```

## Deterministic validator

The validator uses only the Python standard library.

Single title:

```bash
python optimize-amazon-titles/scripts/validate_titles.py \
  --title "RoadForge Front Wheel Bearing Hub, Compatible with Audi A1 2010-2019" \
  --brand "RoadForge" \
  --required "Wheel Bearing Hub" \
  --required "Audi A1" \
  --referenced-brand "Audi"
```

Batch CSV or JSON:

```bash
python optimize-amazon-titles/scripts/validate_titles.py \
  --input examples/titles.csv \
  --output title-audit.csv
```

Input columns can include:

| Column | Purpose |
|---|---|
| `sku` | Seller SKU or row identifier |
| `title` | Existing or proposed title |
| `item_highlights` | Proposed Item Highlights text |
| `brand` | Brand name and restricted-character exception context |
| `locale` | Locale such as `en_US` or `de_DE` |
| `required_phrases` | Pipe-separated facts that must remain in Title |
| `verified_claims` | Pipe-separated claim labels backed by evidence |
| `referenced_brands` | Third-party brands used for compatibility |
| `media_exempt` | `true` when a verified media exemption applies |

## Validation

```bash
python -m unittest discover optimize-amazon-titles/scripts -p "test_*.py" -v
python -m py_compile optimize-amazon-titles/scripts/validate_titles.py
```

The test suite includes representative cases for consumer goods, electronics, automotive, industrial, beauty, apparel, baby, toys, media exemptions, compatibility wording, restricted characters, sensitive claims, and batch I/O.

## Policy maintenance

Amazon policies and product-type schemas change. The skill stores a dated policy baseline in `references/policy-core.md` and instructs the agent to re-verify official Amazon sources before bulk or production-sensitive work. Seller Central and the current Product Type Definition schema remain authoritative.

## License

[MIT](LICENSE)

