# Day 6: conservative title normalization

Implementation verified 2026-10-26. The user identified lowercase conversion as
safe and accurate size preservation as necessary, then explained that `2x8GB`
describes two modules rather than an individual module. Independent explanation
of the string operations/idempotence remains unverified; passing tests does not
establish independent understanding.

## Rule

`productmatch/normalization.py` defines `normalize_title` and a transformation
version, `lowercase-whitespace-v1`. For a string, the operation is:

```python
" ".join(title.lower().split())
```

`lower()` lowercases letters. `split()` with no argument separates on whitespace
and removes leading/trailing whitespace. Joining with one space makes spacing
consistent. Digits and punctuation are preserved; letters within codes also
become lowercase. For example:

```text
Canon PG-545 Black Ink 8ml  → canon pg-545 black ink 8ml
Canon PG-545 Black Ink 18ml → canon pg-545 black ink 18ml
```

The function returns a new value rather than updating a database record. Missing
`None` remains `None`; empty or whitespace-only strings become an empty string.
Unexpected non-string types raise an error rather than silently becoming text.

## Preview and evidence

From the project root with `.venv` active:

```sh
python -m scripts.preview_normalization --examples 5
python -m unittest discover -s tests -v
```

The preview reads unique training listings through a read-only SQLite connection.
It produces separate `original_title`, `normalized_title` and
`normalization_version` fields in memory. No normalized table or export is
written yet, and the pair explorer continues displaying original text.

Measured on the current database: 1,000 training titles inspected, 999 changed,
and all 1,000 satisfy `normalize(normalize(title)) == normalize(title)`. This
property is called **idempotence**: rerunning this transformation does not keep
changing the result. It does not prove the transformation preserves every
possible product distinction.

Six added tests protect variant differences (capacity, generation, decimal
values, pack structure and punctuation), missing values, unexpected types,
multilingual text, idempotence and original-data preservation. All 25 project
tests pass. A synthetic database check confirms the preview excludes test-only
listings and leaves database bytes unchanged.

## Scope and limitations

This is a reproducible cleansing step for the data pipeline, not a matching
decision. Equal normalized titles do not prove equal products, and different
normalized titles do not prove different products. Case-only distinctions are
intentionally collapsed; originals remain available for inspection.

No punctuation stripping, unit conversion, translation, spelling correction or
attribute extraction is performed. `PG-545` and `PG545`, `8 ml` and `8ml`, and
`1L` and `1000ml` remain distinct strings. Unicode lowercasing is used, but full
multilingual equivalence and Unicode normalization are not implemented. These
choices can be revisited with evidence and a new transformation version.

## Learning checkpoint

Explain why running the function twice gives the same output, and why we retain
the original title. Predict the result of `"  DDR4  2x8GB  "` before running it.
Next: Day 7, TF-IDF and cosine similarity, with a small vector calculation.
