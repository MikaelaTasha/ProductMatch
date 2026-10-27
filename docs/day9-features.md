# Day 9: compare product details

Implemented 2026-10-27. Run after importing the database:

```sh
python -m scripts.preview_features
```

This reads training pairs, prints aggregate evidence counts and writes
`artifacts/day9-feature-summary.json`. It does not fit a model or change the
browser. The [published summary](day9-feature-summary.json) contains no listing
text. Original database values and benchmark labels remain unchanged.

## Example

| Evidence | 2 × 4GB | 1 × 8GB | Comparison |
| --- | ---: | ---: | --- |
| Total capacity | 8GB | 8GB | agrees |
| Module count | 2 | 1 | differs |
| Capacity per module | 4GB | 8GB | differs |

Under our product definition these configurations are different. The code
records those evidence states; it does not yet turn them into a prediction.

## Feature dictionary

`attribute-comparisons-v1` uses `title-attributes-v1` extraction from original
titles. Every field has five possible states:

| State | Meaning |
| --- | --- |
| missing_both | Neither title has supported evidence |
| missing_one | Only one title has supported evidence |
| ambiguous | Both have evidence and at least one has multiple distinct values |
| agrees | Each has one distinct value and they are equal |
| differs | Each has one distinct value and they differ |

Missing takes precedence over ambiguity. Repeated identical mentions count as
one distinct value. `agrees` and `differs` describe extracted evidence, not
verified product identity. Two different compatible-printer codes may be
mentioned by listings for the same cartridge.

| Field | Values compared |
| --- | --- |
| model_candidate | Lowercase candidate model tokens; punctuation retained |
| storage_mention / volume_mention | Plain capacity mentions with unspecified role, in GB / ml |
| storage_per_item / volume_per_item | Explicit capacity per item in a pack, in GB / ml |
| storage_total / volume_total | Totals calculated only from explicit pack expressions |
| storage_count / volume_count | Counts from explicit capacity-bearing pack expressions |
| frequency | MHz, converting GHz using the Day 8 convention |
| pack_count | Explicit pack/packs counts |
| sheet_count | Explicit sheet/sheets counts |
| piece_count | Explicit piece/pieces/pcs counts |
| module_count | Explicit module/modules counts |

These 14 fields each produce five 0/1 columns, named `<field>_<state>`.
Exactly one column per field is 1: 70 numeric features with stable ordering in
`FEATURE_NAMES`. Features are symmetric when listings are swapped and never
use benchmark labels, IDs, cluster membership or split identity.

Evidence arrays are also returned for inspection. Plain `16GB` is not inferred
to be a total and cannot be directly compared with the total calculated from
`2x8GB`. Generic module counts are kept separate from storage pack counts.
This conservative choice loses some usable comparisons; future changes must
be versioned and evaluated. Frequency, model-token and unsupported-unit limits
from Day 8 still apply. Brand is audited in SQL but is not a feature yet.

## SQL quality and evidence coverage

The readable [SQL query](../sql/day9-quality.sql) joins each training pair to
its two listings, then aggregates missing titles/brands and broken references.
It uses LEFT JOIN so broken references would not silently disappear. Missing
means NULL or empty after SQLite `trim` (spaces only); other whitespace or
placeholder strings are not covered by this SQL audit.

On 2,500 training pairs: 500 benchmark matches, zero broken references, zero
pairs with missing titles, and 2,123 pairs with at least one missing brand.
Candidate-model evidence agrees in 134 pairs and differs in 530; 895 pairs
have ambiguous model evidence. These are not correctness or conflict-accuracy
measurements. Each field's five counts sums to 2,500. Some fields have no
observed values in this training set and cannot teach a model useful variation.

The 500 labels appear only in the SQL summary; changing labels does not change
comparison features. No validation or test set was evaluated. No improvement
in match precision has been demonstrated. Day 10 will combine attribute
features with title similarity and evaluate a classifier on validation data.

## Verification and learning

All 49 tests pass. Seven new tests cover equal totals/different configurations,
missing/ambiguous states, unit equivalence, separate roles/count categories,
fixed feature order, symmetry, training-only reporting, read-only access and
label independence. Repeating the real-data report produced identical output
and left the database SHA-256 unchanged.

The user correctly calculated 2 × 4GB = 8GB. Independent explanation of why
pack configurations differ and Python/SQL exercises remain pending.

Practice: inspect the SQL query and explain why `listings` is joined twice.
Then write an aggregation counting training pairs where both brands are present.
