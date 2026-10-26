# ProductMatch

Product matching with human review.

## User and problem

ProductMatch is a learning prototype for a catalog reviewer who needs to decide
whether two sellers' listings describe the same product. Titles can differ,
attributes can be missing, and similar-looking products can have different models,
sizes, or pack quantities. Incorrectly merging products can mislead a catalog's
users.

The planned application compares **two supplied listings** and returns **Match**,
**Different**, or **Review**, with supporting evidence. It will store predictions
and human corrections so decisions can be inspected later.

## What counts as the same product?

- Size, model, and pack quantity must agree when known for both listings.
- Different sellers and prices are allowed.
- Missing attributes do not automatically make products different.
- A match requires supporting evidence; absence of a known conflict is not enough.
- Insufficient evidence should lead to human review.

For example, the same model in a one-pack and a two-pack is different under our
definition. Two offers for the same model, size, and pack quantity can match even
when their sellers or prices differ. A missing pack quantity is uncertainty,
not proof of a mismatch.

This is our intended task definition. We still need to inspect how the benchmark's
labels relate to it; we will document discrepancies rather than silently relabel
the benchmark.

## Current status: Day 6

The starter prints the project scope. A dataset tool now downloads and loads
the prepared WDC small training split and prints labeled product pairs.
SQLite now stores listings and original labeled pairs with repeatable imports.
The Streamlit interface now lets you browse training pairs, search titles or
pair IDs, and reveal the benchmark answer. **It does not predict matches yet.**

We have reviewed 30 training pairs and documented [matching evidence, difficult
cases, and unresolved questions](docs/day3-findings.md). See the
[database guide](docs/day4-database.md) for the schema and SQL examples.
See the [interface guide](docs/day5-interface.md) for browsing instructions.
Conservative [title normalization](docs/day6-normalization.md) now lowercases
letters and standardizes whitespace while retaining digits and punctuation.
Original titles stay unchanged. Next is TF-IDF and cosine similarity (Day 7).

## Run locally

Prerequisite: Python 3.10 or newer. Day 1 was checked with Python 3.10.1 on macOS.

From the project directory on macOS or Linux:

```sh
python3 -m venv .venv
source .venv/bin/activate
python main.py
```

Expected output begins with:

```text
ProductMatch — Product Matching with Human Review
Day 1: project setup is working.
```

To download the Day 2 data and preview training pairs:

```sh
python scripts/wdc_data.py --download
```

To preview again offline, run `python scripts/wdc_data.py`.
To create or update the local SQLite database, run:

```sh
python -m scripts.import_data
```

Rerunning the import does not duplicate listings or labeled pairs.
To compare original and normalized training titles, run
`python -m scripts.preview_normalization --examples 5`.
See the [dataset record](docs/dataset.md) for source, terms, file structure,
checks, and an unresolved overlap found in the official test splits.

To launch the graphical interface after importing the database:

```sh
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open http://127.0.0.1:8501. Stop the server with Control+C.
The data scripts and text starter use only Python's standard library; the
interface requires Streamlit. To leave the environment, run `deactivate`.
In a new terminal, activate `.venv` before running these commands.

## Planned approach

| Component | Planned choice |
| --- | --- |
| Language | Python |
| Storage | SQLite |
| Baseline | TF-IDF and cosine similarity |
| Classifier | Logistic regression on pair-comparison features |
| Interface | Streamlit |
| Checks | pytest and GitHub Actions |
| Version control | Git and GitHub |

The initial scope is matching supplied pairs. Marketplace-wide candidate
generation, scraping, embeddings, and production deployment are future work.

We use a prepared [WDC Products benchmark](https://webdatacommons.org/largescaleproductcorpus/wdc-products/)
with small development sets and 50% corner cases. Raw datasets, generated
databases, models, credentials, and the local Python environment are excluded
from Git.

## Evaluation plan

Our main question is: **How many incorrect automatic matches can we avoid, and
how much human review does that require?**

We will report automatic-match precision, match recall, review rate,
automatic-decision coverage, and performance on unseen products together.
Sending every pair to review is not a useful matching system.

Preserve the official training, validation, and test splits. Fit models on
training data, select thresholds on validation data, and use held-out tests only
after freezing the model and thresholds.

## Milestones

The [data-engineering learning roadmap](docs/learning-roadmap.md) expands the
original 20-session prototype plan to 36 sessions, adding Spark, a lakehouse
table format, one cloud platform, a BI dashboard and operational practice.
These extensions are planned, not implemented. From Day 6, sessions also include
small independent Python/SQL tasks and mathematics/English explanations.

- Day 1: repository, Python environment, runnable starter, and task definition.
- Days 2–5: dataset inspection, SQLite import, and pair browsing interface.
- Days 6–10: normalization, similarity baseline, attributes, and classifier.
- Days 11–14: review thresholds, error analysis, and frozen evaluation.
- Days 15–18: prediction history, human review, evidence, and automated checks.
- Days 19–20: fresh-install verification, demo, limitations, and release.
- Days 21–30: data contracts, Parquet, Spark, lakehouse storage, cloud and operations.
- Days 31–36: SQL reporting, BI dashboard, reviewer feedback and English portfolio demo.

Each session records changes, rationale, checks, and uncertainty in
[the development log](docs/development-log.md).
