"""Train logistic regression on title similarity and label-free pair attributes."""
import warnings

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression

from productmatch.baseline import TitleBaseline
from productmatch.features import FEATURE_NAMES, compare_titles

CLASSIFIER_VERSION = 'logistic-title-attributes-v1'
MODEL_FEATURE_NAMES = ('title_cosine', *FEATURE_NAMES)
PARAMETERS = {'C': 1.0, 'solver': 'lbfgs', 'max_iter': 1000,
              'tol': 1e-4, 'class_weight': None, 'random_state': 0}


class PairClassifier:
    def __init__(self):
        self.title_model = TitleBaseline()
        self.estimator = LogisticRegression(**PARAMETERS)

    def matrix(self, split):
        cosine, diagnostics = self.title_model.score(split)
        rows = []
        for score, pair in zip(cosine, split['pairs']):
            features = compare_titles(split['titles'][pair['left_id']],
                                      split['titles'][pair['right_id']])['features']
            rows.append([score, *(features[name] for name in FEATURE_NAMES)])
        return np.asarray(rows, dtype=float), diagnostics

    def fit(self, train):
        labels = np.asarray([p['label'] for p in train['pairs']])
        if set(labels.tolist()) != {0, 1}:
            raise ValueError('Training requires both binary label classes.')
        self.title_model.fit(train['titles'])
        matrix, _ = self.matrix(train)
        # A nonconverged fit must not silently produce a published report.
        with warnings.catch_warnings():
            warnings.simplefilter('error', ConvergenceWarning)
            self.estimator.fit(matrix, labels)
        return self

    def score(self, split):
        matrix, diagnostics = self.matrix(split)
        return self.estimator.predict_proba(matrix)[:, 1], matrix[:, 0], diagnostics
