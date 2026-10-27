# Day 11: send uncertain pairs to Review

Implemented 2026-10-27. Run:

```sh
python -m scripts.evaluate_review
```

The command refits the unchanged Day 10 classifier on training data and selects
two thresholds using validation data. It writes aggregate results locally to
`artifacts/day11-review.json`. The browser and database remain unchanged; this
is a command-line policy evaluation, not a working review queue or saved model.

## Decisions and selection

- Score below the lower threshold: Different.
- Score at or above the upper threshold: Match.
- Everything in between: Review.

Equal thresholds give a binary policy. Score ties stay together. A threshold
just above 1 disables Match; a lower threshold of zero disables Different.
These endpoints also allow all pairs to go to Review.

The provisional default requires at least 95% empirical precision and at least
20 validation decisions for each enabled automatic class. Different precision
means correct nonmatches divided by all automatic Different decisions (negative
predictive value). Match precision means correct matches divided by all
automatic Match decisions. These learning defaults are not business requirements
or statistical confidence guarantees; 20 examples is a small support floor.

Search all observed score boundaries and maximize automatic-decision coverage
subject to those constraints. Ties favor fewer automatic errors, then more
correct automatic Matches, then a higher upper and lower lower threshold.
If a class cannot qualify, it stays disabled. We also report fixed 90% and 99%
target scenarios instead of selecting a target after seeing results.

## What happened on validation

The classifier cannot reach even the 90% Match-precision target with 20 or more
automatic Matches. Consequently all three scenarios disable automatic Match.
Zero false merges in this situation is not successful matching: automatic-match
recall is zero and Match precision is undefined (JSON null).

| Target for each enabled class | Review | Automatic coverage | Automatic Different | Incorrect Different |
| --- | ---: | ---: | ---: | ---: |
| 90% | 21.88% | 78.12% | 1,953 | 195 |
| 95% (default) | 36.68% | 63.32% | 1,583 | 79 |
| 99% | 74.32% | 25.68% | 642 | 6 |

At the default lower threshold of approximately 0.192541, 1,504 nonmatches
and 79 real matches are automatically marked Different. Its Different precision
is 95.01%. The remaining 917 pairs go to Review: 421 matches and 496 nonmatches,
according to benchmark labels. These are routed cases, not completed human
reviews. We do not assume reviewers resolve them perfectly.

The Day 10 binary reference has 342 false matches and 137 false Different
decisions, with no review. Day 11 disables automatic matching to meet its target;
it does not improve the underlying classifier. Review workload and missed
matches must remain visible alongside precision.

See the [aggregate report](day11-review-results.json) for exact thresholds,
counts, provenance and the reproduced Day 10 reference.

## Metric definitions and limits

Automatic-match recall = correct automatic Matches / all actual matches,
including actual matches sent to Review. Review is not counted as a correct
prediction or silently removed from this denominator.

Review rate = Review cases / all pairs. Automatic-decision coverage =
(Match + Different cases) / all pairs. These sum to one. Undefined precision
is null rather than zero or 100%. All six decision/label counts partition the
validation set: correct/incorrect Match, correct/incorrect Different, and
Review with either label.

The targets are measured on the same validation set used for selection, so
results are optimistic development estimates. Scores are not calibrated
confidence. No held-out test sets were read, no latency/cost savings measured,
and no review outcomes collected. Existing split-overlap and extraction issues
remain unresolved. Day 12 will investigate errors and split provenance before
model freezing and test evaluation.

All 61 tests pass. New tests check boundary equality, ties, all-Review behavior,
undefined metrics, invalid inputs, read-only training/validation execution and
search parity with an exhaustive reference on small synthetic datasets. The
real report repeats exactly, preserves the database hash and reproduces Day 10.

Learning exercise: explain why zero false automatic Matches is not enough to
claim success when automatic Match is disabled. Independent explanation remains
pending; implementation completion does not establish mastery.
