"""Fingerprint the selected pipeline and verify the frozen evaluation inputs."""
import hashlib
import json
import platform

import numpy as np
import scipy
import sklearn

from productmatch.candidate import CANDIDATE_VERSION, CandidatePairClassifier
from productmatch.classifier import CLASSIFIER_VERSION, PairClassifier
from productmatch.baseline import load_development_split
from scripts.wdc_data import ROOT, DEFAULT_DATA_DIR, checksum

FROZEN_FILES = (
    'productmatch/normalization.py', 'productmatch/attributes.py', 'productmatch/features.py',
    'productmatch/baseline.py', 'productmatch/classifier.py', 'productmatch/candidate.py',
    'productmatch/review.py', 'productmatch/browsing.py', 'productmatch/frozen.py',
    'scripts/wdc_data.py', 'scripts/select_day13.py', 'scripts/freeze_evaluation.py',
    'requirements.txt', 'docs/dataset-manifest.json', 'docs/day13-experiment-results.json',
    'docs/evaluation-protocol.md',
)
PROTOCOL = {
    'primary': 'test_unseen',
    'secondary': ['test_seen', 'test_half_unseen'],
    'secondary_caveat': 'Official sets contain offers or pairs shared with development.',
    'supplementary_filter': 'For each secondary split exclude pairs whose left or right ID appears in train or validation; preserve original splits.',
    'pool_test_sets': False, 'refit_on_validation': False, 'retune_on_test': False,
    'report': ['frozen review-policy counts, class precision, automatic-match recall, review rate, coverage',
               'frozen binary-threshold confusion matrix, precision, recall, F1',
               'split sizes, label balance, overlap caveats; no independent-pair confidence claim'],
}


def runtime():
    return {'python':platform.python_version(),'numpy':np.__version__,
            'scipy':scipy.__version__,'scikit_learn':sklearn.__version__}


def model_fingerprint(model):
    content = {'vocabulary':{k:int(v) for k,v in model.title_model.vectorizer.vocabulary_.items()},
               'idf':model.title_model.vectorizer.idf_.tolist(),
               'coefficients':model.estimator.coef_.tolist(),
               'intercept':model.estimator.intercept_.tolist(),
               'classes':model.estimator.classes_.tolist()}
    return hashlib.sha256(json.dumps(content,sort_keys=True,allow_nan=False).encode()).hexdigest()


def build_freeze(report, model, db_path):
    chosen=report['results'][report['selected_version']]
    return {'freeze_version':'evaluation-freeze-v1', 'selected_version':report['selected_version'],
            'selection_rule':report['selection_rule'], 'feature_names':chosen['feature_names'],
            'binary_threshold':chosen['binary_threshold'],
            'review_policy':chosen['review_policy'], 'protocol':PROTOCOL,
            'model_fingerprint_sha256':model_fingerprint(model), 'runtime':runtime(),
            'database_sha256':checksum(db_path),
            'file_sha256':{name:checksum(ROOT/name) for name in FROZEN_FILES},
            'test_performance_seen':False}


def verify_freeze(freeze, db_path):
    if freeze['freeze_version'] != 'evaluation-freeze-v1' or freeze['protocol'] != PROTOCOL:
        raise ValueError('Unsupported or changed evaluation protocol.')
    if freeze['runtime'] != runtime():
        raise ValueError('Runtime differs from freeze; do not silently refreeze.')
    if set(freeze['file_sha256']) != set(FROZEN_FILES):
        raise ValueError('Frozen file inventory differs.')
    for name,digest in freeze['file_sha256'].items():
        if checksum(ROOT/name) != digest:
            raise ValueError(f'Frozen file changed: {name}')
    if checksum(db_path) != freeze['database_sha256']:
        raise ValueError('Database differs from frozen snapshot.')
    manifest=json.loads((ROOT/'docs/dataset-manifest.json').read_text())
    for entry in manifest['splits'].values():
        if checksum(DEFAULT_DATA_DIR/entry['filename']) != entry['sha256']:
            raise ValueError('Raw split differs from pinned snapshot.')
    report=json.loads((ROOT/'docs/day13-experiment-results.json').read_text())
    chosen=report['results'][report['selected_version']]
    if (freeze['selected_version'] != report['selected_version'] or
        freeze['feature_names'] != chosen['feature_names'] or
        freeze['binary_threshold'] != chosen['binary_threshold'] or
        freeze['review_policy'] != chosen['review_policy'] or
        freeze['selection_rule'] != report['selection_rule']):
        raise ValueError('Frozen configuration differs from selected experiment.')
    classes={CLASSIFIER_VERSION:PairClassifier,CANDIDATE_VERSION:CandidatePairClassifier}
    model=classes[freeze['selected_version']]().fit(load_development_split(db_path,'train'))
    if model_fingerprint(model) != freeze['model_fingerprint_sha256']:
        raise ValueError('Refitted model differs from freeze; stop before test scoring.')
    return model
