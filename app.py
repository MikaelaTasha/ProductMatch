"""Run with: python -m streamlit run app.py"""
import os
from pathlib import Path
import sqlite3

import streamlit as st

from productmatch.browsing import find_training_pairs, get_training_pair
from productmatch.predictions import DEFAULT_STORE
from productmatch.review_ui import review_page

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get('PRODUCTMATCH_DB', ROOT / 'data/productmatch.sqlite3'))

st.set_page_config(page_title='ProductMatch · Pair explorer', page_icon='🔎', layout='wide')


def hide_label():
    st.session_state.reveal_label = False


def reset_search():
    st.session_state.position = 1
    hide_label()


def move_pair(step):
    st.session_state.position += step
    hide_label()


def display_value(value):
    return 'Not provided' if value is None or value == '' else str(value)


def listing_card(listing, heading):
    with st.container(border=True):
        st.subheader(heading)
        st.caption(f"Listing {listing['listing_id']}")
        # Dataset text is rendered literally; it cannot inject Markdown or HTML.
        st.text(display_value(listing['title']))
        st.divider()
        st.markdown('**Brand**')
        st.text(display_value(listing['brand']))
        st.markdown('**Price · currency**')
        st.text(f"{display_value(listing['price'])} · {display_value(listing['price_currency'])}")
        st.markdown('**Description**')
        with st.container(height=230):
            st.text(display_value(listing['description']))


st.title('ProductMatch')
st.write('Compare the details. Decide what makes two listings the same product.')
mode = st.sidebar.radio('Workspace', ['Explore pairs', 'Review queue'], key='workspace_mode')
if mode == 'Review queue':
    if st.session_state.pop('review_clear_selection', False):
        st.session_state.pop('review_prediction', None)
    review_page(DB_PATH, Path(os.environ.get('PRODUCTMATCH_STORE', DEFAULT_STORE)), listing_card)
    st.stop()
st.caption('PAIR EXPLORER  ·  Training data only')

with st.sidebar:
    st.header('Explore pairs')
    st.text_input('Search titles or pair ID', key='search', on_change=reset_search,
                  placeholder='Try Canon, Kingston, or a pair ID')
    st.divider()
    st.markdown('**What counts as the same product?**')
    st.write('Model, size, and pack quantity must agree when known. Sellers and prices may differ.')
    st.write('Missing information is uncertainty, not proof of a difference.')
    st.caption('This explorer shows original listings and labels. Open Review queue to inspect stored predictions and save your judgment.')

try:
    pair_ids = find_training_pairs(DB_PATH, st.session_state.search)
except FileNotFoundError:
    st.info('Set up the local dataset to start exploring.')
    st.code('python scripts/wdc_data.py --download\npython -m scripts.import_data', language='bash')
    st.stop()
except sqlite3.Error:
    st.error('The database could not be read. Check the database setup in docs/day4-database.md.')
    st.stop()

if not pair_ids:
    st.info('No training pairs found. Try a different title or clear the search. If the database is empty, run python -m scripts.import_data.')
    st.stop()

if 'position' not in st.session_state or not 1 <= st.session_state.position <= len(pair_ids):
    st.session_state.position = 1
    hide_label()

pair_word = 'pair' if len(pair_ids) == 1 else 'pairs'
st.caption(f'{len(pair_ids):,} training {pair_word} in this selection')
previous, position, following = st.columns([1, 2, 1], vertical_alignment='bottom')
with previous:
    st.button('← Previous', key='previous', disabled=st.session_state.position == 1,
              on_click=move_pair, args=(-1,), use_container_width=True)
with position:
    st.number_input('Pair number', min_value=1, max_value=len(pair_ids), step=1,
                    key='position', on_change=hide_label)
with following:
    st.button('Next →', key='next', disabled=st.session_state.position == len(pair_ids),
              on_click=move_pair, args=(1,), use_container_width=True)

pair_id = pair_ids[st.session_state.position - 1]
try:
    pair = get_training_pair(DB_PATH, pair_id)
except (sqlite3.Error, ValueError):
    st.error('This pair could not be loaded. Check the database setup before continuing.')
    st.stop()
if pair is None:
    st.warning('This pair is no longer available. Clear the search to refresh the selection.')
    st.stop()

st.caption(f'Pair {st.session_state.position} of {len(pair_ids):,} · ID {pair_id}')
left, right = st.columns(2)
with left:
    listing_card(pair['left'], 'Left listing')
with right:
    listing_card(pair['right'], 'Right listing')

st.divider()
st.markdown('**Same product, different product, or not enough evidence?**')
st.write('Look for matching model codes and conflicting sizes or quantities before checking the supplied answer.')
st.checkbox('Show benchmark label', key='reveal_label')
if st.session_state.reveal_label:
    label = 'Match' if pair['label'] == 1 else 'Different'
    st.info(f'Benchmark label: {label}')
    st.caption('This is the dataset’s supplied label, not a model prediction. It may not resolve every ambiguity in our matching rules.')
else:
    st.caption('The answer is hidden so you can judge the evidence first.')
