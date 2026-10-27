"""An auxiliary model-code comparison; original candidates remain unchanged."""
import re

import numpy as np

from productmatch.attributes import extract_title_attributes
from productmatch.classifier import PairClassifier, MODEL_FEATURE_NAMES
from productmatch.features import STATES, compare_values

CANDIDATE_VERSION = 'logistic-title-attributes-code-alias-v1'
CANDIDATE_FEATURE_NAMES = (*MODEL_FEATURE_NAMES, *(f'code_alias_{state}' for state in STATES))


def code_alias_state(left_title, right_title):
    def candidates(title):
        return {item['normalized'] for item in extract_title_attributes(title)['model_candidates']}
    left, right = candidates(left_title), candidates(right_title)
    original = compare_values(left, right)
    # Preserve uncertainty even if several original codes collapse to one alias.
    if original in ('missing_both', 'missing_one', 'ambiguous'):
        return original
    canonical = lambda values: {re.sub(r'[-/.]', '', value) for value in values}
    return compare_values(canonical(left), canonical(right))


class CandidatePairClassifier(PairClassifier):
    def matrix(self, split):
        matrix, diagnostics = super().matrix(split)
        states = [code_alias_state(split['titles'][p['left_id']], split['titles'][p['right_id']])
                  for p in split['pairs']]
        extra = np.array([[int(state == choice) for choice in STATES] for state in states], dtype=float)
        return np.column_stack((matrix, extra)), diagnostics
