# Day 10: learn from similarity and product details

Implemented 2026-10-27. After installing requirements and importing the database:

```sh
python -m scripts.train_classifier
```

The command fits a logistic regression classifier locally and writes an aggregate
report to `artifacts/day10-classifier.json`. The browser is unchanged; it still
shows listings and benchmark labels. No fitted model is saved for inference.

## How it works

1. Fit the existing TF-IDF vocabulary and word weights on 1,000 unique training titles.
2. For each of the 2,500 training pairs, build 71 numeric inputs: title cosine
   similarity plus the 70 Day 9 attribute-state indicators.
3. Fit logistic regression using the training pairs' original benchmark labels.
4. Transform validation pairs with the already fitted vocabulary and classifier.
5. Choose a threshold on validation scores by maximum match-class F1, breaking
   ties by higher precision then higher threshold, as in Day 7.

Logistic regression learns weights for the inputs. It calculates a weighted
sum plus an intercept and maps that sum to a score between 0 and 1 with
`1 / (1 + exp(-sum))`. The score is a model estimate, not a verified probability
or a guarantee. Calibration has not been evaluated.

The configuration is fixed: L2 regularization, C=1, lbfgs solver, tolerance
0.0001, maximum 1,000 iterations, random_state=0, no class weighting or resampling.
No additional scaling is applied: cosine is in [0,1] and indicators are 0/1.
The observed fit converged in 100 iterations. A convergence warning aborts the
run rather than silently publishing an unfinished fit. This is one prescribed
configuration, not a hyperparameter search.

Training has 500 matches and 2,000 nonmatches. An always-Different classifier
would get 80% accuracy while finding no matches, so precision, recall and F1
matter more than accuracy alone.

## Validation comparison

Both thresholds below are selected on the same 2,500 validation pairs. These
are development results, not held-out test performance.

| Measure | Day 7 title baseline | Day 10 classifier |
| --- | ---: | ---: |
| Precision | 39.57% | 51.49% |
| Recall | 88.00% | 72.60% |
| F1 | 54.59% | 60.25% |
| Correct matches | 440 | 363 |
| Incorrect matches | 672 | 342 |
| Missed matches | 60 | 137 |
| Correct nonmatches | 1,328 | 1,658 |
| Threshold | 0.246571 cosine | 0.288946 model score |

False matches fell by 330, but missed matches rose by 77. The classifier's F1
improved; it is still unsuitable for reliable automatic merging at this
threshold. Score scales differ, so the two threshold numbers are not directly
comparable. No ablation was run: this comparison does not isolate how much of
the change came from the attributes versus the supervised classifier.

At the classifier's conventional 0.5 threshold, precision is 64.15%, recall
47.60%, F1 54.65%, false matches 133 and missed matches 262. This illustrates
the precision/recall trade-off, not a recommended production threshold.

The [full aggregate report](day10-classifier-results.json) records coefficients,
intercept, feature order, versions, configuration, dataset provenance and metrics.
Correlated indicators make individual coefficient interpretation unreliable;
weights are not causal explanations. Attributes absent from training provide
no learned evidence. Unsupported or mistaken extraction still affects features.

## Boundaries and verification

Only training labels fit the classifier. Labels, IDs, cluster IDs and split
names are not numeric inputs. The runner rejects shared training/validation
listing IDs and mismatched source archives. This check does not prove product
clusters are independent; the broader official split audit remains pending.

Validation selects the threshold, and repeated development on that set can
make the reported performance optimistic. No test set was read. The existing
test-split overlap issue remains unresolved. Review decisions and hard product
identity rules are not implemented: the classifier can still predict Match
when extracted quantities differ.

All 55 tests pass, including six classifier tests for matrix/probability
alignment, validation-label independence, vocabulary preservation, symmetric
scores, repeatability, class validation and split/source guards. The complete
real-data report reproduced exactly, the database hash stayed unchanged and
the rerun baseline matched the saved Day 7 metrics.

## Learning follow-up and next step

Independent probability/class-imbalance explanations remain pending. Practice:
explain why fewer incorrect matches can come with more missed matches.

Day 11 will introduce two decision thresholds and a Review region, reporting
precision/recall together with review rate and automatic-decision coverage.
