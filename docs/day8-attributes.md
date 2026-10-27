# Day 8: extract product details

Implemented 2026-10-27. Run after importing the database:

```sh
python -m scripts.preview_attributes --examples 5
```

The command reads unique training listings only. Original titles and database
records stay unchanged. The Streamlit browser still displays original listings
and benchmark labels; this extractor is currently a separate command.

## What the extractor records

For the teaching example `Kingston HyperX HX316C10F/8 DDR3 2x8GB 1600MHz`:

| Detail | Extracted evidence |
| --- | --- |
| Possible model | `hx316c10f/8`, with original spelling retained |
| Explicit module count | 2 |
| Capacity per module | 8 GB |
| Calculated total | 16 GB |
| Frequency | 1600 MHz |

Model candidates have lowercase comparison values. Original text and unit spelling
are retained: lowercasing everything first would erase the distinction between
`GB` and `Gb`. Mixed-case `Gb`/`Tb` are skipped; lowercase `gb`/`tb` are accepted
as common title spellings, which remains an ambiguity.

Measurements support GB/TB, ml/L and MHz/GHz. The conversion convention is
1 TB = 1000 GB, 1 L = 1000 ml and 1 GHz = 1000 MHz. GiB/TiB are unsupported.
Explicit `2x8GB` or `2×8GB` records per-item and calculated total values.
A plain `8GB` has an unspecified role; it does not establish pack quantity.
For `16GB (2x8GB)`, both pieces of evidence are retained separately.

Count expressions include `2-pack`, `20 sheets`, pieces, pcs and modules.
Multiple mentions remain candidates rather than being collapsed into one answer.
Bare dimensions such as `29 x 2.4` are not pack counts. Missing flags mean
"no supported evidence extracted," not "the product lacks this attribute."

## Measured coverage

The [aggregate report](day8-attribute-coverage.json) covers 1,000 unique training
titles. Evidence was found in:

| Evidence | Titles |
| --- | ---: |
| Model candidates | 762 |
| Storage capacity | 173 |
| Volume | 21 |
| Frequency | 43 |
| Explicit pack/count | 26 |

These categories overlap. These numbers measure extraction coverage, not
extraction accuracy or matching quality. No validation or test pairs were used
for this preview. Only the aggregate report is published.

## Limits and checks

Model candidates are letter-and-digit tokens, not verified model numbers. A
compatible printer code can refer to another product; dimensions and other
unrecognized tokens can also appear as candidates. Numeric-only model codes,
brand inference, descriptions, comma decimals, multilingual quantity terms and
many measurement units are unsupported. Multiple capacities may describe
compatibility or available options rather than the item for sale.

Do not automatically merge or reject products from these candidates alone.
Day 9 will compare evidence while preserving missing and ambiguous information.
No improvement over the Day 7 baseline has been measured yet.

All 42 tests passed, including nine extractor tests for pack arithmetic, units,
unknown values, dimensions, code/rate exclusions, multiple model candidates and
invalid input. The real training preview left the database SHA-256 unchanged.
Five training titles with pack expressions were also inspected; this is a small
spot check, not an annotated extraction evaluation.

## Learning progress

The user correctly identified the model, count and per-module capacity in the
example. The fourth answer was frequency rather than total capacity. We clarified
that 2 × 8 GB = 16 GB and MHz measures frequency. Independent follow-up arithmetic
and a Python extraction exercise remain pending.
