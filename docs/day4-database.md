# Day 4: SQLite storage and repeatable import

Completed 2026-10-26. The database is local at `data/productmatch.sqlite3`
and is ignored by Git. It uses Python's built-in SQLite support; no additional
packages or database server are needed.

## Run

From the project root, with `.venv` activated:

```sh
python -m scripts.import_data
python -m scripts.import_data
```

If the data files are missing, first run `python scripts/wdc_data.py --download`.
The importer checks every selected file's hash and counts against our pinned
manifest before opening the database. It imports all five original splits.
Use `--db PATH` to create another local database or `--data-dir PATH` to read
the same verified files from another directory.

On a fresh database, the first import inserts 22,896 rows: 4,391 listings,
18,500 labeled pairs and five source records. The second imports zero new rows.

## Tables

| Table | One row represents | Unique key |
| --- | --- | --- |
| `listings` | An original product listing and its available attributes | `listing_id` |
| `dataset_splits` | An official split with filename, file/archive hashes and source URL | `split_name` |
| `labeled_pairs` | Two listing IDs, their original benchmark label and sampling flag in a split | `(split_name, pair_id)` |

Both listing IDs in a pair must reference existing listings. A shared listing
is stored once, including when it appears in several splits. A pair that appears
in more than one split retains each split membership. IDs and labels retain
their source meaning; no new train/test split is created.

Prices remain strings and missing values remain SQL NULL. An empty string is
preserved separately from NULL. Cluster IDs and hard-negative flags are retained
as benchmark metadata, not proposed model features. Original labels are kept
separate from the Day 3 human worksheet; that worksheet is not imported here.

This schema supports one pinned WDC snapshot per database. Use a new database
for a different dataset version. A rerun accepts identical records but raises
an error for changed listing content, pair labels, or source metadata. The whole
requested import is one transaction: a conflict rolls back new data rather than
partially importing it. Empty schema tables may remain after a failed first run.

## Read the data with SQL

On macOS, run:

```sh
sqlite3 -header -column data/productmatch.sqlite3 < sql/example_queries.sql
```

The file contains three queries: counts by split, five training pairs joined to
their left/right titles, and shared listing counts across splits. The training
query illustrates how two foreign keys connect one pair to two listing rows.
No test titles or model performance are displayed.

## Verification

- All 18,500 stored pairs were compared against source pair IDs, left/right IDs,
  labels and hard-negative flags.
- Importing twice left 4,391 listings, 18,500 pairs and five split records.
- SQLite integrity and foreign-key checks passed.
- All three example SQL queries executed successfully.
- Seven new synthetic-data tests cover repeat imports, split memberships,
  preserved values, joins, conflict rollback, invalid labels and constraints.
  Together with Day 2 checks, all 14 tests pass:

```sh
python -m unittest discover -s tests -v
```

The known official split overlaps remain present and unresolved. Storing test
pairs is not evaluating them. Do not treat the imported data as a single pooled
training set; always filter by split. No matcher, prediction storage or review
queue has been implemented. Day 5 will add a minimal pair-browsing interface.
