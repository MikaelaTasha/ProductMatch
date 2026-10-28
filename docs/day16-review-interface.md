# Day 16: review queue and saved judgments

Completed 2026-10-28. The Streamlit app now has two workspaces: Explore pairs
and Review queue. Launch it with:

```sh
python -m streamlit run app.py
```

Open http://127.0.0.1:8501 and select **Review queue** in the sidebar. If the
prediction store is missing, run `python -m scripts.store_predictions` first.

## Save your first review

1. Leave Review status as Pending and Model decisions to include as Review.
2. Choose a pair. Compare its original titles, sizes, model codes and quantities.
3. Enter your name or a local reviewer ID.
4. Select Match, Different or Review; optionally explain your reasoning.
5. Click Save review. A confirmation identifies the pair and saved judgment.
6. Select Completed to revisit Match/Different judgments and view their history.

Review keeps the pair Pending when evidence is insufficient. Match or Different
moves it to Completed. To inspect stored automatic Different predictions too,
choose All under Model decisions to include. The queue initially contains 852
model-Review pairs from the 2,500 stored training predictions; these are workflow
examples, not new evaluation results.

## Evidence and history

The page distinguishes original listing details, stored model decision/score,
latest human judgment and the separately hidden benchmark label. A model score
is not calibrated confidence. Dataset text and review notes render literally.
Prediction provenance is available in an expander. No judgment is preselected.

Saving appends an event to the separate local prediction store. Earlier events,
model scores and source benchmark labels remain unchanged. An identical retry
with the same request ID cannot create another event. A subsequent deliberate
save creates a new event, preserving the correction history. Latest means the
last inserted event for that prediction; Completed is a workflow status, not
proof that the judgment is correct.

After a successful save the pair selection clears, so another pair must be
chosen explicitly. Form keys are scoped to each prediction: notes, judgments
and revealed benchmark answers do not carry over to another pair. Drafts are
not guaranteed to persist when navigating away or refreshing.

The queue is restricted to training predictions from the selected stored model
and the exact current source-database hash. Save-time checks repeat that scope
validation. A changed source or mismatched model blocks saving. Human judgments
are not automatically incorporated into training.

## Verification and limits

All 86 tests pass, including five new isolated review-interface tests for saving,
pending/completed transitions, revisions/history, required reviewer input,
pair-switch isolation, missing stores and source/model mismatches. Fictional
test reviews use temporary databases only.

The real local browser was opened and inspected on 2026-10-28. It showed 852
pending Review predictions, original listings and the form with no preselected
judgment. No real review was submitted; the real review-event count remained
zero. The frozen source/model verifier passed after the UI checks. The narrow
browser panel stacks listing cards vertically; a wider window supports side-by-side
comparison.

This remains a local single-user prototype. Reviewer IDs are self-supplied, with
no authentication or concurrent-review conflict workflow. All earlier matching
quality limitations remain. Day 17 will present extracted matching evidence and
missing details more clearly. Learning exercise: explain why a saved human
judgment should remain separate from the benchmark label and model prediction.
