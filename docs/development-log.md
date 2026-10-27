# Development log

## Day 1 — 2026-10-25

- **Changed:** Added the runnable Python introduction, project README, and `.gitignore`; set up a local virtual environment and Git repository, then published Day 1 to `MikaelaTasha/ProductMatch` using GitHub's privacy email for the commit.
- **Why:** Establish a reproducible starting point and define the matching task before adding data or models.
- **Checked:** Ran `main.py` with the virtual environment's Python; checked that local environments, data, databases, and credentials are ignored by Git; verified the commit's author and committer privacy email and a successful push to GitHub.
- **Uncertain:** Dataset terms, benchmark-label alignment, and matching performance have not yet been evaluated.

## Day 2 — 2026-10-25

- **Changed:** Added the official WDC small/50%-corner-case download and training preview tool, dataset source/terms documentation, pinned archive and file hashes, a split audit, and focused loader checks.
- **Why:** Make dataset setup reproducible and inspect supplied pairs before building a matcher; keep raw files out of GitHub.
- **Checked:** Downloaded successfully with the Python script into a fresh temporary folder; loaded 2,500 training pairs (500 matches, 2,000 non-matches), verified all five selected file hashes/counts, reran preparation from the cache, and passed seven synthetic-data tests. Audited offer-ID overlap without model evaluation.
- **Uncertain:** Dataset redistribution license and alignment with our matching definition remain unresolved. Seen/half-unseen test files share some IDs with development splits; preserve files and investigate before evaluation. No model has been trained.

## Day 3 — 2026-10-25 to 2026-10-26 (completed)

- **Changed:** Prepared a reproducible local 30-pair worksheet, recorded all user judgments separately from assistant feedback, and summarized findings in `docs/day3-findings.md`.
- **Why:** Inspect matching evidence before model development without presenting benchmark labels as our own judgments.
- **Checked:** Selected 30 unique training pairs; verified balanced sampling, deterministic selection, overwrite protection, and 30 saved decisions. Recorded decisions agree with 27 benchmark labels, with three disagreements; this is not model accuracy.
- **Uncertain:** Several benchmark matches remain ambiguous under our strict identity definition. Source labels are unchanged. Dataset redistribution terms and the Day 2 split-overlap issue remain unresolved.

## Day 4 — 2026-10-26 (completed)

- **Changed:** Added SQLite tables for listings, split provenance and labeled pairs, an atomic repeatable importer, example SQL queries and a database guide.
- **Why:** Store each listing once while preserving official pair labels and split memberships for later browsing and evaluation.
- **Checked:** Imported 4,391 listings and 18,500 pairs across five splits; rerun inserted zero rows. Compared all stored pair fields with source data, checked SQLite integrity/foreign keys, executed all example queries and passed all 14 tests including conflict rollback.
- **Uncertain:** Official split overlap and ambiguous product identity remain unresolved. No model, prediction store, human-review database or interface has been implemented yet.

## Day 5 — 2026-10-26 (completed)

- **Changed:** Added the Streamlit training-pair explorer, title/ID search, pair navigation, hidden benchmark answers, literal listing-text display, read-only queries, dependency pin and setup guide.
- **Why:** Make original listing evidence easy to compare before building a matcher; keep test data outside the browsing workflow.
- **Checked:** All 19 tests passed, including training-only queries, read-only access, answer reset, navigation, search and missing-database behavior. Started the local server and inspected the browser and search with real training data.
- **Uncertain:** Cross-platform installation and full multilingual search are not verified. The interface does not predict or save human decisions. Dataset terms, identity ambiguities and the official split-overlap issue remain unresolved.

## Roadmap alignment — 2026-10-26 (before Day 6)

- **Changed:** Added `docs/learning-roadmap.md`, organizing data-engineering skills into 36 work sessions and independent learning exercises.
- **Why:** The other chat discussed broader technical coverage, but the original project roadmap had not incorporated it. Make gaps and future deliverables explicit.
- **Checked:** Compared the planned data-engineering coverage with the implemented Days 1–5 and original 20-session plan.
- **Uncertain:** Cloud provider, BI tool, deployment costs and data-upload rights remain to be resolved. Extended requirements are planned rather than demonstrated; Day 6 has not started.

## Day 6 — 2026-10-26 (implementation complete; explanation exercise pending)

- **Changed:** Added a versioned lowercase/whitespace title transformation and read-only training preview with separate original/normalized fields. The user first identified safe lowercase conversion and the need to preserve size differences.
- **Why:** Introduce a repeatable data-cleansing step without erasing model codes, quantities or original evidence.
- **Checked:** Inspected 1,000 training titles (999 changed); all pass idempotence checks. All 25 tests pass, including six new normalization checks and a synthetic database preservation/training-boundary check.
- **Uncertain:** The user's final explanation is pending. Case-sensitive product distinctions, unit equivalence and broader multilingual normalization are not resolved. No prediction or matching-quality claim is made.

## Day 6 learning follow-up — 2026-10-26

The user explained that `2x8GB` may describe two modules, demonstrating why pack
configuration matters. Independent string-operation/idempotence explanation is
not yet verified.

## Day 7 — 2026-10-26 (implementation complete; numerical exercises pending)

- **Changed:** Added a training-fitted TF-IDF/cosine baseline, validation F1 threshold selection, aggregate report and scikit-learn dependency pin.
- **Why:** Establish a measured comparison point before introducing attribute features. The user first explained that similar titles can differ in series or size.
- **Checked:** All 33 tests passed; repeated run reproduced results and left the database unchanged. Fitted 1,000 unique training titles. Validation precision 39.57%, recall 88.00%, F1 54.59%; 672 false matches and 60 missed matches. No test sets read.
- **Uncertain:** Results use the same validation set as threshold selection and are not held-out performance. False-match rate is unsuitable for automatic merging. Numerical learning exercises, attribute features, Review policy and test-split overlap resolution remain pending.


## Day 8 — 2026-10-27 (implementation complete; learning follow-up pending)

- **Changed:** Added versioned title evidence extraction, lowercase model candidates with original spelling, unit conversion, explicit pack arithmetic, missing flags and a training-only preview with aggregate coverage.
- **Why:** Distinguish capacity, frequency and pack configuration before creating pair-comparison features. Keep uncertain model tokens as candidates.
- **Checked:** All 42 tests passed, including nine extractor tests. Inspected five training pack examples. Previewed 1,000 unique training listings: model candidates in 762, storage in 173, volume in 21, frequency in 43, explicit counts/packs in 26. Database SHA-256 unchanged; no test-set evaluation.
- **Uncertain:** Coverage is not accuracy. Compatibility references, unsupported formats and ambiguous quantities require further handling. Matching predictions remain unchanged. The user identified model/count/per-module capacity; total-capacity versus frequency was clarified, with independent follow-up pending.


## Day 9 — 2026-10-27 (implementation complete; independent exercises pending)

- **Changed:** Added 14 attribute comparisons, each encoded as five evidence states (70 numeric features), a training-only aggregate preview, SQL join/quality summary and feature dictionary. Equal totals retain differences in pack counts and per-item capacity.
- **Why:** Supply label-free evidence to the planned classifier without treating missing information or multiple candidates as a verified conflict.
- **Checked:** All 49 tests pass. Two real-data reports agree and preserve the database hash. SQL audited 2,500 training pairs: no broken references/missing titles, 2,123 pairs with at least one missing brand. No validation/test evaluation or prediction changes.
- **Uncertain:** Extraction errors carry through; some comparison fields have no training variation. No matching improvement measured. User correctly calculated 8GB total; independent pack explanation and Python/SQL practice remain pending.


## Day 10 — 2026-10-27 (implementation complete; explanation exercise pending)

- **Changed:** Added logistic regression with 71 inputs (title cosine and Day 9 indicators), training-only fitting, validation threshold selection, comparison report, reproducible configuration and convergence guard.
- **Why:** Measure whether a supervised combination gives a more useful comparison point before introducing human review. No ablation claim is made.
- **Checked:** All 55 tests pass. Real-data report reproduced exactly, database hash unchanged, saved Day 7 baseline metrics reproduced. Validation precision 51.49%, recall 72.60%, F1 60.25%; 342 false matches and 137 missed matches, versus 672 and 60 for the baseline. No test sets read.
- **Uncertain:** Validation is reused for development and threshold selection. Scores are uncalibrated; false matches remain common. No Review policy, hard identity constraints or saved inference model. Probability/class-imbalance explanation exercises and split audit remain pending.


## Day 11 — 2026-10-27 (implementation complete; explanation pending)

- **Changed:** Added two-threshold Match/Different/Review policy, validation coverage maximization under provisional 95% per-class precision and 20-case support constraints, plus fixed 90%/99% scenarios and explicit undefined metrics.
- **Why:** Make review workload and both automatic error types visible without pretending every pair can be reliably decided.
- **Checked:** All 61 tests pass, including exhaustive-reference threshold search. Repeated real report is identical, database hash unchanged, Day 10 binary metrics reproduced. Default: 917 Review cases (36.68%), 1,583 automatic Different decisions including 79 actual matches, and zero automatic Matches.
- **Uncertain:** Automatic Match cannot meet the targets with adequate support; its precision is undefined and recall zero. No underlying model improvement, completed human reviews or held-out evaluation claimed. Browser integration, split/error audit and independent explanation remain pending.


## Day 12 — 2026-10-27 (audit complete; explanation pending)

- **Changed:** Added reproducible validation error slices, local-only difficult examples, unordered pair/product-cluster metadata audit and evaluation options. Inspected ten unique validation error pairs; recorded hypotheses without relabeling or model changes.
- **Why:** Investigate observed failures and qualify future test claims before model/protocol freezing.
- **Checked:** All 64 tests pass; aggregate audit repeats and database hash stays unchanged. Raw file hashes/counts verified. Half-unseen test repeats 20 training and 23 validation pairs; 1,664 pairs touch development offers. Seen test has 35 pairs touching development offers. Unseen has zero shared offers/clusters/pairs with development. Train/validation share all 500 clusters despite disjoint offers.
- **Uncertain:** Publisher-side overlap cause unverified; error categories are hypotheses, not exhaustive ground truth. No test predictions/performance computed. Primary unseen evaluation and qualified secondary/filter options await Day 13 freeze. Independent cluster/generalization explanation pending.


## Day 13 — 2026-10-27 (implementation/freeze complete; explanation pending)

- **Changed:** Tested one auxiliary punctuation-insensitive model-code comparison, retaining original evidence/ambiguity. Predeclared strict validation-F1 improvement selects the 76-input candidate. Added a frozen evaluation protocol, exact source/runtime/data/model fingerprints and a verifier that refuses silent changes.
- **Why:** Address observed code-format failures without broad normalization changes; fix evaluation rules before looking at test performance.
- **Checked:** All 69 tests pass. Experiment reproduced and freeze creation/verification passed. Candidate validation F1 60.47% versus 60.25%, false matches 340 versus 342, missed matches 136 versus 137. Default policy reviews 908 cases (36.32%) with 79 false Different decisions and no automatic Matches. In-memory threshold tampering rejected.
- **Uncertain:** Gain is small and validation-tuned, not statistically established. Automatic matching still fails the precision/support target. Frozen protocol qualifies overlap-contaminated secondary sets and specifies supplementary filtering. No test performance or browser integration yet; independent freeze explanation pending.
