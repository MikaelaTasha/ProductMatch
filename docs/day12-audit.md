# Day 12: validation errors and split overlap

Audited 2026-10-27. Reproduce locally:

```sh
python -m scripts.check_wdc_splits
python -m scripts.audit_day12
```

The first command rechecks the five pinned raw-file hashes and dataset counts
(including label counts), without scoring test data. The new audit reads test
IDs, cluster IDs and source metadata only. It scores training/validation data
with the unchanged Day 10 classifier and Day 11 policy. No test predictions or
performance were computed. Original files, database and labels are preserved.

The [published aggregate report](day12-audit-results.json) contains no listing
text. Up to five examples per error type are saved locally in ignored
`artifacts/day12-validation-examples.json`. These select the highest-scoring
false matches and lowest-scoring missed matches, with pair ID breaking ties.
They are deliberately difficult examples, not a representative random sample.

## Validation findings

The audit reproduces 342 binary false matches, 137 binary missed matches and
79 incorrect automatic Different decisions under the default review policy.
The review queue has 917 pairs. These groups overlap; do not add their counts.

| Extracted model evidence | Binary false matches | Binary missed matches | Review-policy false Different |
| --- | ---: | ---: | ---: |
| Missing on both | 57 | 11 | 5 |
| Missing on one | 61 | 45 | 27 |
| Multiple candidates | 164 | 50 | 24 |
| Single candidates agree | 24 | 2 | 1 |
| Single candidates differ | 36 | 29 | 22 |

A difference between extracted tokens is not necessarily a true product
conflict. Likewise equal capacity does not establish identity. Among binary
false matches, plain storage capacity agrees in 39 cases, is missing on both
sides in 301, and missing on one side in 2. No plain-storage conflict is detected
in this group, so merely rejecting detected capacity conflicts cannot fix it.

Inspection of the local examples suggests this error taxonomy:

| Category | Observed evidence and implication |
| --- | --- |
| Code spelling and segmentation | Hyphens, spaces and code prefixes differ in headphones and cartridge examples. Exact candidate comparisons can miss aliases. |
| Missing details and language differences | A capacity or code appears on only one side; English/German wording differs. Missing evidence must remain uncertainty. |
| Unit formatting | A benchmark match uses mixed-case `Gb` and split `M Hz`; the conservative extractor skips some evidence. Changing this globally risks confusing bits and bytes. |
| Unmodeled variants | False-match examples distinguish laptop SO-DIMM from desktop UDIMM memory, pin counts, graphics-card editions, and drive variants. Equal brand/capacity does not capture these distinctions. |
| Insufficient title evidence or label ambiguity | One high-scoring negative has apparently compatible drive titles, but missing attributes prevent adjudication. Do not override the benchmark label from titles alone. |

These are hypotheses from ten unique inspected pairs (the five review-policy
examples repeat five binary missed matches), not verified root causes for every
error. Labels were not changed. No product facts were inferred from external
catalogs. The full numeric evidence slices are available in the aggregate report.

## Split metadata findings

Pairs are compared as unordered offer-ID tuples, so reversed orientation still
counts as the same pair. Cluster pairs are likewise unordered; shared cluster
pairs do not necessarily mean identical offers.

| Development/test comparison | Shared offers | Shared product clusters | Exact shared pairs |
| --- | ---: | ---: | ---: |
| Train / validation | 0 | 500 | 0 |
| Train / seen test | 0 | 500 | 0 |
| Validation / seen test | 4 | 500 | 0 |
| Train / half-unseen test | 110 | 250 | 20 |
| Validation / half-unseen test | 106 | 250 | 23 |
| Train / unseen test | 0 | 0 | 0 |
| Validation / unseen test | 0 | 0 | 0 |

Training and validation use different offers from the same 500 benchmark
product clusters. Validation therefore does not demonstrate generalization to
new product clusters. Shared clusters in seen-product settings are a different
issue from exact repeated offers or pairs; do not conflate them.

Counting each test pair once when either endpoint occurs in the union of train
and validation gives:

| Test split | Pairs | Touch development offers | Remaining if filtered |
| --- | ---: | ---: | ---: |
| Seen | 4,500 | 35 | 4,465 |
| Half-unseen | 4,500 | 1,664 | 2,836 |
| Unseen | 4,500 | 0 | 4,500 |

The half-unseen test also shares 35 exact pairs with seen test and 288 with
unseen test. Test sets must be reported separately, not pooled as independent
examples. All five raw-file hashes/counts still match the pinned snapshot,
so this is not explained by a changed local download. The publisher-side cause
of the overlap remains unverified; we have not contacted the publisher or
silently repaired the benchmark.

## Evaluation options to finalize on Day 13

1. Prefer the official unseen test as the primary new-cluster evaluation after
   freezing the model and thresholds. It has no measured development overlap
   by offer ID, cluster ID or pair. This is a bounded structural finding, not
   proof that all possible semantic leakage has been excluded.
2. Report original seen/half-unseen results separately as overlap-contaminated
   secondary benchmark results, with the counts above attached.
3. Optionally add explicitly labeled supplementary subsets excluding any pair
   touching a development offer. Preserve official files and report subset sizes
   and selection rules. These are not the unchanged official benchmark and may
   have different class/difficulty distributions. No subset performance has
   been inspected to choose this option.

No test-label-driven decisions, test score inspection or threshold adjustment
has occurred in this audit. Do not claim seen/half-unseen results are leakage-free.
Any future supplementary filter must be fixed before scoring.

## Next improvement and checks

Day 13 candidate: add an auxiliary punctuation-insensitive model-code comparison
while preserving the original candidate and ambiguity states. The observed
hyphenation failures justify testing it, but it must remain soft evidence—not
an automatic identity rule. Measure its validation trade-off, retain or reject
it, then freeze the selected configuration and evaluation protocol. Broader
variant extraction is a separate future option, not a change made today.

All 64 tests pass. New checks cover reversed pairs, shared clusters with disjoint
offers, development-union counting, missing-reference rejection, metadata
independence from title/label changes, error-count reconciliation and validation-
only samples. The real audit repeats exactly and leaves the database hash
unchanged. Independent learning exercise: explain why different offers from
the same product cluster are not a test of unseen-product performance.
