"""Validation-selected abstention policy; targets are empirical, not guarantees."""
import math

import numpy as np

from productmatch.baseline import validate_scores

POLICY_VERSION = 'two-threshold-review-v1'
MAX_THRESHOLD = math.nextafter(1.0, math.inf)


def decisions(scores, lower, upper):
    scores = np.asarray(scores, dtype=float)
    if scores.ndim != 1 or not np.isfinite(scores).all() or ((scores < 0) | (scores > 1)).any():
        raise ValueError('Scores must be a finite vector between zero and one.')
    if not (math.isfinite(lower) and math.isfinite(upper) and 0 <= lower <= upper <= MAX_THRESHOLD):
        raise ValueError('Thresholds must satisfy 0 <= lower <= upper <= nextafter(1).')
    return np.where(scores >= upper, 'Match', np.where(scores < lower, 'Different', 'Review'))


def review_metrics(labels, scores, lower, upper):
    labels, scores = validate_scores(labels, scores)
    result = decisions(scores, lower, upper)
    match, different, review = (result == name for name in ('Match', 'Different', 'Review'))
    positive = labels == 1
    tp, fp = int(np.sum(match & positive)), int(np.sum(match & ~positive))
    tn, fn = int(np.sum(different & ~positive)), int(np.sum(different & positive))
    return {'pairs': len(labels), 'automatic_matches': tp+fp, 'automatic_different': tn+fn,
            'correct_matches': tp, 'false_matches': fp, 'correct_different': tn,
            'false_different': fn, 'review_matches': int(np.sum(review & positive)),
            'review_nonmatches': int(np.sum(review & ~positive)),
            'match_precision': tp/(tp+fp) if tp+fp else None,
            'different_precision': tn/(tn+fn) if tn+fn else None,
            'automatic_match_recall': tp/int(positive.sum()) if positive.any() else None,
            'review_rate': float(review.mean()),
            'automatic_decision_coverage': float((~review).mean())}


def select_review_policy(labels, scores, target_precision=.95, min_support=20):
    labels, scores = validate_scores(labels, scores)
    if set(labels.tolist()) != {0, 1}:
        raise ValueError('Selection requires both validation classes.')
    if not math.isfinite(target_precision) or not 0 < target_precision <= 1:
        raise ValueError('Target precision must be in (0, 1].')
    if isinstance(min_support, bool) or not isinstance(min_support, int) or min_support < 1:
        raise ValueError('Minimum support must be a positive integer.')
    # Every distinct score boundary, preserving ties. Extra endpoint permits no Matches.
    boundaries = np.unique(np.r_[0., scores, MAX_THRESHOLD])
    order = np.argsort(scores)
    sorted_scores, sorted_labels = scores[order], labels[order]
    counts = np.searchsorted(sorted_scores, boundaries, side='left')
    positives = np.r_[0, np.cumsum(sorted_labels)][counts]
    negatives = counts - positives
    suffix_counts = len(labels) - counts
    suffix_positive = labels.sum() - positives
    prefix_ok = (counts == 0) | ((counts >= min_support) &
                                (negatives >= target_precision * counts))
    suffix_ok = (suffix_counts == 0) | ((suffix_counts >= min_support) &
                                      (suffix_positive >= target_precision * suffix_counts))
    best = None
    for upper_index in np.flatnonzero(suffix_ok):
        # Largest permissible prefix maximizes coverage for this upper boundary.
        lower_index = np.flatnonzero(prefix_ok[:upper_index+1])[-1]
        lower_index = np.flatnonzero(prefix_ok & (counts == counts[lower_index]))[0]
        accepted = int(counts[lower_index] + suffix_counts[upper_index])
        errors = int(positives[lower_index] + suffix_counts[upper_index] - suffix_positive[upper_index])
        key = (accepted, -errors, int(suffix_positive[upper_index]),
               float(boundaries[upper_index]), -float(boundaries[lower_index]))
        if best is None or key > best[0]:
            best = (key, float(boundaries[lower_index]), float(boundaries[upper_index]))
    lower, upper = best[1:]
    metrics = review_metrics(labels, scores, lower, upper)
    return {'policy_version': POLICY_VERSION, 'target_precision': target_precision,
            'min_support_per_automatic_class': min_support, 'lower_threshold': lower,
            'upper_threshold': upper, 'validation_metrics': metrics,
            'match_enabled': metrics['automatic_matches'] > 0,
            'different_enabled': metrics['automatic_different'] > 0}
