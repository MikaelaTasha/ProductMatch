# Day 15: versioned predictions and review history

Implemented 2026-10-27. Run:

```sh
python -m scripts.store_predictions
```

The command verifies the frozen model/source, refits the selected model on
training data and stores predictions for the 2,500 training pairs. These are
in-sample workflow records, not new evaluation results. It does not rescore test
sets or change thresholds. The browser remains the original training explorer;
Day 16 will connect a review queue and saved corrections.

## Two databases

- `data/productmatch.sqlite3`: original, frozen benchmark source; read only.
- `data/predictions.sqlite3`: local workflow store; ignored by Git.

The command refuses the source database as its destination, including symlink
and hard-link aliases. It also rejects destinations with unrelated tables.
Original labels and listings stay in the source. Human judgments are separate
from benchmark labels and do not automatically become training data.

## Tables and keys

| Table | Key | Recorded evidence |
| --- | --- | --- |
| model_versions | model_id | Classifier version, complete freeze JSON, creation time |
| predictions | prediction_id | Model link, source database/split hashes, split/pair ID, input title/ID snapshot, ordered feature vector, score, frozen-policy decision, creation time |
| review_events | event_id | Prediction link, reviewer identifier, Match/Different/Review judgment, note, creation time |

`model_id` hashes canonical freeze JSON. It differs from the byte-level freeze
file hash; both identify the record using explicitly different serialization.
The feature names and thresholds are recoverable from that stored freeze.
`prediction_id` hashes model ID, source database hash, split and pair ID. A unique
constraint also protects that tuple. Changed input, feature, score or provenance
under the same identity is a conflict, not an overwrite.

Foreign keys connect prediction → model and review → prediction. Source references
are hashes and IDs across separate files, not cross-database foreign keys. The
CLI verifies the frozen source before writing; low-level storage APIs are for
trusted local callers and do not independently run the full model verifier.

All three tables are append-only through update/delete rejection triggers.
A revised human judgment creates a new event ID, retaining earlier judgments.
The caller reuses the same event ID when retrying one submission; an identical
retry adds nothing, while changed content with the same ID is rejected. This
supports Day 16's UI without overwriting evidence. Reviewer identifiers are
self-supplied local identifiers, not authenticated user accounts.

## Trace an individual prediction

For an existing prediction ID, the API
`productmatch.predictions.prediction_history(connection, prediction_id)` returns
its prediction, frozen model record and all review events in insertion order.
An unknown ID returns None. A SQL trace can use:

```sql
SELECT p.prediction_id, p.pair_id, p.score, p.decision,
       p.source_database_sha256, p.source_split_sha256,
       m.classifier_version, r.event_id, r.decision AS human_decision,
       r.reviewer, r.note, r.created_at AS reviewed_at
FROM predictions AS p
JOIN model_versions AS m ON m.model_id = p.model_id
LEFT JOIN review_events AS r ON r.prediction_id = p.prediction_id
WHERE p.prediction_id = ?;
```

A LEFT JOIN keeps unreviewed predictions visible. Review-history ordering and
a current-decision presentation will be handled explicitly in Day 16; a human
judgment does not replace `p.decision` or `p.score`.

## Verification

All **81 tests pass**, including seven storage tests covering idempotence,
source/input provenance, atomic rollback of a conflicting batch, multiple model
versions, review retries/history, foreign keys, append-only protection, invalid
scores/features and destination isolation.

The real run inserted 2,500 predictions; a second run inserted zero. There is one
model record and **zero real review events**. SQLite integrity and foreign-key
checks passed. The frozen source/model verification passed again after both
runs. Only aggregate counts are published in the
[storage summary](day15-storage-summary.json); title snapshots and feature values
remain in the ignored local database. Fictional review events exist only in
temporary tests, not the real store.

This provides local storage foundations, not deployed access control, a completed
review UI or proof of better matching. The Day 14 test limitations remain.
Independent learning exercise: explain why `prediction_id` is a foreign key in
`review_events`, and why a new human judgment should not erase the model score.
