# Day 3 findings

Completed 2026-10-26: 30 training pairs reviewed with the user in batches of five.
The local worksheet preserves original answers separately from assistant feedback.
Pairs 9, 11 and 29 were interpreted as Different because the user described a
shared type or brand but a different variant. These interpretations were stated
in the conversation, not treated as verbatim binary judgments.

## Review outcome

Recorded decisions agree with 27 of 30 benchmark labels. Pairs 16, 18 and 21
disagree. This is agreement with benchmark labels, not verified correctness or
model accuracy. The sample was deliberately balanced across matches, hard
negatives and random negatives. No model was trained or evaluated, and no source
labels were changed. The user selected no Review decisions; several cases below
still warrant uncertainty under our intended product definition.

## What the examples taught us

| Observation | Review evidence | Consequence for later work |
| --- | --- | --- |
| Shared function or brand is insufficient | Pairs 5, 11, 21 and 29 contain capacity, generation or model differences | Preserve numbers and model codes; compare variant attributes |
| Wording can differ while model codes agree | Pairs 1, 10, 16, 19 and 23 | Normalize carefully without erasing meaningful code differences |
| Missing details do not prove a mismatch | Pair 18 lacks enough evidence to confidently resolve identity | Represent missingness explicitly and support Review |
| Product titles can hide conflicting specifications | Pair 15 shares a title pattern but reports different speeds | Surface contradictions rather than relying only on title similarity |
| Size can remain unspecified | Pair 25 lacks cap sizes | Do not claim verified variant identity from brand and series alone |
| Compatibility is not necessarily product identity | Pair 28 names the same replacement reference but does not establish the same manufacturer | Distinguish a compatibility code from the actual product's model |
| Domain understanding matters | Pair 4 was called different correctly, but printer ink was mistaken for a memory card | Check the evidence behind a decision, not just label agreement |

## Disagreements and unresolved cases

- **Pair 16:** User chose Different, benchmark says Match. The user's proposed
  series difference was not established in the supplied text. The shared
  cartridge code supports a match; wording and missing volume can still justify
  Review. We did not verify an external manufacturer specification.
- **Pair 18:** User chose Different, benchmark says Match. Multilingual naming
  and missing volume/model information leave uncertainty. Same brand alone
  supports neither an automatic match nor a definite mismatch.
- **Pair 21:** User chose Match, benchmark says Different. The supplied titles
  explicitly name different generations despite matching brand and wattage.
- **Pairs 15, 25 and 28:** User chose Match and agrees with the benchmark, but
  conflicting specifications, unspecified size, or uncertain replacement identity
  leave a gap between benchmark agreement and our intended task definition.

These are inspection findings and policy questions, not verified benchmark label
errors. Human feedback has not replaced the original answers. Later threshold
selection must use validation data, not this small reviewed sample.

## Available attributes and next step

Observed listing fields include title, brand, description, price and currency;
some values are missing. Size, model and pack quantity have no dedicated fields
in this snapshot and may need extraction from text. IDs identify records;
cluster IDs, labels and hard-negative metadata must not become model features.

Day 4 will add SQLite tables for listings and labeled pairs, preserve split
provenance and original labels, and make repeated imports safe from duplicates.
The Day 2 split-overlap issue remains unresolved and must be investigated before
evaluation. Database implementation has not started.
