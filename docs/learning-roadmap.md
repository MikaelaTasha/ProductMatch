# ProductMatch learning roadmap: data engineering

Updated 2026-10-27, after Day 13 implementation.

## Source and purpose

This roadmap develops practical data-engineering skills through product matching,
from a local prototype to reproducible pipelines, cloud practice and reporting.
Planned work is distinguished from verified implementation and independent study.

The original 20-session plan covered a local matching prototype. The extension
below adds explicit data-engineering, cloud, lakehouse and BI deliverables.
Days 1–5 are completed. Days 6–13 now have verified implementations; outstanding
learning exercises are recorded in their notes. Days 14 onward remain planned.
Days are work sessions, not consecutive calendar days. Budget roughly 45–90
minutes per session, splitting complex tasks across extra sessions as needed.

The learning goal is to build, debug and explain a product-data pipeline that
helps a catalog reviewer make reliable matching decisions.

## Requirements and evidence

| Learning area | Planned evidence | Current status |
| --- | --- | --- |
| Python and SQL | Ingestion, transformations, joins, reporting, window functions | Basic ingestion/SQL implemented; independent practice ongoing |
| Data cleansing and integration; ETL/ELT | Versioned transformations, data checks, repeatable end-to-end workflow | Import foundations implemented; full workflow planned |
| Linear algebra, probability and statistics | Explain vectors/cosine, sampling, imbalance, evaluation and uncertainty | Planned alongside model work |
| Predictive modeling and project experience | Baseline, classifier, frozen evaluation, error analysis | Planned Days 7–14 |
| Lakehouses and platform design | Parquet plus a transactional table format, schema enforcement and versioned reads | Planned Days 21–25; directories alone do not count |
| Large-scale processing, e.g. Spark/Hadoop | PySpark transformations with parity checks and measured runtime/resource use | Planned Days 23–24; small local runs are not production-scale experience |
| Cloud development, e.g. GCP/AWS/Azure | One deployed batch pipeline with storage, permissions, logs and cost records | Planned Days 26–30; provider not selected |
| Visualization, e.g. Tableau/Power BI | A BI dashboard connected to documented reporting outputs | Planned Days 31–33; Streamlit alone does not demonstrate these tools |
| Business issues and decision support | Explain false merges versus review workload using measured results | Problem defined; metrics and feedback planned |
| Platform operation | Scheduling, retries, safe reruns, failure recovery and runbook | Planned Days 28–30 |
| Collaboration | Feedback from a consenting reviewer, documented requirements and response | Planned Day 34; proxy feedback is not actual business-unit experience |
| Business-level English | Explain architecture, trade-offs, results and limitations aloud | Practice every session; final demo Day 36 |
| Coding test | Independent timed Python/SQL exercises and correction log | Parallel track; project code alone is insufficient |
| Degree or equivalent knowledge | User's education and separate foundational study | A project cannot substitute for or certify eligibility |

Use **Spark**, **one cloud platform**, and **one of Tableau/Power BI** where they
serve a concrete purpose. The plan does not require installing all competing tools. Hadoop concepts can be studied alongside Spark;
a separate Hadoop cluster is not currently planned. Select the cloud and BI tool
after checking current account access, budget, operating-system support and terms.
No cloud resources, paid plans or public dashboards are authorized by this document.

## Sessions 1–20: local foundation and evaluated prototype

| Day | Build/study task | Evidence of completion |
| --- | --- | --- |
| 1–5 | Repository, data provenance, manual inspection, SQLite import, pair explorer | Already completed; see development log |
| 6 | Normalize titles as a transformation; keep original text separate | Versioned function, identity-preserving examples, idempotence tests; user explains string operations |
| 7 | TF-IDF/cosine baseline; study vectors and dot products | Training-fitted vocabulary, validation results; user calculates a small cosine example |
| 8 | Extract supported model/size/quantity attributes and missingness | Inspection-backed extraction examples; user writes one extraction rule |
| 9 | Build documented pair features and SQL data-quality summaries | Feature dictionary, missingness/conflict counts; user writes a join and aggregation |
| 10 | Train logistic regression; compare with baseline | Reproducible validation comparison; explain probabilities and class imbalance |
| 11 | Add Match/Different/Review thresholds | Validation precision, recall, review rate and coverage; explain cost trade-offs without invented savings |
| 12 | Inspect validation errors and investigate the known split overlaps | Error taxonomy and split audit; document evaluation options without tuning on test performance |
| 13 | Make one justified improvement; finalize evaluation protocol and freeze model/thresholds | Written rationale and versioned configuration; unresolved overlap must not be called leakage-free |
| 14 | Run frozen held-out evaluation under the documented protocol | Separate results by test setting, explicit overlap caveats, uncertainty and limitations |
| 15 | Store predictions, model versions and review records | Trace a prediction to its source/model; user explains schema and keys |
| 16 | Add review queue and saved corrections | Review action can be retrieved; original labels remain unchanged |
| 17 | Present matching evidence and business-oriented summaries | Explain a decision using attributes and missingness |
| 18 | Assemble local pipeline command and automate checks with GitHub Actions | Ingest-to-report workflow, meaningful failure checks, passing CI; run existing unittest tests directly |
| 19 | Test fresh checkout and document setup | Reproduction instructions, dependency decisions and troubleshooting |
| 20 | Release local v0.1 and explain its limits | Demo, results, architecture and next steps; no cloud/scale claims yet |

## Sessions 21–36: data-engineering extension

| Day | Build/study task | Evidence of completion |
| --- | --- | --- |
| 21 | Define raw, cleaned and curated data contracts | Schemas, keys, provenance, quality rules and ownership of each transformation |
| 22 | Add columnar Parquet outputs preserving source and split information | Repeatable export, round-trip checks and comparison with JSON/SQLite |
| 23 | Implement selected transformations in PySpark | Outputs agree with the reference Python implementation; explain DataFrames, joins and lazy execution |
| 24 | Benchmark Spark at several measured input sizes | Runtime/resources, partition choices and bottlenecks; clearly label synthetic/duplicated scale data and keep it outside ML evaluation |
| 25 | Add a transactional lakehouse table format (candidate: Delta Lake) | Demonstrate schema enforcement, a controlled update and an earlier-version read; check compatibility before selecting packages |
| 26 | Select one cloud and design the small deployment | Architecture, permissions, cost estimate, cleanup plan; confirm account/budget and data-upload rights before provisioning |
| 27 | Add cloud object storage and transfer approved data | Verified round trip and documented access boundaries; use synthetic data if benchmark upload rights remain unclear |
| 28 | Execute a small batch pipeline in the cloud | Successful run, quality checks and observable logs; document actual runtime environment |
| 29 | Add a schedule/orchestrator and run metadata | Demonstrate execution order, retry behavior and safe reruns; introduce a tool only if it supports the chosen deployment |
| 30 | Exercise operational failures and recovery | Failed-input test, recovery runbook, cost review and resource cleanup |
| 31 | Create SQL reporting tables/views | CTE/window-function exercises and defined denominators for quality, matching and review metrics |
| 32 | Choose and connect Tableau or Power BI | A working report from permitted aggregate outputs; verify access and supported workflow first |
| 33 | Build and validate the BI dashboard | Data quality, precision/recall, review rate, coverage and unseen-product results reconciled with source reports |
| 34 | Gather reviewer feedback and respond | Consented feedback, requested change and documented trade-off; identify simulated/proxy feedback honestly |
| 35 | Reproduce and review the extended architecture | Setup/run/cleanup guide, dependency and permission review, scale limits and reproducibility checks |
| 36 | Prepare the portfolio and English interview demo | Explain the pipeline, model, SQL, dashboard, operational failure and limitations; show only measured accomplishments |

## Learning routine from Day 6

Each build session follows: **explain → user tries a small task → review together
→ implement and verify → user explains the result**. Do not mark understanding
complete merely because generated code runs. Keep the task small enough that
the user can attempt it without writing an entire feature alone.

Alongside project work, alternate 15–20 minute practice blocks:

- Python coding: strings, dictionaries, sets, sorting, then common data
  structures/algorithms and time/space complexity. Attempt unfamiliar problems
  before viewing solutions.
- SQL: joins and aggregation, then CTEs, window functions and query reasoning.
- Mathematics/statistics: vectors, dot products, probability, sampling,
  conditional probability, class imbalance, metrics and uncertainty.
- English: a 60–90 second explanation of the problem, choice, evidence and
  limitation; receive feedback on clarity and technical accuracy.

Record attempts, mistakes and what can be explained independently. Do not
invent solved exercises or fluency assessments. Scheduling these blocks is a
study plan, not an automation or reminder setup.

## Guardrails for honest portfolio evidence

Keep original benchmark labels and held-out data boundaries. Resolve or clearly
qualify the existing overlap issue before evaluation claims. Do not upload raw
benchmark data or publish dashboards containing it until rights are established.
Never present a local Spark demo, duplicated data, a folder structure or a
successful cloud run as proof of production-scale operational experience.
This project supports preparation; it does not guarantee hiring, establish
degree equivalence, or prove coding-test and English proficiency by itself.
