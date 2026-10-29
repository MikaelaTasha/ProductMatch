"""Explain stored evidence without changing scores or claiming causal attribution."""
import json
import math

from productmatch.candidate import CANDIDATE_VERSION, CANDIDATE_FEATURE_NAMES, code_alias_state
from productmatch.classifier import CLASSIFIER_VERSION, MODEL_FEATURE_NAMES
from productmatch.features import STATES, compare_titles
from productmatch.review import decisions

LABELS = {
    'model_candidate': ('Possible model code', ''),
    'storage_mention': ('Storage mentioned (role unspecified)', 'GB'),
    'storage_per_item': ('Storage per item', 'GB'),
    'storage_total': ('Calculated pack storage', 'GB'),
    'storage_count': ('Storage pack item count', ''),
    'volume_mention': ('Volume mentioned (role unspecified)', 'ml'),
    'volume_per_item': ('Volume per item', 'ml'),
    'volume_total': ('Calculated pack volume', 'ml'),
    'volume_count': ('Volume pack item count', ''),
    'frequency': ('Frequency', 'MHz'),
    'pack_count': ('Pack count', ''), 'sheet_count': ('Sheet count', ''),
    'piece_count': ('Piece count', ''), 'module_count': ('Module count', ''),
}
STATE_LABELS = {'agrees':'Same extracted value', 'differs':'Different extracted values',
                'ambiguous':'Multiple possible values', 'missing_one':'Missing on one side',
                'missing_both':'Not found in either title'}


def format_values(values, unit):
    if not values:
        return 'Not extracted'
    return ', '.join((format(v,'.12g') if isinstance(v,(int,float)) else str(v)) +
                     (f' {unit}' if unit else '') for v in values)


def explain_prediction(record):
    prediction=record['prediction']
    freeze=json.loads(record['model']['freeze_json'])
    version=freeze['selected_version']
    schemas={CLASSIFIER_VERSION:MODEL_FEATURE_NAMES,CANDIDATE_VERSION:CANDIDATE_FEATURE_NAMES}
    if version not in schemas or freeze['feature_names']!=list(schemas[version]):
        raise ValueError('This stored model has no supported evidence display.')
    values=json.loads(prediction['features_json'])
    if len(values)!=len(freeze['feature_names']) or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in values):
        raise ValueError('Stored evidence vector is invalid.')
    stored=dict(zip(freeze['feature_names'],values))
    if not 0 <= stored['title_cosine'] <= 1:
        raise ValueError('Stored title similarity is invalid.')
    inputs=json.loads(prediction['input_json'])
    compared=compare_titles(inputs['left_title'],inputs['right_title'])
    expected=dict(compared['features'])
    alias=None
    if version==CANDIDATE_VERSION:
        alias=code_alias_state(inputs['left_title'],inputs['right_title'])
        expected.update({f'code_alias_{state}':int(alias==state) for state in STATES})
    if any(stored[key]!=value for key,value in expected.items()):
        raise ValueError('Extracted details no longer agree with the stored prediction evidence.')
    policy=freeze['review_policy']
    lower,upper=policy['lower_threshold'],policy['upper_threshold']
    decision=str(decisions([prediction['score']],lower,upper)[0])
    if prediction['decision']!=decision:
        raise ValueError('Stored decision does not agree with its recorded thresholds.')
    rows=[]
    counts={state:0 for state in STATES}
    for field,item in compared['comparisons'].items():
        name,unit=LABELS[field]
        rows.append({'Detail':name,'Left':format_values(item['left'],unit),
                     'Right':format_values(item['right'],unit),'Evidence':STATE_LABELS[item['state']],
                     'state':item['state']})
        counts[item['state']]+=1
    summary=(f"Details with the same extracted value: {counts['agrees']}; "
             f"different values: {counts['differs']}; multiple candidates: {counts['ambiguous']}. "
             f"{counts['missing_one']+counts['missing_both']} details lack evidence on one or both sides.")
    if decision=='Review':
        reason='This score falls in the recorded review range, so the pair is routed for human judgment.'
    elif decision=='Different':
        reason='This score is below the recorded Different threshold. This is a model decision, not proof of different products.'
    else:
        reason='This score reaches the recorded Match threshold. Check product variants before accepting a merge.'
    if upper>1:
        reason+=' Automatic Match is disabled for this model policy.'
    return {'rows':rows,'summary':summary,'decision_reason':reason,
            'title_similarity':stored['title_cosine'],
            'alias_evidence':STATE_LABELS[alias] if alias else None,
            'lower_threshold':lower,'upper_threshold':upper,
            'score':prediction['score'], 'match_enabled':upper<=1}
