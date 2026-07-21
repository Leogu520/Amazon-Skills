# Category Profiles

Select the closest profile by product identity. If multiple profiles apply, combine their required checks and use the stricter risk level.

## General Consumer Goods

Examples: home, kitchen, office, garden, pet, sports, travel, and basic tools.

Preferred order:

`Brand + Core Product Type + Primary Differentiator + Size/Count/Color`

Preserve:

- Product type
- Capacity, dimensions, count, or selected variation when purchase-critical
- One differentiating material or function when verified

Move first:

- Long use-case lists
- Secondary materials and features
- Gift language and subjective quality claims

## Apparel, Footwear, and Accessories

Preferred order:

`Brand + Product Type + Audience/Gender if required + Style/Material + Child Size/Color`

Required checks:

- Distinguish parent title from child variation title.
- Confirm whether size and color are appended or supplied in `item_name` for the exact schema.
- Do not place one child's color or size in a parent title.
- Preserve pack count and fit type when they materially distinguish the product.

Risk: medium because variation rendering differs by product type and marketplace.

## Electronics and Electrical Products

Preferred order:

`Brand + Product Type + Model/Interface + Power/Capacity + Port/Pack Count`

Preserve:

- Model or generation
- Connector or interface
- Power, voltage, capacity, or protocol when purchase-critical
- Included quantity and cable/accessory status when needed to prevent misbuy

Flag:

- Unsupported fast-charging, waterproof, safety, or certification claims
- Ambiguous compatibility lists
- Trademarked device names without clear relationship wording

## Automotive, Replacement Parts, and Compatibility Products

Preferred order:

`Brand + Part Type + Position/Key Spec + Compatible with/Fits + Make/Model/Year Range`

Preserve:

- Part type and installation position
- `Compatible with`, `Fits`, or equivalent relationship wording
- Make, model, year range, engine, OE number, or dimensions needed to prevent misfit

Never compress a year range or compatibility list in a way that changes coverage. If 75 characters cannot carry enough fitment information, keep the highest-level safe identifier in Title and move verified detail to Item Highlights or fitment attributes. Mark `MANUAL_REVIEW`.

Risk: high for trademark wording, fitment accuracy, and returns.

## Industrial, Hardware, and B2B Components

Preferred order:

`Brand + Component Type + Standard/Material + Critical Dimensions + Pack Count`

Preserve:

- Standard, thread, gauge, tolerance, material grade, dimensions, or connection type
- Pack quantity
- Model or part number when used for procurement

Avoid replacing precise specifications with broad benefits. Mark `MANUAL_REVIEW` when the title cannot identify the exact component within the limit.

## Beauty and Personal Care

Preferred order:

`Brand + Product Type + Form/Primary Ingredient + Size/Count + Variant`

Preserve:

- Product form
- Net quantity
- Shade, scent, skin/hair type, or variant when purchase-critical

Flag all therapeutic, clinical, hypoallergenic, organic, non-toxic, cruelty-free, and certification claims unless verified. Do not convert cosmetic benefits into medical claims.

Risk: high for claims and marketplace-specific restrictions.

## Grocery, Supplements, and Consumables

Preferred order:

`Brand + Product Type + Flavor/Form + Strength if lawful + Net Quantity/Count`

Preserve:

- Flavor or form
- Count, weight, volume, and concentration when applicable
- Dietary attribute only when verified

Flag disease, treatment, prevention, weight-loss, immunity, FDA-approval, organic, allergen-free, and performance claims. Do not infer nutrition or ingredient properties.

Risk: high. Default to `MANUAL_REVIEW` when claims or regulatory classification are unclear.

## Baby and Children's Products

Preferred order:

`Brand + Product Type + Verified Age/Weight Range + Critical Size/Count/Use Boundary`

Preserve:

- Accurate age or weight range when relevant
- Product type and intended use
- Size, quantity, and safety-critical limitations

Flag sleep, medical, developmental, safety, non-toxic, BPA-free, and certification claims unless supported. Ensure title, packaging, instructions, tests, and listing use cases agree.

Risk: high. Default to `MANUAL_REVIEW` for safety-sensitive products.

## Toys and Games

Preferred order:

`Brand + Product Type/Game Name + Verified Age Range + Piece/Player Count + Variant`

Preserve:

- Age grading
- Piece count or player count
- Licensed character or franchise wording only when authorized

Flag developmental, educational, safety, and licensing claims when evidence is absent.

## Bundles, Multipacks, and Kits

Preferred order:

`Brand + Bundle/Kit Identity + Main Components + Total Count/Size`

Preserve:

- Exact included components
- Pack or piece count
- Size and variant boundaries

Do not imply accessories are included when they are not. Compare title contents against structured package data and images. Mark `MANUAL_REVIEW` for virtual bundles or mixed-brand bundles.

## Media

Books and DVDs were exempt from the 2026 75-character requirement at the last policy verification. Do not force a 75-character rewrite merely because the title is long. Verify current media guidance and preserve canonical work title, edition, author/artist, format, and volume information as required.

