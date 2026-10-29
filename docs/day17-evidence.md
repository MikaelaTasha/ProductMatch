# Day 17: readable matching evidence

Implemented 2026-10-29. Open the Streamlit Review queue, choose a pair and scroll
to **Details to check**. The panel adds:

- A plain-language explanation of how the stored score falls within its recorded
  decision thresholds, including when automatic Match is disabled.
- Side-by-side extracted model candidates, capacities, frequencies and counts,
  with units and separate per-item/total roles.
- Distinct states for agreeing values, differing values, multiple candidates and
  missing evidence. Details missing on both sides are hidden by default and can
  be shown with the checkbox.
- A separate punctuation-insensitive code comparison and an expandable view of
  title similarity, score and thresholds.

For example, `AB-12 2x4GB` versus `AB12 1x8GB` has equal calculated total storage,
but different counts and per-item capacities. Original model candidates differ;
the auxiliary punctuation-insensitive comparison agrees. Neither observation
alone determines product identity.

## Meaning and limits

The summary counts evidence fields, not independent votes or probabilities.
Fields are correlated: total, count and per-item capacity describe related facts.
An agreeing candidate may be a compatibility reference rather than the item's
model. The extractor can miss meaningful information such as dosage, dimensions
or product variants; always inspect the original listings.

The score-range explanation describes the decision policy, not why each feature
caused a model score. This is not a feature-attribution method or verified factual
explanation. No coefficient-weighted contribution or causal claim is made.
Existing matching-quality limitations remain; no model improvement is claimed.

## Fidelity to the stored prediction

The display uses the stored title snapshot and the ordered feature names from
its stored freeze record. It reconstructs the attribute/alias evidence and checks
that every indicator matches the stored vector before showing it. Title similarity
is read from the stored vector; it is not recalculated with a new vocabulary.
The decision is also checked against the recorded score and thresholds.

Unsupported models, malformed vectors, changed evidence or a decision/threshold
mismatch produce an unavailable-evidence warning. Original listings and the
manual review form remain available. The panel supports the Day 10 and selected
Day 13 schemas; it does not silently reinterpret arbitrary future schemas.
Displayed numbers are rounded, while decision checks use full stored values.

This reads records only. It does not alter the frozen pipeline, source database,
prediction store, benchmark labels or human judgments. No test set was rescored.

## Verification

All 92 tests pass, including six new checks for pack distinctions, aliases,
missing/ambiguous values, stale evidence rejection, schema/numeric validation,
threshold equality and UI rendering without review writes. All 2,500 real stored
predictions passed evidence consistency checks. Frozen pipeline verification
still passes. The live review page was inspected with a real training pair;
its summary, disabled-Match explanation and threshold section rendered. No real
review was submitted during verification; the real review count was zero.

Day 18 will add a local pipeline command and automated GitHub checks. Independent
learning exercise: why can equal total capacity still describe different products?
