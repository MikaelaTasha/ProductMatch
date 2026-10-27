"""Fit on training pairs; compare on validation only. No test evaluation."""
import argparse
import json
from pathlib import Path
import platform
import sqlite3

import numpy as np
import scipy
import sklearn
from sklearn.exceptions import ConvergenceWarning

from productmatch.attributes import EXTRACTION_VERSION
from productmatch.baseline import BASELINE_VERSION, binary_metrics, load_development_split, select_threshold
from productmatch.classifier import CLASSIFIER_VERSION, MODEL_FEATURE_NAMES, PARAMETERS, PairClassifier
from productmatch.features import FEATURE_VERSION
from productmatch.normalization import NORMALIZATION_VERSION
from scripts.import_data import DEFAULT_DB
from scripts.wdc_data import ROOT


def run_classifier(path):
    train = load_development_split(path, 'train')
    validation = load_development_split(path, 'validation')
    overlap = set(train['titles']) & set(validation['titles'])
    if overlap:
        raise ValueError(f'Train/validation share {len(overlap)} listing IDs; refusing to fit.')
    if train['source']['archive_sha256'] != validation['source']['archive_sha256']:
        raise ValueError('Train and validation have different source archives.')
    model = PairClassifier().fit(train)
    scores, cosine, diagnostics = model.score(validation)
    labels = [p['label'] for p in validation['pairs']]
    threshold, metrics = select_threshold(labels, scores)
    baseline_threshold, baseline_metrics = select_threshold(labels, cosine)
    return {
        'classifier_version': CLASSIFIER_VERSION, 'feature_version': FEATURE_VERSION,
        'extraction_version': EXTRACTION_VERSION, 'normalization_version': NORMALIZATION_VERSION,
        'fit_scope': 'TF-IDF on unique training titles; logistic regression on training pairs and labels',
        'evaluation_scope': 'validation used to select thresholds; not held-out performance',
        'selection_rule': 'maximize match-class F1; ties: higher precision then higher threshold',
        'decision_rule': 'Match if score >= threshold, otherwise Different; no Review policy yet',
        'parameters': PARAMETERS,
        'training': {'pairs': len(train['pairs']), 'matches': sum(p['label'] for p in train['pairs']),
                     'unique_listings': len(train['titles']),
                     'vocabulary_size': len(model.title_model.vectorizer.vocabulary_)},
        'feature_names': list(MODEL_FEATURE_NAMES),
        'coefficients': dict(zip(MODEL_FEATURE_NAMES, model.estimator.coef_[0].tolist())),
        'intercept': float(model.estimator.intercept_[0]),
        'iterations': int(model.estimator.n_iter_[0]),
        'threshold': threshold, 'validation_metrics': metrics,
        'validation_metrics_at_0_5': binary_metrics(labels, scores, .5),
        'baseline': {'version': BASELINE_VERSION, 'threshold': baseline_threshold,
                     'validation_metrics': baseline_metrics},
        'validation_diagnostics': diagnostics, 'train_validation_offer_overlap': len(overlap),
        'sources': {'train': train['source'], 'validation': validation['source']},
        'runtime': {'python': platform.python_version(), 'scikit_learn': sklearn.__version__,
                    'numpy': np.__version__, 'scipy': scipy.__version__},
        'test_sets_read': False,
        'limitations': 'Scores are not calibrated confidence. No attribute-only ablation or Review policy. No trained model saved.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=DEFAULT_DB)
    parser.add_argument('--output', type=Path, default=ROOT/'artifacts/day10-classifier.json')
    args = parser.parse_args()
    try:
        report = run_classifier(args.db)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    except (OSError, sqlite3.Error, ValueError, ConvergenceWarning) as error:
        parser.exit(1, f'Classifier failed: {error}\n')
    for name, metrics in [('Baseline', report['baseline']['validation_metrics']),
                          ('Classifier', report['validation_metrics'])]:
        print(f"{name}: precision {metrics['precision']:.2%}, recall {metrics['recall']:.2%}, "
              f"F1 {metrics['f1']:.2%}; false matches {metrics['false_positives']}")
    print('Validation-selected thresholds; test sets untouched. No model saved.')
    print(f'Report: {args.output}')


if __name__ == '__main__':
    main()
