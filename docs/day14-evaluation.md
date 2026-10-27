# Day 14: frozen test evaluation

Executed 2026-10-27 after the Day 13 freeze passed verification. The model,
feature order, thresholds, data and evaluation protocol were not changed.
The [full aggregate report](day14-test-results.json) records all required counts,
thresholds, provenance, frozen-record hash and evaluation-runner hash.

## Primary result: unseen products

The official unseen test contains 4,500 pairs: 500 matches and 4,000 nonmatches.
The Day 12 metadata audit found no development overlap by offer, cluster or
pair ID. This is the primary generalization result under our fixed protocol.

The frozen Review policy produces:

| Decision | Actual match | Actual nonmatch | Total |
| --- | ---: | ---: | ---: |
| Automatic Match | 0 | 0 | 0 |
| Automatic Different | 109 | 2,584 | 2,693 |
| Review | 391 | 1,416 | 1,807 |

- Review rate: **40.16%**; automatic coverage: **59.84%**.
- Automatic Different precision: **95.95%** (2,584 / 2,693).
- Automatic Match precision: undefined; automatic-match recall: **0%**.
- The policy incorrectly rejects **109 of 500 actual matches (21.8%)**.

Review means routed for future human judgment, not correctly resolved. Having
zero automatic false matches while disabling Match is not successful automatic
matching. The Different precision exceeds the provisional validation target in
this sample, but is not a future guarantee.

The separately reported frozen binary diagnostic (no Review) has:

| Metric | Unseen test |
| --- | ---: |
| Precision | 23.61% |
| Recall | 67.20% |
| F1 | 34.95% |
| True matches found | 336 |
| False matches | 1,087 |
| Missed matches | 164 |
| Correct nonmatches | 2,913 |
| Accuracy | 72.20% |

Validation binary F1 was 60.47%; this test F1 is substantially lower. This
classifier is not ready for reliable automatic product merging. Validation used
seen clusters and a 20% positive rate; the test has unseen clusters and an 11.11%
positive rate. Both are relevant differences, but this evaluation does not
isolate their causal contributions. An always-Different classifier would have
88.89% accuracy here and zero match recall, illustrating why accuracy alone is
misleading.

Thirty-one unseen listings have zero TF-IDF vectors under the training vocabulary,
affecting 275 pairs. This is a diagnostic observation, not proof that those pairs
account for the errors. No test examples were inspected to change the model.

## Separate secondary results

Official seen and half-unseen sets are overlap-affected; half-unseen contains
exact repeated development pairs. Do not call these leakage-free results or
combine them with the primary result.

| Official set | Pairs | Review rate | Automatic coverage | Different precision | Incorrect Different | Binary precision | Binary recall | Binary F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Seen | 4,500 | 34.64% | 65.36% | 97.28% | 80 | 31.67% | 70.00% | 43.61% |
| Half-unseen | 4,500 | 37.84% | 62.16% | 97.53% | 69 | 29.42% | 74.20% | 42.14% |

Both contain 500 matches and 4,000 nonmatches. Automatic Match is disabled on
both: Match precision is undefined and automatic-match recall is zero.

## Predetermined supplementary subsets

These remove any pair with either endpoint present in train or validation.
The filter was frozen before test scoring and uses IDs only. No official records
were changed. These are modified subsets, not official benchmark replacements.

| Subset | Retained | Actual matches / nonmatches | Excluded | Excluded matches / nonmatches |
| --- | ---: | --- | ---: | --- |
| Seen without development offers | 4,465 | 496 / 3,969 | 35 | 4 / 31 |
| Half-unseen without development offers | 2,836 | 325 / 2,511 | 1,664 | 175 / 1,489 |

| Subset | Review rate | Coverage | Different precision | Incorrect Different | Binary precision | Binary recall | Binary F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Seen without development offers | 34.51% | 65.49% | 97.30% | 79 | 31.83% | 69.96% | 43.76% |
| Half-unseen without development offers | 39.67% | 60.33% | 96.96% | 52 | 27.11% | 71.08% | 39.25% |

Automatic Match is disabled here too. Full confusion counts are in the JSON.
Filtering changes the population and does not establish general independence;
product clusters and test sets can still overlap.

## Execution and verification

```sh
python -m scripts.freeze_evaluation
python -m scripts.evaluate_frozen
```

The runner verifies the freeze before reading test records, checks predeclared
subset sizes, scores each official set once and derives supplementary results
from those scores. It never calls threshold selection on test labels. It refuses
to overwrite an existing output. The recorded real run used
`--output docs/day14-test-results.json`; rerunning evaluation is unnecessary for
this result and must not be treated as a fresh untouched test.

All **74 tests passed before the real run**, including five synthetic evaluation
tests for fixed decision boundaries, review denominators, undefined precision,
label-independent filtering, freeze-failure stopping and read-only split loading.
Post-run checks reconciled all six decision/label counts and binary confusion
counts for all five reported populations. The database, freeze record, fitted
model and runner hashes remained consistent. No source/model/threshold repair
was needed during evaluation.

## What the result permits us to claim

This is a measured local prototype with a reproducible frozen evaluation and
explicit generalization limitations. It does not establish production readiness,
calibrated confidence, human-review accuracy or cost savings. Pair/cluster
relationships mean ordinary independent-pair confidence intervals would be
misleading; we report descriptive counts and point estimates without significance
claims. Test sets are reported separately, never pooled.

The test results are now exposed. The historical freeze's
`test_performance_seen: false` records the state when it was created; the Day 14
report records `true`. Preserve that historical record. Further model development
must disclose this exposure and use new evaluation data for a fresh final claim.

Day 15 will store prediction versions and review records separately from the
frozen source database, so the evaluation input remains reproducible. The browser
is still the training-pair explorer. Learning follow-up: explain why 95.95%
Different precision can coexist with 109 missed genuine matches.
