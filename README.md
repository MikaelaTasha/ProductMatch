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

## Current status: Day 1

The runnable starter prints the project purpose, planned decisions, and matching
definition. **It does not predict matches yet.** No dataset, trained model,
database, or graphical interface is included at this stage.

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

No third-party packages are needed yet. Later sessions will record dependencies
as they are introduced. To leave the environment, run `deactivate`. To run again
in a new terminal, activate `.venv` and run `python main.py`.

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

We plan to use a prepared [WDC Products benchmark](https://webdatacommons.org/largescaleproductcorpus/wdc-products/).
Day 2 will verify its source, terms, chosen variant, and file structure before
loading data. Raw datasets, generated databases, models, credentials, and the
local Python environment are excluded from Git.

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

- Day 1: repository, Python environment, runnable starter, and task definition.
- Days 2–5: dataset inspection, SQLite import, and pair browsing interface.
- Days 6–10: normalization, similarity baseline, attributes, and classifier.
- Days 11–14: review thresholds, error analysis, and frozen evaluation.
- Days 15–18: prediction history, human review, evidence, and automated checks.
- Days 19–20: fresh-install verification, demo, limitations, and release.

Each session records changes, rationale, checks, and uncertainty in
[the development log](docs/development-log.md).
