# Day 5: training-pair explorer

The Streamlit app displays two listings with their original titles, brands,
descriptions, prices and currencies. Missing attributes are shown as
“Not provided”. Source text is rendered literally rather than interpreted as
Markdown or HTML. Two panels sit side by side on a wide screen and stack on
narrow screens.

## Start locally

From the project root:

```sh
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open http://127.0.0.1:8501 in a browser. Keep the terminal running; stop the
server with Control+C. The server is bound to your own computer, not published
as a public site. Streamlit usage statistics are disabled in the project config.

For a fresh checkout, first create `.venv` as described in the README, then run:

```sh
python scripts/wdc_data.py --download
python -m scripts.import_data
```

The interface shows setup instructions if the database is missing and does not
create a blank database accidentally. The default database path is resolved
relative to the project. Developers can set `PRODUCTMATCH_DB` to another
database using the same schema; this is also how the tests use fictional data.

## Try it

1. Use **Next** and **Previous**, or enter a pair number and press Enter.
2. Search a title keyword or exact pair ID in the sidebar, then press Enter.
   Search uses literal substring matching; it is not a matching model.
   SQLite's default case-insensitive LIKE behavior covers ASCII letters, not
   full multilingual case folding. Clear the search to see all training pairs.
3. Compare the two listings before selecting **Show benchmark label**.
4. Change the pair or search: the answer is hidden again automatically.

The displayed answer is the original benchmark label, never a prediction.
There are no correction or save controls yet. The Day 3 review worksheet stays
separate. Validation and test data cannot be selected or retrieved through this
browser's query functions. SQLite connections use read-only mode.

## Validation and limitations

- Installed and ran Streamlit 1.65.0 with Python 3.10.1 on macOS.
- All 19 tests passed, including five new tests covering read-only queries,
  training-only access, navigation boundaries, answer reset, search, and missing
  database handling. UI tests use Streamlit AppTest and fictional data.
- Started the actual local server and inspected the browser layout and a search
  result against a previously reviewed training pair.
- The full dependency tree is resolved by pip; `requirements.txt` pins Streamlit,
  not every transitive dependency. Other operating systems have not been tested.
- Original descriptions can be long and are scrollable. No images are supplied
  by this dataset schema. No model predictions, persisted review decisions,
  deployment, or resolution of the split-overlap issue is included in Day 5.

Run checks after installing requirements:

```sh
python -m unittest discover -s tests -v
```

Next: Day 6 title normalization with tests that preserve model codes and numbers.
