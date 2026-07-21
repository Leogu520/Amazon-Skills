---
name: optimize-amazon-titles
description: Rewrite and audit Amazon product titles under the applicable marketplace and category rules, including the 75-character title requirement, keyword prioritization, product attributes, variations, compatibility wording, Item Highlights allocation, and risk flags. Use when users ask to shorten, optimize, review, compare, or batch-process Amazon listing titles from text, CSV, JSON, or spreadsheets, or when they need a title migration plan without directly publishing changes.
---

# Optimize Amazon Titles

Rewrite Amazon titles as product-identity fields, not keyword containers. Preserve facts that prevent wrong purchases, allocate secondary information to the correct listing fields, and validate every proposed title deterministically.

## Safety Boundary

- Generate recommendations and audit files only. Do not publish or write changes to Seller Central unless the user separately requests and approves that external action.
- Never invent an attribute, certification, performance claim, compatibility relationship, age range, quantity, material, or model number.
- Treat existing listing text as a claim source, not proof. Flag evidence-sensitive claims unless the user supplies supporting evidence or marks them verified.
- Preserve wording that defines a legal or commercial relationship, such as `Compatible with`, when a third-party brand is referenced. Escalate ambiguous trademark wording for human review.
- Treat marketplace validation and current Seller Central guidance as authoritative when they conflict with this skill.

## Load References

Always read [policy-core.md](references/policy-core.md).

Then read only the references needed for the task:

- Read [category-profiles.md](references/category-profiles.md) to select the title slot order and mandatory review points.
- Read [keyword-priority.md](references/keyword-priority.md) when search-query, advertising, Brand Analytics, or keyword files are available.
- Read [risk-and-claims.md](references/risk-and-claims.md) for regulated goods, compatibility products, bundles, variations, multilingual listings, or any factual claim.

## Choose the Mode

### Rewrite Mode

Use when the user provides product facts and wants new titles. Produce one recommended title and up to two materially different alternatives.

### Audit Mode

Use when the user provides an existing or proposed title. Do not silently rewrite. Report compliance, missing purchase-critical information, keyword problems, and risk flags before offering a revision.

### Batch Mode

Use for CSV, JSON, or spreadsheet inputs. Process every row independently. Do not block the whole batch because some rows are incomplete; mark those rows `MANUAL_REVIEW` and state the missing fields.

For `.xlsx` files, use the spreadsheet tooling to preserve workbook structure. Use the bundled validator on exported or extracted row data, then write results back to a new sheet or new output file. Never overwrite the source workbook unless explicitly requested.

## Required Inputs

Collect or derive these fields where available:

- Marketplace and locale
- Product type or category
- Parent, child, or standalone status
- Current title
- Brand and product line
- Core product type
- Variation attributes: size, color, count, style, flavor, or model
- Purchase-critical specifications: dimensions, capacity, power, interface, fitment, age/weight range, or included components
- Verified claims and evidence boundaries
- Primary and secondary keywords with performance data when available

If marketplace, core product type, or purchase-critical attributes are missing, ask one concise question for a single listing. In batch mode, continue and flag the row.

## Workflow

### 1. Establish the Rule Context

Identify marketplace, locale, product type, variation level, and whether the item is in an exempt media category. Verify current official Amazon policy online before high-volume or production-sensitive work because title rules and schema constraints can change.

When SP-API access is available, prefer the current Product Type Definition for the exact marketplace, locale, product type, and `parentageLevel`. Do not substitute a generic category template for a live schema.

### 2. Separate Facts from Marketing Language

Create three internal sets:

- `verified_facts`: supplied structured attributes and explicitly verified claims
- `candidate_terms`: relevant keywords and existing title phrases
- `prohibited_or_unverified`: unsupported claims, promotional language, irrelevant traffic terms, and ambiguous compatibility statements

Only `verified_facts` and defensible `candidate_terms` may enter a proposed title.

### 3. Select the Category Profile

Use [category-profiles.md](references/category-profiles.md). Preserve the profile's purchase-critical attributes before adding secondary differentiators.

If the product spans profiles, use the stricter profile. For example, an electronic baby monitor uses both Electronics and Baby/Children review requirements.

### 4. Prioritize Keywords and Attributes

Use this precedence:

1. Required identity, variation, safety, fitment, and anti-misbuy information
2. Exact core product term
3. Proven high-contribution query terms that accurately describe the ASIN
4. One primary differentiating attribute
5. Secondary material, use-case, and feature terms
6. Synonyms and broad discovery terms

Move levels 5 and 6 to Item Highlights, bullet points, descriptions, or backend search terms when space is constrained. Never sacrifice level 1 to retain a higher-volume generic term.

### 5. Build Candidates

Start from the selected category profile, not from the old title's word order. Use concise standard units and natural marketplace language.

For non-media products under the current 75-character policy:

- Keep every candidate at 75 characters or fewer, including spaces and punctuation.
- Prefer a working range around 55-70 characters when the product can still be identified accurately. This is a heuristic, not a policy requirement.
- Leave headroom when Amazon, a feed, or a variation process may append size, color, or count.

Do not create alternatives that differ only by punctuation or trivial word order. Each alternative must test a real information-priority hypothesis.

### 6. Allocate Removed Information

For each removed phrase, choose one destination:

- Item Highlights: material, use case, and second-level comparison information
- Bullet points: benefits, operation, dimensions, package contents, and limitations
- Backend search terms: relevant synonyms and alternate generic expressions
- Delete: duplication, subjective adjectives, promotions, unverifiable claims, and irrelevant traffic terms

Do not treat Item Highlights as a replacement for bullet points.

### 7. Validate Deterministically

Run `scripts/validate_titles.py` on every final candidate. Fix all errors before presenting a recommendation. Review all warnings and either resolve them or surface them explicitly.

Single title:

```powershell
python scripts/validate_titles.py --title "NovaTrail Stainless Steel Water Bottle, 32 oz, Leakproof, BPA-Free" --brand "NovaTrail" --locale en_US --required "Water Bottle" --required "32 oz"
```

Batch CSV or JSON:

```powershell
python scripts/validate_titles.py --input titles.csv --output title_audit.csv
python scripts/validate_titles.py --input titles.json --output title_audit.json
```

If `python` is unavailable, locate the configured workspace Python runtime. The script uses only the Python standard library.

### 8. Present the Result

For a single listing, return:

| Field | Required content |
|---|---|
| Recommended title | Final title and exact character count |
| Alternatives | Up to two distinct compliant options |
| Item Highlights | Proposed secondary information, within the currently applicable limit |
| Retained | Keywords and attributes kept in the title |
| Moved | Phrase, destination field, and reason |
| Deleted | Phrase and reason |
| Risks | Claims, compatibility, variation, or policy concerns |
| Review status | `READY`, `READY_WITH_WARNINGS`, or `MANUAL_REVIEW` |

For batch work, preserve source columns and append:

`recommended_title`, `char_count`, `item_highlights`, `item_highlights_char_count`, `retained_terms`, `moved_terms`, `deleted_terms`, `errors`, `warnings`, `review_status`, and `review_reason`.

## Review Status Rules

- `READY`: all hard checks pass, required facts are present, and no unresolved evidence or relationship warning remains.
- `READY_WITH_WARNINGS`: hard checks pass, but non-blocking style or data-quality warnings remain.
- `MANUAL_REVIEW`: missing purchase-critical facts, unverified sensitive claims, compatibility or trademark ambiguity, parent-child uncertainty, regulated-product risk, or conflicting source data.

Never label a title `READY` solely because it fits the character limit.
