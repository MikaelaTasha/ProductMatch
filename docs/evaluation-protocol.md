# Frozen evaluation protocol v1

Fixed on Day 13, before test predictions or performance are computed.

## Pipeline and selection

Compare exactly two configurations: unchanged Day 10 logistic regression and
one candidate adding five punctuation-insensitive model-code evidence indicators.
Retain the candidate only for strictly higher validation-selected binary F1;
ties retain Day 10. Keep regularization, training data and other features fixed.
This is a development selection rule, not a significance test.

The selected version, ordered features, binary threshold, two review thresholds,
precision target, support floor, model fingerprint and source/runtime hashes
are recorded in `evaluation-freeze.json`. TF-IDF fits unique training titles;
logistic regression fits training pairs and labels. Do not refit on validation.
Do not change a threshold or model based on test outcomes.

The primary decision policy is the frozen 95%-target, minimum-20-support Review
policy. Its Match channel is disabled in this freeze. Also report the frozen
binary-threshold result as a separately identified diagnostic. Never substitute
a more favorable policy after seeing test results.

## Test sets and overlap

Primary: official `test_unseen` (4,500 pairs). The Day 12 audit found no shared
development offer/cluster/pair IDs. This is unseen according to supplied cluster
metadata, not a guarantee against all semantic leakage.

Secondary: official `test_seen` and `test_half_unseen`, each separately labeled
as containing development-offer overlap. Half-unseen also contains exact repeated
development pairs. Keep original files and benchmark labels.

For each secondary set also report a predetermined supplementary subset removing
every pair with either offer ID in the union of train and validation IDs. Expected
sizes are 4,465 seen and 2,836 half-unseen. Do not select subsets using labels,
scores or error inspection. Report retained/excluded counts and label balance.
These subsets are not unchanged official benchmarks.

Do not pool the three test sets: they contain overlapping offers and pairs.
Cluster/offer dependence also prevents treating every pair as an independent
trial for an ordinary binomial confidence interval.

## Required outputs and interpretation

For every set/subset report:

- Pair count, actual match/nonmatch counts and overlap qualifications.
- All six review-policy decision/label counts, automatic Match precision,
  automatic Different precision, automatic-match recall, review rate and coverage.
- The fixed binary threshold's confusion matrix, precision, recall, F1 and accuracy.
- Undefined precision as null when no automatic decisions of that class occur.

Review cases are not correct predictions or completed human decisions. Recall
uses all true matches, including those sent to Review. Report point estimates
with counts and dependence limitations; no statistical-significance or calibrated-
confidence claim. The 95% validation target is not a promised test precision.

## Verification and stop conditions

Before scoring, run `python -m scripts.freeze_evaluation`. It verifies frozen
source/configuration files, exact numerical package versions, the local database
snapshot and the five raw-file hashes, then refits on training only and checks
the vocabulary/IDF/weights fingerprint. Frozen thresholds must equal the selected
experiment's values. Any mismatch stops scoring; investigate without silently
regenerating the freeze. The exact database hash intentionally binds this local
snapshot and may reject a logically equivalent re-import or a database modified
later with new tables. Such a mismatch requires an explicit provenance review.

The verifier returns the fitted model for a future evaluation runner. It does
not score test pairs. Source hashes are a reproducibility guard, not a security
signature. The freeze itself is preserved in Git. Do not overwrite it to hide
a change after test inspection. If evaluation code fails, fix the execution bug
without changing model/selection rules and document the repair.

Day 14 will execute this protocol once after the verification checks. Inspecting
test results ends their role as an untouched final evaluation; further development
must acknowledge that exposure and use new data for fresh generalization claims.
