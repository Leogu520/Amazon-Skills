# Risk and Claims Review

Mark `MANUAL_REVIEW` whenever a title change can alter factual, legal, compatibility, variation, or safety meaning.

## Evidence-Sensitive Claims

Examples include:

- BPA-free, non-toxic, food-safe, child-safe
- Waterproof or water-resistant ratings
- Organic, natural, sustainable, eco-friendly, recyclable
- Hypoallergenic, dermatologist-tested, clinically proven
- Medical-grade, FDA-approved, prevents, treats, cures, relieves
- Fireproof, flame-resistant, antimicrobial
- Certified, compliant, tested, approved
- Exact duration, speed, strength, load, temperature, or efficiency claims

Require a supplied evidence boundary such as a test report, certification scope, packaging statement, controlled product specification, or explicit user confirmation. Do not infer evidence from competitor listings.

## Compatibility and Trademark Wording

- Preserve `Compatible with`, `Fits`, `Replacement for`, or an equivalent relationship phrase when it distinguishes a third-party product from the referenced brand's own product.
- Do not shorten a third-party compatibility title into wording that can imply origin, sponsorship, or brand ownership.
- Verify make, model, generation, year, engine, connector, and OE/part number against structured source data.
- Flag any AI rewrite that introduces a trademark not present in verified source data.

## Parent and Child Variations

- Never copy one child's color, size, flavor, count, or model into the parent title.
- Verify whether the marketplace renders variation attributes from `item_name` or appends them separately.
- Audit the final displayed child title, not only the source parent title.
- Leave character headroom when a downstream system may append variation text.

## Bundles and Package Contents

- Preserve exact counts and included components.
- Do not convert `works with` into `includes`.
- Do not imply a cable, battery, case, mount, refill, or accessory is included without structured evidence.

## Regulated and Safety-Sensitive Products

Default to manual review for:

- Baby sleep, restraint, carrying, feeding, and durable nursery products
- Medical devices and products making health claims
- Supplements and ingestibles
- Cosmetics using therapeutic language
- Protective equipment and products with safety ratings
- Batteries, chargers, electrical safety, and radio products

The title can affect how a product is classified. A shorter title must not erase intended-use language needed for accurate classification, or introduce a new intended use not supported by the product.

## Shared Detail Pages and Data Ownership

- A seller's submitted title may not control the live detail page when multiple contributors supply catalog data.
- Record the source title and proposed title before editing.
- Check `View Change History` after any approved change.
- Identify ERP, PIM, feed, template, API, and manual-edit sources that can overwrite one another.

## Multilingual Listings

- Rebuild character priorities per locale; do not translate an English title word for word.
- Preserve units, decimal conventions, and standard local product terminology.
- Count both Unicode code points and UTF-8 bytes.
- Treat machine translation of compatibility, safety, age, and regulatory terms as manual-review content.

