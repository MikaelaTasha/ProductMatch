"""Streamlit review workflow; invoked separately from the original explorer."""
import sqlite3
import uuid

import streamlit as st

from productmatch.browsing import get_training_pair
from productmatch.evidence import explain_prediction
from productmatch.review_queue import available_models, queue_rows, get_review_record, submit_review
from scripts.wdc_data import checksum


def review_page(source_path,store_path,listing_card):
    st.caption('REVIEW QUEUE · Training predictions only')
    st.write('Record your judgment from the listing details. Your review does not replace the model prediction or benchmark label.')
    try:
        source_hash=checksum(source_path)
        models=available_models(store_path,source_hash)
    except (OSError,sqlite3.Error):
        st.info('Prepare the prediction store to start reviewing.')
        st.code('python -m scripts.store_predictions',language='bash')
        return
    if not models:
        st.info('No training predictions match this source database. Run the prediction storage command for this source.')
        return
    labels={m['model_id']:f"{m['classifier_version']} · {m['model_id'][:8]}" for m in models}
    with st.sidebar:
        model_id=st.selectbox('Stored model version',list(labels),format_func=labels.get,key='queue_model')
        status=st.selectbox('Review status',['Pending','Completed','All'],key='queue_status')
        model_decision=st.selectbox('Model decisions to include',['Review','All'],key='queue_decisions')
        st.caption('Pending includes unreviewed pairs and judgments saved as Review. Choose All model decisions to inspect automatic Different decisions too.')
    try:
        rows=queue_rows(store_path,source_hash,model_id,status=status,model_decision=model_decision)
    except (sqlite3.Error,ValueError) as error:
        st.error(f'Cannot read the review queue: {error}')
        return
    if 'review_saved_message' in st.session_state:
        st.success(st.session_state.pop('review_saved_message'))
    st.caption(f'{len(rows):,} pairs in this queue')
    if not rows:
        st.info('No pairs in this queue. Change the review status or model-decision filter.')
        return
    by_id={r['prediction_id']:r for r in rows}
    selected=st.selectbox('Choose a pair',list(by_id),index=None,
                          format_func=lambda pid:by_id[pid]['pair_id'],key='review_prediction',
                          placeholder='Select a pair to review')
    if selected is None:
        return
    try:
        record=get_review_record(store_path,selected,source_hash,model_id)
        prediction=record['prediction']
        pair=get_training_pair(source_path,prediction['pair_id'])
        if pair is None:
            raise ValueError('Original training pair is missing.')
    except (OSError,sqlite3.Error,ValueError) as error:
        st.error(f'Cannot load this pair: {error}')
        return
    st.subheader(f"Pair {prediction['pair_id']}")
    left,right=st.columns(2)
    with left:
        listing_card(pair['left'],'Left listing')
    with right:
        listing_card(pair['right'],'Right listing')
    st.info(f"Stored model decision: {prediction['decision']} · model score: {prediction['score']:.3f}")
    st.caption('The score is not calibrated confidence. Model predictions can be wrong.')
    st.subheader('Details to check')
    try:
        evidence=explain_prediction(record)
    except (ValueError,KeyError,TypeError) as error:
        st.warning(f'Extracted evidence is unavailable: {error} Use the original listings above.')
    else:
        st.write(evidence['decision_reason'])
        st.write(evidence['summary'])
        st.caption('These are title-extraction hints, not verified facts or an explanation of each feature’s influence on the score. Missing evidence does not mean a mismatch. Extraction can miss important differences; check the original listings.')
        show_missing=st.checkbox('Include details not found in either title',key=f'evidence_missing_{selected}')
        visible=[{k:v for k,v in row.items() if k!='state'} for row in evidence['rows']
                 if show_missing or row['state']!='missing_both']
        if visible:
            st.dataframe(visible,hide_index=True,width="stretch")
        else:
            st.info('No supported product details were extracted from either title. Inspect the original listings; this is not evidence of a match.')
        if evidence['alias_evidence']:
            st.caption(f"Model codes ignoring punctuation: {evidence['alias_evidence']}. This extra comparison does not establish product identity.")
        with st.expander('Score and decision thresholds'):
            st.text(f"Stored model score: {evidence['score']:.12g}\nTitle similarity: {evidence['title_similarity']:.12g}\nDifferent when score is below: {evidence['lower_threshold']:.12g}")
            if evidence['match_enabled']:
                st.text(f"Match when score is at least: {evidence['upper_threshold']:.12g}")
            else:
                st.text('Automatic Match: disabled')
            st.caption('Scores between the two thresholds go to Review. Displayed numbers are rounded; decisions use the full stored values.')
    history=record['reviews']
    if history:
        st.write(f"Latest human judgment: {history[-1]['decision']}")
        with st.expander(f'Review history ({len(history)})'):
            for event in history:
                st.text(f"{event['created_at']} · {event['reviewer']} · {event['decision']}")
                if event['note']:
                    st.text(event['note'])
    else:
        st.caption('No human reviews saved for this prediction yet.')
    with st.expander('Prediction provenance'):
        st.text(f"Prediction ID: {selected}\nModel: {record['model']['classifier_version']}\nSource split: train\nSource database SHA-256: {prediction['source_database_sha256']}")
    # Per-prediction widget keys prevent notes or decisions leaking to another pair.
    key=f'review_{selected}'
    token_key=f'{key}_event'
    if token_key not in st.session_state:
        st.session_state[token_key]=str(uuid.uuid4())
    with st.form(key,clear_on_submit=False):
        reviewer=st.text_input('Your name or reviewer ID',key=f'{key}_reviewer')
        decision=st.radio('Your judgment',['Match','Different','Review'],index=None,key=f'{key}_decision')
        note=st.text_area('Reason or note (optional)',key=f'{key}_note')
        save=st.form_submit_button('Save review')
    if save:
        if not reviewer.strip() or decision is None:
            st.error('Enter your reviewer ID and choose a judgment before saving.')
        else:
            try:
                submit_review(store_path,source_path,model_id=model_id,prediction_id=selected,
                              event_id=st.session_state[token_key],decision=decision,reviewer=reviewer,note=note)
            except (OSError,sqlite3.Error,ValueError) as error:
                st.error(f'Review was not saved: {error}')
            else:
                st.session_state.pop(token_key,None)
                st.session_state.review_saved_message=f"Saved {decision} for pair {prediction['pair_id']}. The model prediction is unchanged."
                # Clear the selection on the next run, before its widget is created.
                st.session_state.review_clear_selection=True
                st.rerun()
    if st.checkbox('Show benchmark label',key=f'{key}_benchmark'):
        st.info(f"Benchmark label: {'Match' if pair['label']==1 else 'Different'}")
        st.caption('Supplied dataset answer, separate from both model prediction and human judgment.')
