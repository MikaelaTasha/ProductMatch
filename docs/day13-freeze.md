# Day 13: one improvement, then freeze

Completed 2026-10-27. We tested one candidate motivated by Day 12's validation
examples: add a punctuation-insensitive comparison of extracted model codes.
The rule was stated before running it: retain only if validation-selected binary
F1 strictly improves; otherwise keep Day 10. Report the review-policy trade-off
separately. No test data was scored to make this decision.

## What changed

`logistic-title-attributes-code-alias-v1` adds five indicators to the original
71 inputs, for 76 total. An example such as `ATHM40X` versus `ATH-M40X` can now
produce agreeing auxiliary code evidence. Digits are preserved. Only hyphens,
slashes and dots inside existing candidate tokens are removed for this extra
comparison; original titles, candidates and all old feature columns remain.

Missing evidence stays missing. If either title has multiple original candidates,
ambiguity remains even when their aliases collapse to the same string. We do
not join split tokens, reinterpret Gb as GB or add product-variant rules.
A canonical alias can collide across different products, so it is soft evidence,
not a hard Match rule. Regularization and training data are unchanged.

## Measured result

| Validation metric | Day 10 | Candidate retained |
| --- | ---: | ---: |
| Binary precision | 51.49% | 51.70% |
| Binary recall | 72.60% | 72.80% |
| Binary F1 | 60.25% | 60.47% |
| False matches | 342 | 340 |
| Missed matches | 137 | 136 |
| Review rate at 95% target | 36.68% | 36.32% |
| Automatic coverage | 63.32% | 63.68% |
| Incorrect automatic Different | 79 | 79 |

The candidate passes the predeclared selection rule, but this small gain is not
proof of statistical significance or future performance. Validation has been
used repeatedly for development. The full [experiment report](day13-experiment-results.json)
includes both models and exact thresholds.

The frozen review policy still has zero automatic Matches and undefined Match
precision. It sends 908 validation pairs to Review and marks 1,592 Different,
including 79 actual matches. We have not solved reliable automatic matching.

## Frozen deliverables

- [Evaluation protocol](evaluation-protocol.md): primary unseen evaluation,
  separately qualified official secondary sets, and fixed supplementary filters.
- [Freeze record](evaluation-freeze.json): selected version, 76-feature order,
  thresholds, runtime, code/data hashes and trained-model fingerprint.
- Verifier: `python -m scripts.freeze_evaluation`.

The freeze is created once with `python -m scripts.freeze_evaluation --create`;
creation refuses to overwrite an existing record. Normal reruns verify it.
The selected model can be reproduced by fitting on training data and checking
its fingerprint. No executable model artifact or raw vocabulary is published.

For research reproduction, `python -m scripts.select_day13` reruns the fixed
comparison into local artifacts; it does not replace the frozen experiment.
Do not keep modifying this model after looking at test results and still call
those tests untouched.

## Checks and remaining work

All 69 tests pass. Five new tests check alias ambiguity/digits, preservation of
original feature columns, symmetry/label independence, strict selection behavior,
fingerprint sensitivity and rejection of changed code/runtime. The experiment
reproduced exactly during freeze creation; creation and standalone verification
both reproduced the fitted-model fingerprint and validated the frozen inputs.
A modified threshold in an in-memory copy was rejected. No test predictions or
performance computed, and no browser changes made.

Day 14 will run the frozen evaluation protocol. Independent learning exercise:
explain why freezing the thresholds before viewing test results matters.
