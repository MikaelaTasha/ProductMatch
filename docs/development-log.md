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
