# Day 3: human review in progress

Prepare the local worksheet from the project root:

```sh
python -m scripts.prepare_review
```

Open `data/reviews/day3/worksheet.md`. Review pairs 1–5 first, then continue in
batches of five. Record Match, Different, or Review, the supporting evidence,
and missing or confusing information. Only then consult `answer-key.md` and
record agreement or disagreement. Preserve the benchmark labels.

The sample contains 10 matches, 10 hard negatives, and 10 randomly selected
negatives, drawn from the pinned training file with seed 42 and shuffled.
This is a deliberately balanced learning sample, not an accuracy estimate.
The generator verifies the training file hash and never reads validation/test
files. `selection.json` records the exact pair IDs. Rerunning refuses to
overwrite existing review files so human notes are preserved.

Generated files remain under the Git-ignored `data/` folder because they contain
source listing text. The repository includes only the generator and instructions.

Status: worksheet prepared; human judgments and the final findings summary are
pending. Day 3 will be complete after all 30 pairs are reviewed and common
failure cases and label-definition disagreements are summarized.
