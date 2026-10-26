"""Training-only TF-IDF fitting and validation-only threshold selection."""
from contextlib import closing
import math

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from productmatch.browsing import connect_readonly
from productmatch.normalization import normalize_title

BASELINE_VERSION = 'title-tfidf-cosine-v1'
# Keep single-character numbers and internal model-code punctuation.
TOKEN_PATTERN = r'(?u)\b\w+(?:[./-]\w+)*\b'


def load_development_split(path, split):
    if split not in ('train', 'validation'):
        raise ValueError('Day 7 only permits train and validation splits.')
    with closing(connect_readonly(path)) as connection:
        source = connection.execute('SELECT * FROM dataset_splits WHERE split_name=?',
                                    (split,)).fetchone()
        pairs = connection.execute('''SELECT pair_id, left_id, right_id, label
            FROM labeled_pairs WHERE split_name=? ORDER BY pair_id''', (split,)).fetchall()
        listings = connection.execute('''SELECT listing_id, title FROM listings
            WHERE listing_id IN (
                SELECT left_id FROM labeled_pairs WHERE split_name=?
                UNION SELECT right_id FROM labeled_pairs WHERE split_name=?
            ) ORDER BY listing_id''', (split, split)).fetchall()
    if not pairs or source is None:
        raise ValueError(f'Missing {split} data; run python -m scripts.import_data.')
    return {'titles': {r['listing_id']: r['title'] for r in listings},
            'pairs': [dict(r) for r in pairs], 'source': dict(source)}


class TitleBaseline:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(lowercase=False, token_pattern=TOKEN_PATTERN,
                                         norm='l2', smooth_idf=True)

    def fit(self, training_titles):
        """Supply a mapping of unique training listing IDs to original titles."""
        if not training_titles:
            raise ValueError('Training titles are empty.')
        self.vectorizer.fit([normalize_title(title) or '' for title in training_titles.values()])
        return self

    def score(self, split):
        ids = list(split['titles'])
        positions = {identifier: index for index, identifier in enumerate(ids)}
        vectors = self.vectorizer.transform(
            [normalize_title(split['titles'][identifier]) or '' for identifier in ids])
        left = [positions[pair['left_id']] for pair in split['pairs']]
        right = [positions[pair['right_id']] for pair in split['pairs']]
        # L2-normalized sparse vectors: row-wise dot product equals cosine.
        # This avoids constructing an all-listings-by-all-listings matrix.
        scores = np.asarray(vectors[left].multiply(vectors[right]).sum(axis=1)).ravel()
        scores = np.clip(scores, 0.0, 1.0)
        zero_ids = {identifier for identifier, count in zip(ids, vectors.getnnz(axis=1)) if count == 0}
        diagnostics = {'unique_listings': len(ids), 'zero_vector_listings': len(zero_ids),
                       'pairs_with_zero_vector': sum(p['left_id'] in zero_ids or p['right_id'] in zero_ids
                                                     for p in split['pairs'])}
        return scores, diagnostics


def validate_scores(labels, scores):
    labels, scores = np.asarray(labels), np.asarray(scores, dtype=float)
    if labels.ndim != 1 or scores.ndim != 1 or len(labels) != len(scores) or not len(labels):
        raise ValueError('Labels and scores must be nonempty, equally sized vectors.')
    if not np.isin(labels, (0, 1)).all():
        raise ValueError('Labels must be binary.')
    if not np.isfinite(scores).all() or ((scores < 0) | (scores > 1)).any():
        raise ValueError('Cosine scores must be finite and between zero and one.')
    return labels, scores


def binary_metrics(labels, scores, threshold):
    labels, scores = validate_scores(labels, scores)
    if not math.isfinite(threshold):
        raise ValueError('Threshold must be finite.')
    predicted = scores >= threshold
    positives = labels == 1
    tp = int(np.sum(predicted & positives))
    fp = int(np.sum(predicted & ~positives))
    fn = int(np.sum(~predicted & positives))
    tn = int(np.sum(~predicted & ~positives))
    return {'pairs': len(labels), 'true_matches': int(positives.sum()),
            'predicted_matches': tp + fp, 'true_positives': tp, 'false_positives': fp,
            'false_negatives': fn, 'true_negatives': tn,
            'precision': tp / (tp + fp) if tp + fp else 0.0,
            'recall': tp / (tp + fn) if tp + fn else 0.0,
            'f1': 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0,
            'accuracy': (tp + tn) / len(labels),
            'review_rate': 0.0, 'automatic_decision_coverage': 1.0}


def select_threshold(labels, scores):
    """Maximize validation match-class F1; tie-break by precision then threshold.

    Include every observed score (using >=), plus a reject-all candidate.
    This is a baseline objective, not a claim that false merges are acceptable.
    """
    labels, scores = validate_scores(labels, scores)
    if set(labels.tolist()) != {0, 1}:
        raise ValueError('Threshold selection requires both validation classes.')
    candidates = [*np.unique(scores), math.nextafter(1.0, math.inf)]
    best = None
    for threshold in candidates:
        metrics = binary_metrics(labels, scores, float(threshold))
        key = (metrics['f1'], metrics['precision'], float(threshold))
        if best is None or key > best[0]:
            best = (key, float(threshold), metrics)
    return best[1], best[2]
