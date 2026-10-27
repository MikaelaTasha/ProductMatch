# Day 2 dataset record

## Selection and source

We chose WDC Products pair-wise matching, small development size, 50% corner
cases. This is our starting choice for manageable development with difficult
examples, not a result of model comparison.

- Publisher: Web Data Commons, University of Mannheim.
- [Benchmark page](https://webdatacommons.org/largescaleproductcorpus/wdc-products/)
- [Official archive](https://data.dws.informatik.uni-mannheim.de/largescaleproductcorpus/data/wdc-products/50pair.zip)
- Initial benchmark release: 2022-12-22; source offers were collected in 2020.
- Retrieved: 2026-10-25. No numbered archive version is advertised on the page.
- Our exact snapshot is identified by its SHA-256 in [dataset-manifest.json](dataset-manifest.json).

## Terms checked

The benchmark page offers public downloads but does not state an explicit
license for redistributing the dataset. The associated [code repository's
license](https://github.com/wbsg-uni-mannheim/wdcproducts/blob/main/LICENSE) is
BSD-3-Clause; we do not assume that it licenses third-party product content.
The downloaded archive contains nine data files and no license file.
Dataset redistribution terms remain unresolved. Our repository distributes
scripts, source links, hashes, and aggregate counts only. Keep raw data local;
confirm dataset terms before redistributing it. This is a record of what we
found, not a claim of unrestricted reuse.

## Run

From the project root, with the virtual environment activated:

```sh
python scripts/wdc_data.py --download
python scripts/wdc_data.py --examples 4
python -m scripts.check_wdc_splits
python -m unittest discover -s tests -v
```

The first command downloads approximately 22 MB, verifies the pinned archive
hash, and prepares five files. Reruns reuse the verified archive and restore any
changed selected files from it. A hash mismatch stops processing rather than
silently accepting a different release. Interrupted downloads use a temporary
`.part` file. The second command works offline and previews training data only.
No extra Python packages are needed.

## Local file structure and measured counts

All downloaded files are under `data/raw/wdc-products/` (ignored by Git).
The original `50pair.zip` is retained. Every selected filename starts with
`wdcproducts50cc50rnd`; the following table gives its remaining suffix.

| Split | Filename suffix | Pairs | Label 1 | Label 0 |
| --- | --- | ---: | ---: | ---: |
| Training | `000un_train_small.json.gz` | 2,500 | 500 | 2,000 |
| Validation | `000un_valid_small.json.gz` | 2,500 | 500 | 2,000 |
| Seen test | `000un_gs.json.gz` | 4,500 | 500 | 4,000 |
| Half-unseen test | `050un_gs.json.gz` | 4,500 | 500 | 4,000 |
| Unseen test | `100un_gs.json.gz` | 4,500 | 500 | 4,000 |

These counts were measured locally, not model results. Each selected file has
1,000 distinct offer IDs. The archive also has medium/large training and
validation files, which our script does not extract.

## How to read a pair

Each gzip-compressed file contains one JSON object per line. Observed fields:

| Fields | Meaning in this project |
| --- | --- |
| `id_left`, `id_right` | Listing identifiers |
| `title_left`, `title_right` | Original titles to compare |
| `brand_*`, `description_*`, `price_*`, `priceCurrency_*` | Listing attributes; preserve missing values |
| `cluster_id_left`, `cluster_id_right` | Benchmark product groups; never use as prediction features |
| `pair_id` | Listing IDs joined with `#` |
| `label` | Benchmark answer: 1 = match, 0 = non-match |
| `is_hard_negative` | Benchmark sampling metadata; never use as a prediction feature |

Prices are strings; some attributes are JSON `null`. No dedicated size, model,
or pack-quantity fields were found in the observed schema. Later extraction must
work from available text. The loader preserves original values and labels.

The benchmark's labels come from product-identifier clustering. Their alignment
with our stricter size/model/quantity definition needs manual inspection.
There is no benchmark `Review` label: that will be our application's uncertainty
policy. Printed labels are supplied answers, not predictions.

## Split audit: unresolved overlap

The publisher describes separation of offers across development and test sets.
Our audit of this exact download found the following shared offer IDs:

| Comparison | Shared IDs |
| --- | ---: |
| Train / validation | 0 |
| Train / seen test | 0 |
| Train / half-unseen test | 110 |
| Train / unseen test | 0 |
| Validation / seen test | 4 |
| Validation / half-unseen test | 106 |
| Validation / unseen test | 0 |

The audit combines left and right IDs within each split. It checks file hashes,
counts, and ID intersections; it does not inspect test titles to guide model
choices or compute performance. Reproduce it with `python -m scripts.check_wdc_splits`.

We have preserved the official files and have not silently removed overlaps or
created new splits. Investigate the discrepancy before Days 13–14 and before
claiming leakage-free seen/half-unseen evaluation. Training and validation have
no shared IDs in this snapshot, so Day 3 training-pair inspection can proceed.
Product-level and pair-level leakage have not been fully audited.


## Day 12 follow-up — 2026-10-27

The [expanded audit](day12-audit.md) confirms shared product clusters across
train/validation and exact repeated pairs in half-unseen test (20 with training,
23 with validation). The unseen test shares no measured offer, cluster or pair
IDs with development data. Evaluation options are documented; the source of
the official overlaps is still unverified. All pinned raw-file hashes/counts
were rechecked. No test predictions or test performance were computed.
