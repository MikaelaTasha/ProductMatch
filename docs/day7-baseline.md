# Day 7: title similarity baseline

Implementation and validation run completed 2026-10-26. The user correctly
identified that similar titles can describe different sizes or series. Numerical
cosine and metrics explanation exercises remain pending.

## Run

With the virtual environment active and the database imported:

```sh
python -m pip install -r requirements.txt
python -m scripts.run_baseline
python -m unittest discover -s tests -v
```

The default report is `artifacts/day7-baseline.json` (local, Git-ignored).
The measured aggregate snapshot is [day7-baseline-results.json](day7-baseline-results.json).
Neither report contains listing text. A rerun rebuilds TF-IDF from training data
and reselects the validation threshold. It overwrites the specified report;
use `--output PATH` to keep another result. No fitted model is saved yet.

## Method and boundaries

1. Read only `train` and `validation` from SQLite. Reject shared listing IDs
   between those two splits and mismatched source archive metadata.
2. Apply Day 6 normalization to original titles in memory. Fit TF-IDF on each
   unique training listing exactly once, so repeated pair appearances do not
   distort document frequencies. Labels, IDs, cluster IDs and sampling flags
   are not text features.
3. Transform validation titles using the already learned vocabulary and weights.
   Validation-only terms are ignored; there is no refitting on validation data.
4. Compute cosine for each supplied pair using a sparse row-wise dot product.
5. Choose a threshold using validation labels only. Return Match when the score
   is greater than or equal to the threshold, otherwise Different.

TF-IDF weights depend on term frequency and document frequency. With the
scikit-learn settings used here, smoothed IDF is `log((1+n)/(1+df)) + 1`.
Vectors are L2-normalized, so their dot product is cosine similarity.
See the [scikit-learn TF-IDF documentation](https://scikit-learn.org/1.7/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html).

The fixed token rule keeps single-digit tokens and internal periods, hyphens
and slashes in codes such as `pg-545`, `hx432c16fb3/16`, and `3.7ghz`. It does
not preserve all possible punctuation structures. This is tokenization of a
derived representation; original and Day 6 normalized strings remain intact.
No tokenization alternatives were tuned on validation results in this session.

Missing titles become empty text for vectorization. Empty or entirely unknown
titles have zero vectors, and their cosine score is zero, including two empty
titles. This is an acknowledged weakness of a binary baseline; a later Review
policy should handle insufficient evidence explicitly. There were zero such
validation listings in this run. No external language model or API is used.

## Threshold selection

The predeclared baseline objective is the highest match-class **F1** on
validation data. Search every distinct observed score and one reject-all
threshold; tied F1 results prefer higher precision, then the higher threshold.
Identical scores receive the same decision. Report precision as zero when no
matches are predicted, and recall as zero when there are no true matches;
threshold selection requires both classes.

This objective balances precision and recall; it does not establish a safe
automatic-merge policy. The two-threshold Review policy is still planned for
Day 11. Cosine scores are similarities, not calibrated match probabilities.

## Measured validation results

TF-IDF used 1,000 unique training listings and learned 2,693 tokens. Validation
contains 2,500 pairs: 500 matches and 2,000 non-matches. Train/validation listing
ID overlap is zero. The selected threshold is **0.24657051110717756**.

| Measure | Result |
| --- | ---: |
| Correct predicted matches (TP) | 440 |
| Incorrect predicted matches (FP) | 672 |
| Missed matches (FN) | 60 |
| Correct non-matches (TN) | 1,328 |
| Match precision: TP / (TP + FP) | 39.57% |
| Match recall: TP / (TP + FN) | 88.00% |
| Match F1: 2TP / (2TP + FP + FN) | 54.59% |
| Accuracy | 70.72% |
| Review rate | 0% |
| Automatic-decision coverage | 100% |

The baseline calls 1,112 pairs matches, but 672 of those decisions are wrong
against benchmark labels. It is unsuitable for reliable automatic merging.
Always predicting Different would give 80% accuracy but zero match recall,
illustrating why accuracy alone is misleading here.

These are **threshold-selection-set results**, not an unbiased held-out estimate.
The official test splits were not read by this workflow. Their known overlap
issue remains unresolved and must be addressed or qualified before Day 14.
Benchmark identity ambiguities from Day 3 also remain. Results are against the
supplied labels, not independently verified product identities.

The pair explorer still shows original listings and benchmark labels only;
baseline predictions have not been integrated into the UI or database.

## Verification

All 33 tests passed. Eight new tests check vocabulary/IDF isolation, sparse
cosine versus a reference implementation, token distinctions, confusion counts,
threshold equality/ties, bad inputs, overlap rejection and a run with no test
split present. Repeating the real run reproduced the report exactly on this
environment, and the database file hash was unchanged. Runtime versions and
imported-source hashes are recorded in the result snapshot. The report carries
source metadata from the database; it does not rehash raw dataset files.

## Learning checkpoint

For simple vectors `A=(1,1,0)` and `B=(1,0,1)`, compute the dot product and
divide by their lengths to obtain cosine similarity. These are teaching vectors,
not this dataset's fitted TF-IDF values. Also explain why 440 correct matches
out of 1,112 predicted matches is precision, while 440 out of 500 actual matches
is recall. Neither exercise is recorded as completed yet.

Next: Day 8, extract supported attributes to distinguish similar product variants.
